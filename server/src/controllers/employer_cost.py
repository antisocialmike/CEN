"""Costo patronal de un recibo.

Separado de las retenciones al trabajador (payroll_controller): aqui se calcula
lo que la empresa paga encima de la nomina. Cada cuota es una estrategia
aparte, para poder sustituirla o corregirla sin tocar las demas, y ninguna
tasa vive en el codigo: todas llegan en EmployerCostParameters, leidas de la
base con su vigencia.

Lo que falta en los parametros no se inventa. El componente queda fuera del
total y su nombre en `missing`, para que el tablero avise que el costo esta
incompleto.

Simplificaciones que conviene saber:
- El SBC se integra solo con el salario fijo, el aguinaldo y la prima
  vacacional minimos de ley. Las percepciones variables (horas extra, bonos)
  todavia no se integran.
- El limite inferior del SBC es el salario minimo general; no se distingue la
  Zona Libre de la Frontera Norte.
- La antiguedad sale de la fecha de alta de la cuenta.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

CENT = Decimal("0.01")
SIX_PLACES = Decimal("0.000001")

IMSS = "imss"
SAR = "sar"
INFONAVIT = "infonavit"
ISN = "isn"

# Dias que dividen al salario del periodo para obtener el diario (LSS art. 29 fr. II).
DAILY_DIVISOR = {"mensual": 30, "quincenal": 15, "semanal": 7}


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def completed_years(since, on) -> int:
    """Anios completos de servicio entre la fecha de alta y `on`."""
    if since is None:
        return 0
    start = since.date() if hasattr(since, "date") else since
    years = on.year - start.year - ((on.month, on.day) < (start.month, start.day))
    return max(0, years)


def vacation_days(years_completed: int) -> int:
    """Dias de vacaciones del anio de servicio en curso (LFT art. 76, DOF 27-12-2022).

    12 el primer anio, dos mas por anio hasta 20 en el quinto, y a partir del
    sexto dos mas por cada cinco anios.
    """
    service_year = max(0, years_completed) + 1
    if service_year <= 5:
        return 12 + 2 * (service_year - 1)
    return 20 + 2 * -(-(service_year - 5) // 5)


class MissingParameter(Exception):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = name


@dataclass
class EmployerCostParameters:
    rates: dict = field(default_factory=dict)
    ceav_brackets: list = field(default_factory=list)
    isn_rate: Optional[Decimal] = None
    risk_rate: Optional[Decimal] = None

    def get(self, key: str) -> Decimal:
        value = self.rates.get(key)
        if value is None:
            raise MissingParameter(key)
        return Decimal(value)


@dataclass
class EmployerCostInputs:
    period_salary: Decimal
    periodicity: str
    days: Decimal
    years_completed: int
    total_perceptions: Decimal


@dataclass
class CostContext:
    params: EmployerCostParameters
    inputs: EmployerCostInputs
    sbc: Optional[Decimal]
    uma: Optional[Decimal]

    def require_sbc(self) -> Decimal:
        if self.sbc is None:
            raise MissingParameter("sbc")
        return self.sbc

    def require_uma(self) -> Decimal:
        if self.uma is None:
            raise MissingParameter("uma_diaria")
        return self.uma


@dataclass(frozen=True)
class ComponentAmount:
    base: Decimal
    rate: Decimal

    @property
    def amount(self) -> Decimal:
        return money(self.base * self.rate)


class EmployerCostComponent(ABC):
    key = ""
    description = ""
    group = IMSS

    @abstractmethod
    def compute(self, ctx: CostContext) -> ComponentAmount:
        pass


class PercentOfSbc(EmployerCostComponent):
    """Una tasa fija sobre el SBC por los dias cotizados."""

    def __init__(self, key: str, description: str, group: str, param: str):
        self.key = key
        self.description = description
        self.group = group
        self.param = param

    def compute(self, ctx: CostContext) -> ComponentAmount:
        return ComponentAmount(
            ctx.require_sbc() * ctx.inputs.days, ctx.params.get(self.param)
        )


class SicknessFixedQuota(EmployerCostComponent):
    key = "em_cuota_fija"
    description = "Enfermedad y maternidad, cuota fija"

    def compute(self, ctx: CostContext) -> ComponentAmount:
        return ComponentAmount(
            ctx.require_uma() * ctx.inputs.days,
            ctx.params.get("imss_em_cuota_fija"),
        )


class SicknessExcess(EmployerCostComponent):
    key = "em_excedente"
    description = "Enfermedad y maternidad, excedente de 3 UMA"

    def compute(self, ctx: CostContext) -> ComponentAmount:
        threshold = ctx.require_uma() * ctx.params.get(
            "imss_em_excedente_umbral_uma"
        )
        excess = max(Decimal(0), ctx.require_sbc() - threshold)
        return ComponentAmount(
            excess * ctx.inputs.days, ctx.params.get("imss_em_excedente")
        )


class WorkRisk(EmployerCostComponent):
    key = "riesgo_trabajo"
    description = "Riesgos de trabajo"

    def compute(self, ctx: CostContext) -> ComponentAmount:
        if ctx.params.risk_rate is None:
            raise MissingParameter("prima_riesgo_trabajo")
        return ComponentAmount(
            ctx.require_sbc() * ctx.inputs.days, Decimal(ctx.params.risk_rate)
        )


class RetirementUnemploymentOldAge(EmployerCostComponent):
    """Cesantia en edad avanzada y vejez, escalonada por SBC en UMA (LSS art. 168)."""

    key = "ceav"
    description = "Cesantía en edad avanzada y vejez"
    group = SAR

    def compute(self, ctx: CostContext) -> ComponentAmount:
        sbc = ctx.require_sbc()
        return ComponentAmount(sbc * ctx.inputs.days, self.rate_for(ctx, sbc))

    def rate_for(self, ctx: CostContext, sbc: Decimal) -> Decimal:
        brackets = ctx.params.ceav_brackets
        if not brackets:
            raise MissingParameter("ceav")

        minimum_wage = ctx.params.get("salario_minimo_general")
        if sbc <= minimum_wage:
            for bracket in brackets:
                if bracket["minimum_wage"]:
                    return Decimal(bracket["rate"])

        # La tabla usa dos decimales: 1.505 UMA cae en "1.51 a 2.00".
        times_uma = (sbc / ctx.require_uma()).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
        ranges = sorted(
            (b for b in brackets if not b["minimum_wage"]),
            key=lambda b: (b["upper_uma"] is None, b["upper_uma"] or 0),
        )
        for bracket in ranges:
            upper = bracket["upper_uma"]
            if upper is None or times_uma <= Decimal(upper):
                return Decimal(bracket["rate"])
        raise MissingParameter("ceav")


class StatePayrollTax(EmployerCostComponent):
    """Impuesto sobre nominas del estado, sobre el total de percepciones."""

    key = "isn"
    description = "Impuesto sobre nóminas"
    group = ISN

    def compute(self, ctx: CostContext) -> ComponentAmount:
        if ctx.params.isn_rate is None:
            raise MissingParameter("isn")
        return ComponentAmount(
            Decimal(ctx.inputs.total_perceptions), Decimal(ctx.params.isn_rate)
        )


def default_components() -> List[EmployerCostComponent]:
    return [
        SicknessFixedQuota(),
        SicknessExcess(),
        PercentOfSbc(
            "em_prestaciones_dinero",
            "Enfermedad y maternidad, prestaciones en dinero",
            IMSS, "imss_em_prestaciones_dinero",
        ),
        PercentOfSbc(
            "gastos_medicos_pensionados", "Gastos médicos de pensionados",
            IMSS, "imss_gastos_medicos_pensionados",
        ),
        PercentOfSbc(
            "invalidez_vida", "Invalidez y vida", IMSS, "imss_invalidez_vida",
        ),
        WorkRisk(),
        PercentOfSbc(
            "guarderias", "Guarderías y prestaciones sociales",
            IMSS, "imss_guarderias",
        ),
        PercentOfSbc("retiro", "Retiro", SAR, "imss_retiro"),
        RetirementUnemploymentOldAge(),
        PercentOfSbc("infonavit", "INFONAVIT", INFONAVIT, "infonavit"),
        StatePayrollTax(),
    ]


class EmployerCostService:
    def __init__(self, components: Optional[List[EmployerCostComponent]] = None):
        self.components = components or default_components()

    def integration_factor(
        self, params: EmployerCostParameters, years_completed: int
    ) -> Decimal:
        """(365 + aguinaldo + vacaciones x prima vacacional) / 365."""
        aguinaldo = params.get("lft_aguinaldo_dias")
        prima = params.get("lft_prima_vacacional")
        days = Decimal(vacation_days(years_completed))
        factor = (365 + aguinaldo + days * prima) / 365
        return factor.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)

    def sbc(
        self, params: EmployerCostParameters, daily_salary: Decimal,
        factor: Decimal,
    ) -> Decimal:
        """Salario diario integrado, entre el salario minimo y 25 UMA (LSS art. 28)."""
        uma = params.get("uma_diaria")
        floor = params.get("salario_minimo_general")
        ceiling = uma * params.get("imss_tope_uma")
        return money(min(max(daily_salary * factor, floor), ceiling))

    def calculate(
        self, inputs: EmployerCostInputs, params: EmployerCostParameters
    ) -> dict:
        daily_salary = money(
            Decimal(inputs.period_salary) / DAILY_DIVISOR[inputs.periodicity]
        )
        missing: List[str] = []

        factor = Decimal(1)
        try:
            factor = self.integration_factor(params, inputs.years_completed)
        except MissingParameter as error:
            missing.append(error.name)

        sbc = None
        try:
            if not missing:
                sbc = self.sbc(params, daily_salary, factor)
        except MissingParameter as error:
            missing.append(error.name)

        ctx = CostContext(
            params=params, inputs=inputs, sbc=sbc,
            uma=params.rates.get("uma_diaria"),
        )

        items = []
        for position, component in enumerate(self.components):
            try:
                result = component.compute(ctx)
            except MissingParameter as error:
                if error.name not in missing:
                    missing.append(error.name)
                continue
            items.append({
                "component": component.key,
                "group_key": component.group,
                "description": component.description,
                "base": money(result.base),
                "rate": result.rate,
                "amount": result.amount,
                "position": position,
            })

        return {
            "daily_salary": daily_salary,
            "integration_factor": factor,
            "sbc_daily": sbc,
            "uma_daily": ctx.uma,
            "days": Decimal(inputs.days),
            "items": items,
            "total": money(sum((item["amount"] for item in items), Decimal(0))),
            "missing": missing,
        }

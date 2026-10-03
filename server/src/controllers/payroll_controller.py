"""Retenciones al trabajador: ISR e IMSS de un periodo.

Lo que cambia con el anio no vive aqui: la UMA, el salario minimo, el subsidio
para el empleo y la tarifa del ISR llegan en PayrollParameters, leidos de la
base con su vigencia (migraciones 012 y 013). Las tasas de la cuota obrera del
IMSS si estan aqui: las fija la LSS y no se actualizan cada anio.

La cuota obrera se calcula sobre el SBC que tambien usa el costo patronal
(employer_cost.EmployerCostService.contribution_base): trabajador y empresa
cotizan sobre la misma base.

Dos tipos de nomina (claves del catalogo c_TipoRegimen del SAT):
- 02 Sueldos: la de siempre.
- 09 Asimilados honorarios: misma tarifa de ISR, pero sin subsidio para el
  empleo (el decreto es solo para el art. 94 primer parrafo y fr. I), sin
  IMSS y sin las exenciones del art. 93, que son para trabajadores. Sin
  relacion laboral tampoco hay horas extra, aguinaldo, prima vacacional ni
  credito Infonavit.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Tuple

CENT = Decimal("0.01")
CERO = Decimal("0.00")

DIAS_TARIFA_MENSUAL = Decimal("30.4")

SUELDOS = "02"
ASIMILADOS = "09"
TIPOS_DE_REGIMEN = (SUELDOS, ASIMILADOS)

# Jornada maxima por dia, la que divide el salario diario en horas (LFT art. 61).
HORAS_POR_JORNADA = {
    "01": Decimal("8"), "02": Decimal("7"), "03": Decimal("7.5"),
}
DIURNA = "01"

# Lo que un asimilado no puede tener: son prestaciones de la relacion laboral.
CONCEPTOS_SOLO_DE_TRABAJADORES = (
    "overtime_double_hours",
    "overtime_triple_hours",
    "christmas_bonus_days",
    "vacation_days",
    "housing_credit_deduction",
)

MENSUAL = "mensual"
QUINCENAL = "quincenal"
SEMANAL = "semanal"

PERIODICITIES = {
    MENSUAL: {
        "tarifa_dias": Decimal("30.4"), "dias_nominales": 30,
        "semanas": 4, "etiqueta": "Mensual",
    },
    QUINCENAL: {
        "tarifa_dias": Decimal("15.2"), "dias_nominales": 15,
        "semanas": 2, "etiqueta": "Quincenal",
    },
    SEMANAL: {
        "tarifa_dias": Decimal("7"), "dias_nominales": 7,
        "semanas": 1, "etiqueta": "Semanal",
    },
}

# Cuota obrera del IMSS sobre el SBC (LSS arts. 25, 106, 107, 147 y 168).
IMSS_ENFERMEDAD_MATERNIDAD_DINERO = Decimal("0.0025")
IMSS_GASTOS_MEDICOS_PENSIONADOS = Decimal("0.00375")
IMSS_INVALIDEZ_VIDA = Decimal("0.00625")
IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ = Decimal("0.01125")
IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE = Decimal("0.0040")
IMSS_EXCEDENTE_UMBRAL_UMA = 3

AGUINALDO_EXENTO_UMA = 30
PRIMA_VACACIONAL_EXENTO_UMA = 15
PRIMA_VACACIONAL_PORCENTAJE = Decimal("0.25")
HORAS_EXTRA_EXENTO_UMA_POR_SEMANA = 5
HORAS_EXTRA_PORCENTAJE_EXENTO = Decimal("0.5")

FACTOR_HORA_DOBLE = 2
FACTOR_HORA_TRIPLE = 3

PERCEPTION = "perception"
DEDUCTION = "deduction"


def _decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _round(amount) -> Decimal:
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP) + 0


def _quantity(value: Decimal) -> str:
    return "{:f}".format(value.normalize())


class MissingPayrollParameter(Exception):
    """Falta un parametro vigente para el periodo: sin el no hay retencion."""

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name


@dataclass(frozen=True)
class PayrollParameters:
    uma_diaria: Decimal
    salario_minimo_general: Decimal
    subsidio_porcentaje_uma: Decimal
    subsidio_limite_mensual: Decimal
    # Tarifa mensual del art. 96: (limite inferior, limite superior o None,
    # cuota fija, porcentaje sobre el excedente), del tramo mas bajo al mas alto.
    isr_table: Tuple[tuple, ...]

    @classmethod
    def from_rows(cls, rates: dict, isr_rows: list) -> "PayrollParameters":
        """Con lo que devuelve el repositorio para la fecha del periodo."""

        def required(key: str) -> Decimal:
            value = rates.get(key)
            if value is None:
                raise MissingPayrollParameter(key)
            return _decimal(value)

        if not isr_rows:
            raise MissingPayrollParameter("tarifa_isr")

        return cls(
            uma_diaria=required("uma_diaria"),
            salario_minimo_general=required("salario_minimo_general"),
            subsidio_porcentaje_uma=required("subsidio_empleo_porcentaje_uma"),
            subsidio_limite_mensual=required("subsidio_empleo_limite_mensual"),
            isr_table=tuple(
                (
                    _decimal(row["lower_limit"]),
                    None if row["upper_limit"] is None
                    else _decimal(row["upper_limit"]),
                    _decimal(row["fixed_fee"]),
                    _decimal(row["rate"]),
                )
                for row in isr_rows
            ),
        )

    @property
    def uma_mensual(self) -> Decimal:
        return _round(self.uma_diaria * DIAS_TARIFA_MENSUAL)

    @property
    def subsidio_mensual(self) -> Decimal:
        """El porcentaje del decreto sobre la UMA mensual del periodo.

        En 2026: 15.02% de 3,566.22 = 535.65 de febrero a diciembre, y 15.59%
        de la UMA 2025 (3,439.46) = 536.21 en enero.
        """
        return _round(self.uma_mensual * self.subsidio_porcentaje_uma)


@dataclass(frozen=True)
class PayrollItem:
    kind: str
    concept: str
    description: str
    amount: Decimal
    taxable: Decimal = CERO
    exempt: Decimal = CERO

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "concept": self.concept,
            "description": self.description,
            "amount": self.amount,
            "taxable": self.taxable,
            "exempt": self.exempt,
        }


def _split_exemption(amount: Decimal, exempt_cap: Decimal) -> tuple:
    exempt = min(amount, max(CERO, exempt_cap))
    return _round(amount - exempt), _round(exempt)


class TaxCalculationStrategy(ABC):
    @abstractmethod
    def calculate(self, base_salary: Decimal) -> Decimal:
        pass


def scale_isr_table(table: Tuple[tuple, ...], factor: Decimal) -> list:
    return [
        (
            limite_inferior * factor,
            None if limite_superior is None else limite_superior * factor,
            cuota_fija * factor,
            porcentaje,
        )
        for limite_inferior, limite_superior, cuota_fija, porcentaje in table
    ]


class ISRStrategy(TaxCalculationStrategy):
    def __init__(
        self, parameters: PayrollParameters, periodicity: str = MENSUAL,
        with_subsidy: bool = True,
    ):
        self.factor = (
            PERIODICITIES[periodicity]["tarifa_dias"] / DIAS_TARIFA_MENSUAL
        )
        self.table = scale_isr_table(parameters.isr_table, self.factor)
        self.subsidio_limite = parameters.subsidio_limite_mensual * self.factor
        self.subsidio = (
            parameters.subsidio_mensual * self.factor if with_subsidy else CERO
        )

    def calculate(self, base_salary) -> Decimal:
        base_salary = _decimal(base_salary)
        isr_causado = CERO
        for limite_inferior, limite_superior, cuota_fija, porcentaje in self.table:
            dentro_del_rango = base_salary >= limite_inferior and (
                limite_superior is None or base_salary <= limite_superior
            )
            if dentro_del_rango:
                isr_causado = cuota_fija + (base_salary - limite_inferior) * porcentaje
                break

        # El subsidio solo se resta del ISR: si es mayor, no se entrega la
        # diferencia (decreto DOF 01-05-2024, art. segundo).
        if base_salary <= self.subsidio_limite:
            isr_causado = max(CERO, isr_causado - self.subsidio)

        return _round(isr_causado)


class IMSSStrategy:
    """Cuota obrera del IMSS: el SBC diario por los dias cotizados del periodo."""

    def __init__(self, parameters: PayrollParameters):
        self.umbral_excedente = parameters.uma_diaria * IMSS_EXCEDENTE_UMBRAL_UMA

    def calculate(self, sbc_daily, days) -> Decimal:
        sbc_daily = _decimal(sbc_daily)
        days = _decimal(days)
        cuotas_sobre_sbc = (
            IMSS_ENFERMEDAD_MATERNIDAD_DINERO
            + IMSS_GASTOS_MEDICOS_PENSIONADOS
            + IMSS_INVALIDEZ_VIDA
            + IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ
        )
        excedente = max(CERO, sbc_daily - self.umbral_excedente)

        imss = (
            sbc_daily * days * cuotas_sobre_sbc
            + excedente * days * IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE
        )

        return _round(imss)


class PayrollService:
    def process(
        self, inputs: dict, parameters: PayrollParameters, sbc_daily
    ) -> dict:
        """El desglose del periodo.

        `parameters` son los vigentes en el periodo y `sbc_daily` el salario
        base de cotizacion que usa tambien el costo patronal.
        """
        gross_salary = _decimal(inputs.get("gross_salary"))
        periodicity = inputs.get("periodicity") or MENSUAL
        if periodicity not in PERIODICITIES:
            raise ValueError("Periodicidad no reconocida")

        given_days = inputs.get("paid_days")
        paid_days = _decimal(
            given_days
            if given_days is not None
            else PERIODICITIES[periodicity]["dias_nominales"]
        )
        if paid_days <= 0:
            raise ValueError("Los días pagados deben ser mayores que cero")

        regimen = inputs.get("tipo_regimen") or SUELDOS
        if regimen not in TIPOS_DE_REGIMEN:
            raise ValueError("Tipo de régimen no reconocido")
        jornada = inputs.get("tipo_jornada") or DIURNA
        if jornada not in HORAS_POR_JORNADA:
            raise ValueError("Tipo de jornada no reconocido")
        assimilated = regimen == ASIMILADOS

        self._reject_negatives(inputs)
        if assimilated:
            self._reject_labor_concepts(inputs)

        perceptions = self._perceptions(
            gross_salary, inputs, paid_days, periodicity,
            parameters.uma_diaria, HORAS_POR_JORNADA[jornada], assimilated,
        )
        taxable_base = sum(item.taxable for item in perceptions)

        # El salario minimo (LISR 96 y LSS 36) es cosa de trabajadores.
        minimum_wage = not assimilated and self._earns_minimum_wage(
            gross_salary, periodicity, parameters
        )
        imss_quota = (
            CERO if assimilated
            else IMSSStrategy(parameters).calculate(sbc_daily, paid_days)
        )

        deductions = self._deductions(
            ISRStrategy(parameters, periodicity, with_subsidy=not assimilated),
            taxable_base,
            imss_quota,
            minimum_wage,
            only_salary=len(perceptions) == 1,
            inputs=inputs,
            assimilated=assimilated,
        )

        total_perceptions = _round(sum(item.amount for item in perceptions))
        total_deductions = _round(sum(item.amount for item in deductions))

        isr = next(item.amount for item in deductions if item.concept == "isr")
        # Un asimilado no lleva renglon de IMSS: no cotiza.
        imss = next(
            (item.amount for item in deductions if item.concept == "imss"), CERO
        )

        return {
            "periodicity": periodicity,
            "tipo_regimen": regimen,
            "paid_days": paid_days,
            "gross_salary": gross_salary,
            "isr_deduction": isr,
            "imss_deduction": imss,
            # La cuota obrera que paga la empresa: va a su costo, no al recibo.
            "imss_employer_paid": imss_quota if minimum_wage else CERO,
            "total_perceptions": total_perceptions,
            "total_deductions": total_deductions,
            "taxable_base": _round(taxable_base),
            "net_salary": _round(total_perceptions - total_deductions),
            "items": [item.as_dict() for item in perceptions + deductions],
        }

    def _earns_minimum_wage(
        self, gross_salary: Decimal, periodicity: str,
        parameters: PayrollParameters,
    ) -> bool:
        # El mismo salario diario que usa el costo patronal: 30, 15 o 7 dias.
        daily = _round(gross_salary / PERIODICITIES[periodicity]["dias_nominales"])
        return daily <= parameters.salario_minimo_general

    def _reject_labor_concepts(self, inputs: dict) -> None:
        if any(
            _decimal(inputs.get(field)) > 0
            for field in CONCEPTOS_SOLO_DE_TRABAJADORES
        ):
            raise ValueError(
                "Un asimilado a salarios no tiene horas extra, aguinaldo, prima "
                "vacacional ni crédito Infonavit: no hay relación laboral"
            )

    def _reject_negatives(self, inputs: dict) -> None:
        if _decimal(inputs.get("gross_salary")) < 0:
            raise ValueError("El salario no puede ser negativo")

        for field in (
            "overtime_double_hours",
            "overtime_triple_hours",
            "christmas_bonus_days",
            "vacation_days",
            "bonus",
            "loan_deduction",
            "housing_credit_deduction",
        ):
            if _decimal(inputs.get(field)) < 0:
                raise ValueError("Los conceptos de nómina no pueden ser negativos")

    def _hourly_wage(
        self, gross_salary: Decimal, paid_days: Decimal, hours_per_day: Decimal
    ) -> Decimal:
        return self._daily_wage(gross_salary, paid_days) / hours_per_day

    def _daily_wage(self, gross_salary: Decimal, paid_days: Decimal) -> Decimal:
        return gross_salary / paid_days

    def _perceptions(
        self,
        gross_salary: Decimal,
        inputs: dict,
        paid_days: Decimal,
        periodicity: str,
        uma_diaria: Decimal,
        hours_per_day: Decimal,
        assimilated: bool,
    ) -> List[PayrollItem]:
        items = [
            PayrollItem(
                kind=PERCEPTION,
                concept="sueldo",
                description=(
                    "Honorarios asimilados a salarios del periodo"
                    if assimilated else "Sueldo del periodo"
                ),
                amount=_round(gross_salary),
                taxable=_round(gross_salary),
            )
        ]

        overtime = self._overtime(
            gross_salary, inputs, paid_days, periodicity, uma_diaria,
            hours_per_day,
        )
        if overtime is not None:
            items.append(overtime)

        christmas_bonus = self._christmas_bonus(
            gross_salary, inputs, paid_days, uma_diaria
        )
        if christmas_bonus is not None:
            items.append(christmas_bonus)

        vacation_premium = self._vacation_premium(
            gross_salary, inputs, paid_days, uma_diaria
        )
        if vacation_premium is not None:
            items.append(vacation_premium)

        bonus = _decimal(inputs.get("bonus"))
        if bonus > 0:
            items.append(
                PayrollItem(
                    kind=PERCEPTION,
                    concept="bono",
                    description="Bono o gratificación",
                    amount=_round(bonus),
                    taxable=_round(bonus),
                )
            )

        return items

    def _overtime(
        self,
        gross_salary: Decimal,
        inputs: dict,
        paid_days: Decimal,
        periodicity: str,
        uma_diaria: Decimal,
        hours_per_day: Decimal,
    ):
        double_hours = _decimal(inputs.get("overtime_double_hours"))
        triple_hours = _decimal(inputs.get("overtime_triple_hours"))
        if double_hours <= 0 and triple_hours <= 0:
            return None

        hourly = self._hourly_wage(gross_salary, paid_days, hours_per_day)
        amount = _round(
            hourly * FACTOR_HORA_DOBLE * double_hours
            + hourly * FACTOR_HORA_TRIPLE * triple_hours
        )

        cap = (
            uma_diaria
            * HORAS_EXTRA_EXENTO_UMA_POR_SEMANA
            * PERIODICITIES[periodicity]["semanas"]
        )
        taxable, exempt = _split_exemption(
            amount, min(amount * HORAS_EXTRA_PORCENTAJE_EXENTO, cap)
        )

        return PayrollItem(
            kind=PERCEPTION,
            concept="horas_extra",
            description="Horas extra ({} dobles, {} triples)".format(
                _quantity(double_hours), _quantity(triple_hours)
            ),
            amount=amount,
            taxable=taxable,
            exempt=exempt,
        )

    def _christmas_bonus(
        self, gross_salary: Decimal, inputs: dict, paid_days: Decimal,
        uma_diaria: Decimal,
    ):
        days = _decimal(inputs.get("christmas_bonus_days"))
        if days <= 0:
            return None

        amount = _round(self._daily_wage(gross_salary, paid_days) * days)
        taxable, exempt = _split_exemption(
            amount, uma_diaria * AGUINALDO_EXENTO_UMA
        )

        return PayrollItem(
            kind=PERCEPTION,
            concept="aguinaldo",
            description="Aguinaldo ({} días)".format(_quantity(days)),
            amount=amount,
            taxable=taxable,
            exempt=exempt,
        )

    def _vacation_premium(
        self, gross_salary: Decimal, inputs: dict, paid_days: Decimal,
        uma_diaria: Decimal,
    ):
        days = _decimal(inputs.get("vacation_days"))
        if days <= 0:
            return None

        amount = _round(
            self._daily_wage(gross_salary, paid_days)
            * days
            * PRIMA_VACACIONAL_PORCENTAJE
        )
        taxable, exempt = _split_exemption(
            amount, uma_diaria * PRIMA_VACACIONAL_EXENTO_UMA
        )

        return PayrollItem(
            kind=PERCEPTION,
            concept="prima_vacacional",
            description="Prima vacacional ({} días de vacaciones)".format(
                _quantity(days)
            ),
            amount=amount,
            taxable=taxable,
            exempt=exempt,
        )

    def _deductions(
        self,
        isr_calc: ISRStrategy,
        taxable_base: Decimal,
        imss_quota: Decimal,
        minimum_wage: bool,
        only_salary: bool,
        inputs: dict,
        assimilated: bool = False,
    ) -> List[PayrollItem]:
        # A quien en el periodo solo cobra el salario minimo no se le retiene
        # ISR (LISR art. 96), y su cuota del IMSS la paga el patron (LSS art. 36).
        if minimum_wage and only_salary:
            isr = PayrollItem(
                kind=DEDUCTION,
                concept="isr",
                description="ISR: no se retiene a quien gana el salario mínimo",
                amount=CERO,
            )
        else:
            isr = PayrollItem(
                kind=DEDUCTION,
                concept="isr",
                description="ISR retenido",
                amount=isr_calc.calculate(taxable_base),
            )

        if assimilated:
            imss = None
        elif minimum_wage:
            imss = PayrollItem(
                kind=DEDUCTION,
                concept="imss",
                description="IMSS: lo paga el patrón por ser salario mínimo",
                amount=CERO,
            )
        else:
            imss = PayrollItem(
                kind=DEDUCTION,
                concept="imss",
                description="IMSS retenido",
                amount=imss_quota,
            )

        items = [isr] + ([imss] if imss is not None else [])

        loan = _decimal(inputs.get("loan_deduction"))
        if loan > 0:
            items.append(
                PayrollItem(
                    kind=DEDUCTION,
                    concept="prestamo",
                    description="Préstamo a la empresa",
                    amount=_round(loan),
                )
            )

        housing = _decimal(inputs.get("housing_credit_deduction"))
        if housing > 0:
            items.append(
                PayrollItem(
                    kind=DEDUCTION,
                    concept="infonavit",
                    description="Crédito Infonavit",
                    amount=_round(housing),
                )
            )

        return items


def missing_parameter_label(name: Optional[str]) -> str:
    """Como decirle al usuario que parametro falta."""
    return MISSING_LABELS.get(name or "", name or "un parámetro")


MISSING_LABELS = {
    "uma_diaria": "la UMA",
    "salario_minimo_general": "el salario mínimo",
    "subsidio_empleo_porcentaje_uma": "el subsidio para el empleo",
    "subsidio_empleo_limite_mensual": "el subsidio para el empleo",
    "tarifa_isr": "la tarifa del ISR",
    "lft_aguinaldo_dias": "el aguinaldo mínimo de la LFT",
    "lft_prima_vacacional": "la prima vacacional mínima de la LFT",
    "imss_tope_uma": "el tope de cotización del IMSS",
}

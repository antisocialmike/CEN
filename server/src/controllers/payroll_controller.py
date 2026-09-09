from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

UMA_MENSUAL = 3566.22
UMA_DIARIA = round(UMA_MENSUAL / 30.4, 2)

HORAS_DE_JORNADA = 8
DIAS_TARIFA_MENSUAL = 30.4

MENSUAL = "mensual"
QUINCENAL = "quincenal"
SEMANAL = "semanal"

PERIODICITIES = {
    MENSUAL: {
        "tarifa_dias": 30.4, "dias_nominales": 30,
        "semanas": 4.0, "etiqueta": "Mensual",
    },
    QUINCENAL: {
        "tarifa_dias": 15.2, "dias_nominales": 15,
        "semanas": 2.0, "etiqueta": "Quincenal",
    },
    SEMANAL: {
        "tarifa_dias": 7.0, "dias_nominales": 7,
        "semanas": 1.0, "etiqueta": "Semanal",
    },
}

ISR_SUBSIDIO_LIMITE = 11492.66
ISR_SUBSIDIO_MONTO = 536.22

ISR_TABLE = [
    (0.0, 844.59, 0.0, 0.0192),
    (844.60, 7168.51, 16.22, 0.0640),
    (7168.52, 12598.02, 420.95, 0.1088),
    (12598.03, 14644.64, 1011.68, 0.1600),
    (14644.65, 17533.64, 1339.14, 0.1792),
    (17533.65, 35362.83, 1856.84, 0.2136),
    (35362.84, 55736.68, 5665.16, 0.2352),
    (55736.69, 106410.50, 10457.09, 0.3000),
    (106410.51, 141880.66, 25659.23, 0.3200),
    (141880.67, 425641.99, 37009.69, 0.3400),
    (425642.00, None, 133488.54, 0.3500),
]

IMSS_ENFERMEDAD_MATERNIDAD_DINERO = 0.0025
IMSS_GASTOS_MEDICOS_PENSIONADOS = 0.00375
IMSS_INVALIDEZ_VIDA = 0.00625
IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ = 0.01125
IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE = 0.0040
IMSS_TOPE_UMA = 25

AGUINALDO_EXENTO_UMA = 30
PRIMA_VACACIONAL_EXENTO_UMA = 15
PRIMA_VACACIONAL_PORCENTAJE = 0.25
HORAS_EXTRA_EXENTO_UMA_POR_SEMANA = 5
HORAS_EXTRA_PORCENTAJE_EXENTO = 0.5

FACTOR_HORA_DOBLE = 2
FACTOR_HORA_TRIPLE = 3

PERCEPTION = "perception"
DEDUCTION = "deduction"


@dataclass(frozen=True)
class PayrollItem:
    kind: str
    concept: str
    description: str
    amount: float
    taxable: float = 0.0
    exempt: float = 0.0

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "concept": self.concept,
            "description": self.description,
            "amount": self.amount,
            "taxable": self.taxable,
            "exempt": self.exempt,
        }


def _round(amount: float) -> float:
    return round(amount + 0.0, 2)


def _split_exemption(amount: float, exempt_cap: float) -> tuple:
    exempt = min(amount, max(0.0, exempt_cap))
    return _round(amount - exempt), _round(exempt)


class TaxCalculationStrategy(ABC):
    @abstractmethod
    def calculate(self, base_salary: float) -> float:
        pass


def scale_isr_table(factor: float) -> list:
    return [
        (
            limite_inferior * factor,
            None if limite_superior is None else limite_superior * factor,
            cuota_fija * factor,
            porcentaje,
        )
        for limite_inferior, limite_superior, cuota_fija, porcentaje in ISR_TABLE
    ]


class ISRStrategy(TaxCalculationStrategy):
    def __init__(self, periodicity: str = MENSUAL):
        self.factor = (
            PERIODICITIES[periodicity]["tarifa_dias"] / DIAS_TARIFA_MENSUAL
        )
        self.table = scale_isr_table(self.factor)

    def calculate(self, base_salary: float) -> float:
        isr_causado = 0.0
        for limite_inferior, limite_superior, cuota_fija, porcentaje in self.table:
            dentro_del_rango = base_salary >= limite_inferior and (
                limite_superior is None or base_salary <= limite_superior
            )
            if dentro_del_rango:
                isr_causado = cuota_fija + (base_salary - limite_inferior) * porcentaje
                break

        if base_salary <= ISR_SUBSIDIO_LIMITE * self.factor:
            isr_causado = max(
                0.0, isr_causado - ISR_SUBSIDIO_MONTO * self.factor
            )

        return _round(isr_causado)


class IMSSStrategy(TaxCalculationStrategy):
    def __init__(self, periodicity: str = MENSUAL):
        self.factor = (
            PERIODICITIES[periodicity]["tarifa_dias"] / DIAS_TARIFA_MENSUAL
        )

    def calculate(self, base_salary: float) -> float:
        tope = UMA_MENSUAL * IMSS_TOPE_UMA * self.factor
        salario_cotizable = min(base_salary, tope)
        tres_uma_mensual = UMA_MENSUAL * 3 * self.factor
        excedente = max(0.0, salario_cotizable - tres_uma_mensual)

        cuotas_sobre_sbc = (
            IMSS_ENFERMEDAD_MATERNIDAD_DINERO
            + IMSS_GASTOS_MEDICOS_PENSIONADOS
            + IMSS_INVALIDEZ_VIDA
            + IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ
        )

        imss = (
            salario_cotizable * cuotas_sobre_sbc
            + excedente * IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE
        )

        return _round(imss)


class PayrollService:
    def __init__(self, isr=None, imss=None):
        self.isr_override = isr
        self.imss_override = imss

    def _strategies(self, periodicity: str) -> tuple:
        isr = self.isr_override or ISRStrategy(periodicity)
        imss = self.imss_override or IMSSStrategy(periodicity)
        return isr, imss

    def process_salary(self, gross_salary: float) -> dict:
        return self.process({"gross_salary": gross_salary})

    def process(self, inputs: dict) -> dict:
        gross_salary = float(inputs.get("gross_salary", 0))
        periodicity = inputs.get("periodicity") or MENSUAL
        if periodicity not in PERIODICITIES:
            raise ValueError("Periodicidad no reconocida")

        given_days = inputs.get("paid_days")
        paid_days = float(
            given_days
            if given_days is not None
            else PERIODICITIES[periodicity]["dias_nominales"]
        )
        if paid_days <= 0:
            raise ValueError("Los dias pagados deben ser mayores que cero")

        self.isr_calc, self.imss_calc = self._strategies(periodicity)
        self._reject_negatives(inputs)

        perceptions = self._perceptions(
            gross_salary, inputs, paid_days, periodicity
        )
        taxable_base = sum(item.taxable for item in perceptions)

        deductions = self._deductions(gross_salary, taxable_base, inputs)

        total_perceptions = _round(sum(item.amount for item in perceptions))
        total_deductions = _round(sum(item.amount for item in deductions))

        isr = next(item.amount for item in deductions if item.concept == "isr")
        imss = next(item.amount for item in deductions if item.concept == "imss")

        return {
            "periodicity": periodicity,
            "paid_days": paid_days,
            "gross_salary": gross_salary,
            "isr_deduction": isr,
            "imss_deduction": imss,
            "total_perceptions": total_perceptions,
            "total_deductions": total_deductions,
            "taxable_base": _round(taxable_base),
            "net_salary": _round(total_perceptions - total_deductions),
            "items": [item.as_dict() for item in perceptions + deductions],
        }

    def _reject_negatives(self, inputs: dict) -> None:
        if float(inputs.get("gross_salary", 0)) < 0:
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
            if float(inputs.get(field) or 0) < 0:
                raise ValueError("Los conceptos de nomina no pueden ser negativos")

    def _hourly_wage(self, gross_salary: float, paid_days: float) -> float:
        return self._daily_wage(gross_salary, paid_days) / HORAS_DE_JORNADA

    def _daily_wage(self, gross_salary: float, paid_days: float) -> float:
        return gross_salary / paid_days

    def _perceptions(
        self,
        gross_salary: float,
        inputs: dict,
        paid_days: float,
        periodicity: str,
    ) -> List[PayrollItem]:
        items = [
            PayrollItem(
                kind=PERCEPTION,
                concept="sueldo",
                description="Sueldo del periodo",
                amount=_round(gross_salary),
                taxable=_round(gross_salary),
            )
        ]

        overtime = self._overtime(gross_salary, inputs, paid_days, periodicity)
        if overtime is not None:
            items.append(overtime)

        christmas_bonus = self._christmas_bonus(gross_salary, inputs, paid_days)
        if christmas_bonus is not None:
            items.append(christmas_bonus)

        vacation_premium = self._vacation_premium(
            gross_salary, inputs, paid_days
        )
        if vacation_premium is not None:
            items.append(vacation_premium)

        bonus = float(inputs.get("bonus") or 0)
        if bonus > 0:
            items.append(
                PayrollItem(
                    kind=PERCEPTION,
                    concept="bono",
                    description="Bono o gratificacion",
                    amount=_round(bonus),
                    taxable=_round(bonus),
                )
            )

        return items

    def _overtime(
        self,
        gross_salary: float,
        inputs: dict,
        paid_days: float,
        periodicity: str,
    ):
        double_hours = float(inputs.get("overtime_double_hours") or 0)
        triple_hours = float(inputs.get("overtime_triple_hours") or 0)
        if double_hours <= 0 and triple_hours <= 0:
            return None

        hourly = self._hourly_wage(gross_salary, paid_days)
        amount = _round(
            hourly * FACTOR_HORA_DOBLE * double_hours
            + hourly * FACTOR_HORA_TRIPLE * triple_hours
        )

        cap = (
            UMA_DIARIA
            * HORAS_EXTRA_EXENTO_UMA_POR_SEMANA
            * PERIODICITIES[periodicity]["semanas"]
        )
        taxable, exempt = _split_exemption(
            amount, min(amount * HORAS_EXTRA_PORCENTAJE_EXENTO, cap)
        )

        return PayrollItem(
            kind=PERCEPTION,
            concept="horas_extra",
            description="Horas extra ({:g} dobles, {:g} triples)".format(
                double_hours, triple_hours
            ),
            amount=amount,
            taxable=taxable,
            exempt=exempt,
        )

    def _christmas_bonus(
        self, gross_salary: float, inputs: dict, paid_days: float
    ):
        days = float(inputs.get("christmas_bonus_days") or 0)
        if days <= 0:
            return None

        amount = _round(self._daily_wage(gross_salary, paid_days) * days)
        taxable, exempt = _split_exemption(
            amount, UMA_DIARIA * AGUINALDO_EXENTO_UMA
        )

        return PayrollItem(
            kind=PERCEPTION,
            concept="aguinaldo",
            description="Aguinaldo ({:g} dias)".format(days),
            amount=amount,
            taxable=taxable,
            exempt=exempt,
        )

    def _vacation_premium(
        self, gross_salary: float, inputs: dict, paid_days: float
    ):
        days = float(inputs.get("vacation_days") or 0)
        if days <= 0:
            return None

        amount = _round(
            self._daily_wage(gross_salary, paid_days)
            * days
            * PRIMA_VACACIONAL_PORCENTAJE
        )
        taxable, exempt = _split_exemption(
            amount, UMA_DIARIA * PRIMA_VACACIONAL_EXENTO_UMA
        )

        return PayrollItem(
            kind=PERCEPTION,
            concept="prima_vacacional",
            description="Prima vacacional ({:g} dias de vacaciones)".format(
                days
            ),
            amount=amount,
            taxable=taxable,
            exempt=exempt,
        )

    def _deductions(
        self, gross_salary: float, taxable_base: float, inputs: dict
    ) -> List[PayrollItem]:
        items = [
            PayrollItem(
                kind=DEDUCTION,
                concept="isr",
                description="ISR retenido",
                amount=self.isr_calc.calculate(taxable_base),
            ),
            PayrollItem(
                kind=DEDUCTION,
                concept="imss",
                description="IMSS retenido",
                amount=self.imss_calc.calculate(gross_salary),
            ),
        ]

        loan = float(inputs.get("loan_deduction") or 0)
        if loan > 0:
            items.append(
                PayrollItem(
                    kind=DEDUCTION,
                    concept="prestamo",
                    description="Prestamo a la empresa",
                    amount=_round(loan),
                )
            )

        housing = float(inputs.get("housing_credit_deduction") or 0)
        if housing > 0:
            items.append(
                PayrollItem(
                    kind=DEDUCTION,
                    concept="infonavit",
                    description="Credito Infonavit",
                    amount=_round(housing),
                )
            )

        return items

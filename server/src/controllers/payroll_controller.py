from abc import ABC, abstractmethod

UMA_MENSUAL = 3566.22
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


class TaxCalculationStrategy(ABC):
    @abstractmethod
    def calculate(self, base_salary: float) -> float:
        pass


class ISRStrategy(TaxCalculationStrategy):
    def calculate(self, base_salary: float) -> float:
        isr_causado = 0.0
        for limite_inferior, limite_superior, cuota_fija, porcentaje in ISR_TABLE:
            dentro_del_rango = base_salary >= limite_inferior and (
                limite_superior is None or base_salary <= limite_superior
            )
            if dentro_del_rango:
                isr_causado = cuota_fija + (base_salary - limite_inferior) * porcentaje
                break

        if base_salary <= ISR_SUBSIDIO_LIMITE:
            isr_causado = max(0.0, isr_causado - ISR_SUBSIDIO_MONTO)

        return round(isr_causado, 2)


class IMSSStrategy(TaxCalculationStrategy):
    def calculate(self, base_salary: float) -> float:
        tres_uma_mensual = UMA_MENSUAL * 3
        excedente = max(0.0, base_salary - tres_uma_mensual)

        cuotas_sobre_sbc = (
            IMSS_ENFERMEDAD_MATERNIDAD_DINERO
            + IMSS_GASTOS_MEDICOS_PENSIONADOS
            + IMSS_INVALIDEZ_VIDA
            + IMSS_CESANTIA_EDAD_AVANZADA_VEJEZ
        )

        imss = (
            base_salary * cuotas_sobre_sbc
            + excedente * IMSS_ENFERMEDAD_MATERNIDAD_EXCEDENTE
        )

        return round(imss, 2)


class PayrollService:
    def __init__(
        self,
        isr: TaxCalculationStrategy = ISRStrategy(),
        imss: TaxCalculationStrategy = IMSSStrategy()
    ):
        self.isr_calc = isr
        self.imss_calc = imss

    def process_salary(self, gross_salary: float) -> dict:
        if gross_salary < 0:
            raise ValueError("El salario no puede ser negativo")
        isr = self.isr_calc.calculate(gross_salary)
        imss = self.imss_calc.calculate(gross_salary)
        net = round(gross_salary - (isr + imss), 2)
        return {
            "gross_salary": gross_salary,
            "isr_deduction": isr,
            "imss_deduction": imss,
            "net_salary": net
        }

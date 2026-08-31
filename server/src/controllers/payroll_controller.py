from abc import ABC, abstractmethod

class TaxCalculationStrategy(ABC):
    @abstractmethod
    def calculate(self, base_salary: float) -> float:
        pass

class ISRStrategy(TaxCalculationStrategy):
    def calculate(self, base_salary: float) -> float:
        return round(base_salary * 0.16, 2)

class IMSSStrategy(TaxCalculationStrategy):
    def calculate(self, base_salary: float) -> float:
        return round(base_salary * 0.0275, 2)

class PayrollService:
    def __init__(self, isr: TaxCalculationStrategy = ISRStrategy(), imss: TaxCalculationStrategy = IMSSStrategy()):
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
            "isr": isr,
            "imss": imss,
            "net_salary": net
        }
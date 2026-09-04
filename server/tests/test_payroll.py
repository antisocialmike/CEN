import pytest
from server.src.controllers.payroll_controller import (
    PayrollService,
    ISRStrategy,
    IMSSStrategy
)


def test_isr_calculation():
    strategy = ISRStrategy()
    assert strategy.calculate(10000) == 192.8


def test_isr_calculation_bajo_limite_de_subsidio():
    strategy = ISRStrategy()
    assert strategy.calculate(5000) == 0.0


def test_imss_calculation():
    strategy = IMSSStrategy()
    assert strategy.calculate(10000) == 237.5


def test_imss_calculation_con_excedente_de_3_uma():
    strategy = IMSSStrategy()
    assert strategy.calculate(20000) == 512.21


def test_process_salary_success():
    service = PayrollService()
    result = service.process_salary(10000)

    assert result["gross_salary"] == 10000.0
    assert result["isr_deduction"] == 192.8
    assert result["imss_deduction"] == 237.5
    assert result["net_salary"] == 9569.7


def test_process_salary_negative_value_raises_error():
    service = PayrollService()
    with pytest.raises(ValueError, match="El salario no puede ser negativo"):
        service.process_salary(-500)

import pytest
from server.src.controllers.payroll_controller import (
    PayrollService,
    ISRStrategy,
    IMSSStrategy
)

def test_isr_calculation():
    strategy = ISRStrategy()
    # Salario base de 10,000 * 16% = 1,600
    assert strategy.calculate(10000) == 1600.0

def test_imss_calculation():
    strategy = IMSSStrategy()
    # Salario base de 10,000 * 2.75% = 275
    assert strategy.calculate(10000) == 275.0

def test_process_salary_success():
    service = PayrollService()
    result = service.process_salary(10000)
    
    assert result["gross_salary"] == 10000.0
    assert result["isr_deduction"] == 1600.0
    assert result["imss_deduction"] == 275.0
    # 10,000 - 1,600 - 275 = 8,125
    assert result["net_salary"] == 8125.0

def test_process_salary_negative_value_raises_error():
    service = PayrollService()
    # Verificamos que el sistema detenga cálculos inválidos correctamente
    with pytest.raises(ValueError, match="El salario no puede ser negativo"):
        service.process_salary(-500)
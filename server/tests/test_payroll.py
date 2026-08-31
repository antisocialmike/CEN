import pytest
from server.src.controllers.payroll_controller import PayrollService

@pytest.fixture
def service():
    return PayrollService()

def test_salary_calculation(service):
    res = service.process_salary(10000.0)
    assert res["gross_salary"] == 10000.0
    assert res["isr_deduction"] == 1600.0
    assert res["imss_deduction"] == 275.0
    assert res["net_salary"] == 8125.0

def test_zero_salary(service):
    res = service.process_salary(0.0)
    assert res["net_salary"] == 0.0

def test_negative_salary(service):
    with pytest.raises(ValueError):
        service.process_salary(-500.0)
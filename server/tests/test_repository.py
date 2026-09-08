from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from server.src.repositories.payroll_repository import PayrollRepository


@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.payroll_repository.db_cursor"
    ) as mock_db_cursor:
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


@pytest.fixture
def repository():
    return PayrollRepository()


def test_run_migrations_applies_every_pending_file(repository, cursor):
    cursor.fetchall.return_value = []

    applied = repository.run_migrations()

    assert applied == [
        "001_initial_schema.sql",
        "002_receipt_period_and_audit.sql",
    ]
    executed = " ".join(str(call[0][0]) for call in cursor.execute.call_args_list)
    assert "CREATE TABLE IF NOT EXISTS employees" in executed
    assert "ADD COLUMN IF NOT EXISTS period DATE" in executed


def test_run_migrations_skips_the_applied_ones(repository, cursor):
    cursor.fetchall.return_value = [{"filename": "001_initial_schema.sql"}]

    applied = repository.run_migrations()

    assert applied == ["002_receipt_period_and_audit.sql"]


def test_run_migrations_does_nothing_when_up_to_date(repository, cursor):
    cursor.fetchall.return_value = [
        {"filename": "001_initial_schema.sql"},
        {"filename": "002_receipt_period_and_audit.sql"},
    ]

    assert repository.run_migrations() == []


def test_get_employee_by_id_found(repository, cursor):
    cursor.fetchone.return_value = {
        "id": 1, "name": "Juan", "base_salary": 10000
    }

    result = repository.get_employee_by_id(1)

    assert result is not None
    assert result["name"] == "Juan"
    cursor.execute.assert_called_once()


def test_get_employee_by_id_not_found(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.get_employee_by_id(999) is None


def test_get_employee_by_email_found(repository, cursor):
    cursor.fetchone.return_value = {
        "id": 1, "name": "Juan", "email": "juan@cen.com",
        "role": "admin", "base_salary": 10000, "password_hash": "hashed"
    }

    result = repository.get_employee_by_email("juan@cen.com")

    assert result is not None
    assert result["email"] == "juan@cen.com"
    assert "password_hash" in cursor.execute.call_args[0][0]


def test_get_employee_by_email_not_found(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.get_employee_by_email("nadie@cen.com") is None


def test_create_employee_success(repository, cursor):
    cursor.fetchone.return_value = {"id": 10}

    result = repository.create_employee({
        "name": "Juan Perez",
        "email": "juan@cen.com",
        "role": "employee",
        "base_salary": 12000,
        "password_hash": "hashed"
    })

    assert result == 10


def test_create_employee_without_returned_id(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(RuntimeError, match="ID del empleado"):
        repository.create_employee({
            "name": "Juan Perez",
            "email": "juan@cen.com",
            "role": "employee",
            "base_salary": 12000,
            "password_hash": "hashed"
        })


def test_list_employees(repository, cursor):
    cursor.fetchall.return_value = [
        {
            "id": 1, "name": "Ana Lopez", "email": "ana@cen.com",
            "role": "employee", "base_salary": 9000
        },
        {
            "id": 2, "name": "Luis Diaz", "email": "luis@cen.com",
            "role": "admin", "base_salary": 15000
        }
    ]

    result = repository.list_employees()

    assert len(result) == 2
    assert result[0]["name"] == "Ana Lopez"


def test_list_employees_empty(repository, cursor):
    cursor.fetchall.return_value = []

    assert repository.list_employees() == []


def test_get_receipts_by_employee_id(repository, cursor):
    cursor.fetchall.return_value = [
        {
            "id": 1, "employee_id": 5, "gross_salary": 10000,
            "isr_deduction": 1600, "imss_deduction": 275,
            "net_salary": 8125, "created_at": "2026-09-01T10:00:00"
        }
    ]

    result = repository.get_receipts_by_employee_id(5)

    assert len(result) == 1
    assert result[0]["employee_id"] == 5


def test_list_recent_receipts_applies_the_limit(repository, cursor):
    cursor.fetchall.return_value = []

    repository.list_recent_receipts(5)

    assert cursor.execute.call_args[0][1] == (5,)


def _receipt(**overrides):
    data = {
        "employee_id": 1,
        "period": date(2026, 9, 1),
        "processed_by": "admin@cen.com",
        "gross_salary": 10000,
        "isr_deduction": 1600,
        "imss_deduction": 275,
        "net_salary": 8125,
    }
    data.update(overrides)
    return data


def test_save_payroll_receipt_creates_a_new_one(repository, cursor):
    cursor.fetchone.return_value = {"id": 100, "created": True}

    result = repository.save_payroll_receipt(_receipt())

    assert result == {"id": 100, "created": True}
    assert cursor.execute.call_args[0][1][1] == date(2026, 9, 1)
    assert cursor.execute.call_args[0][1][6] == "admin@cen.com"


def test_save_payroll_receipt_replaces_the_period(repository, cursor):
    cursor.fetchone.return_value = {"id": 100, "created": False}

    result = repository.save_payroll_receipt(_receipt())

    assert result == {"id": 100, "created": False}
    assert "ON CONFLICT (employee_id, period)" in cursor.execute.call_args[0][0]


def test_save_payroll_receipt_without_returned_id(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(RuntimeError, match="ID del recibo"):
        repository.save_payroll_receipt(_receipt())

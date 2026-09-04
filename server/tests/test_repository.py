import pytest
from unittest.mock import patch, MagicMock
from server.src.repositories.payroll_repository import PayrollRepository


@patch('server.src.repositories.payroll_repository.get_connection')
def test_get_employee_by_id_found(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"id": 1, "name": "Juan", "base_salary": 10000}

    repo = PayrollRepository()
    result = repo.get_employee_by_id(1)

    assert result is not None
    assert result["name"] == "Juan"
    mock_cursor.execute.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_get_employee_by_id_not_found(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    repo = PayrollRepository()
    result = repo.get_employee_by_id(999)

    assert result is None
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_get_employee_by_email_found(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "id": 1, "name": "Juan", "email": "juan@cen.com",
        "role": "admin", "base_salary": 10000, "password_hash": "hashed"
    }

    repo = PayrollRepository()
    result = repo.get_employee_by_email("juan@cen.com")

    assert result is not None
    assert result["email"] == "juan@cen.com"
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_get_employee_by_email_not_found(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    repo = PayrollRepository()
    result = repo.get_employee_by_email("nadie@cen.com")

    assert result is None
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_create_employee_success(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"id": 10}

    repo = PayrollRepository()
    employee_data = {
        "name": "Juan Perez",
        "email": "juan@cen.com",
        "role": "employee",
        "base_salary": 12000,
        "password_hash": "hashed"
    }
    result = repo.create_employee(employee_data)

    assert result == 10
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_list_employees(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "id": 1, "name": "Ana Lopez", "email": "ana@cen.com",
            "role": "employee", "base_salary": 9000
        },
        {
            "id": 2, "name": "Luis Diaz", "email": "luis@cen.com",
            "role": "admin", "base_salary": 15000
        }
    ]

    repo = PayrollRepository()
    result = repo.list_employees()

    assert len(result) == 2
    assert result[0]["name"] == "Ana Lopez"
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_list_employees_empty(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    repo = PayrollRepository()
    result = repo.list_employees()

    assert result == []
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_get_receipts_by_employee_id(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "id": 1, "employee_id": 5, "gross_salary": 10000,
            "isr_deduction": 1600, "imss_deduction": 275,
            "net_salary": 8125, "created_at": "2026-09-01T10:00:00"
        }
    ]

    repo = PayrollRepository()
    result = repo.get_receipts_by_employee_id(5)

    assert len(result) == 1
    assert result[0]["employee_id"] == 5
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_save_payroll_receipt_success(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"id": 100}

    repo = PayrollRepository()
    receipt_data = {
        "employee_id": 1,
        "gross_salary": 10000,
        "isr_deduction": 1600,
        "imss_deduction": 275,
        "net_salary": 8125
    }
    result = repo.save_payroll_receipt(receipt_data)

    assert result == 100
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('server.src.repositories.payroll_repository.get_connection')
def test_save_payroll_receipt_fails(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    repo = PayrollRepository()
    receipt_data = {
        "employee_id": 1, "gross_salary": 10000,
        "isr_deduction": 1600, "imss_deduction": 275, "net_salary": 8125
    }

    with pytest.raises(RuntimeError, match="No se pudo obtener el ID del recibo"):
        repo.save_payroll_receipt(receipt_data)

    mock_conn.close.assert_called_once()

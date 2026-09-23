from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from server.src.repositories.payroll_repository import (
    MIGRATIONS_DIR,
    PayrollRepository,
    ReceiptOfAnotherCompanyError,
    SharedAdminError,
)


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


def _migration_names():
    return sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))


def test_run_migrations_applies_every_pending_file(repository, cursor):
    cursor.fetchall.return_value = []

    applied = repository.run_migrations()

    assert applied == _migration_names()
    executed = " ".join(str(call[0][0]) for call in cursor.execute.call_args_list)
    assert "CREATE TABLE IF NOT EXISTS schema_migrations" in executed
    assert "CREATE TABLE IF NOT EXISTS employees" in executed


def test_run_migrations_skips_the_applied_ones(repository, cursor):
    names = _migration_names()
    cursor.fetchall.return_value = [{"filename": names[0]}]

    assert repository.run_migrations() == names[1:]


def test_run_migrations_does_nothing_when_up_to_date(repository, cursor):
    cursor.fetchall.return_value = [
        {"filename": name} for name in _migration_names()
    ]

    assert repository.run_migrations() == []


COMPANY = 1


def _queries(cursor) -> list:
    return [str(call[0][0]) for call in cursor.execute.call_args_list]


def _member(is_shared=False, role="employee"):
    return {"id": 3, "role": role, "is_shared": is_shared}


def _saved_row(**overrides):
    row = {
        "id": 3, "name": "Ana", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000, "is_active": True
    }
    row.update(overrides)
    return row


def test_get_employee_by_id_found(repository, cursor):
    cursor.fetchone.return_value = {
        "id": 1, "name": "Juan", "base_salary": 10000
    }

    result = repository.get_employee_by_id(1, COMPANY)

    assert result is not None
    assert result["name"] == "Juan"
    assert cursor.execute.call_args[0][1] == (1, COMPANY, COMPANY)


def test_get_employee_by_id_not_found(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.get_employee_by_id(999, COMPANY) is None


def test_get_employee_by_email_found(repository, cursor):
    cursor.fetchone.return_value = {
        "id": 1, "name": "Juan", "email": "juan@cen.com",
        "role": "admin", "base_salary": 10000, "password_hash": "hashed"
    }

    result = repository.get_employee_by_email("juan@cen.com")

    assert result is not None
    assert result["email"] == "juan@cen.com"
    assert "password_hash" in cursor.execute.call_args[0][0]
    assert "company_id" in cursor.execute.call_args[0][0]


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
    }, COMPANY)

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
        }, COMPANY)


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

    result = repository.list_employees(COMPANY)

    assert len(result) == 2
    assert result[0]["name"] == "Ana Lopez"
    assert cursor.execute.call_args[0][1] == (COMPANY, COMPANY)


def test_admin_queries_only_see_the_company(repository, cursor):
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None

    repository.list_employees(COMPANY)
    repository.get_employee_by_id(1, COMPANY)
    repository.update_employee(1, {
        "name": "Ana", "email": "ana@cen.com",
        "role": "employee", "base_salary": 1
    }, COMPANY)
    repository.set_employee_active(1, False, COMPANY)
    repository.reset_password(1, "hash", COMPANY)

    queries = _queries(cursor)
    assert len(queries) == 5
    for query in queries:
        assert "role IN ('admin', 'employee')" in query
        assert "e.company_id = %s" in query
        assert "ca.is_active" in query


def test_list_employees_empty(repository, cursor):
    cursor.fetchall.return_value = []

    assert repository.list_employees(COMPANY) == []


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


def test_list_recent_receipts_applies_the_company_and_limit(
    repository, cursor
):
    cursor.fetchall.return_value = []

    repository.list_recent_receipts(COMPANY, 5)

    query, params = cursor.execute.call_args[0]
    assert "WHERE r.company_id = %s" in query
    assert params == (COMPANY, 5)


def _receipt(**overrides):
    data = {
        "employee_id": 1,
        "company_id": COMPANY,
        "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30),
        "periodicity": "mensual",
        "paid_days": 30,
        "processed_by": "admin@cen.com",
        "gross_salary": 10000,
        "isr_deduction": 1600,
        "imss_deduction": 275,
        "net_salary": 8125,
        "total_perceptions": 10000,
        "total_deductions": 1875,
        "taxable_base": 10000,
        "items": [
            {
                "kind": "perception", "concept": "sueldo",
                "description": "Sueldo del periodo", "amount": 10000,
                "taxable": 10000, "exempt": 0
            },
            {
                "kind": "deduction", "concept": "isr",
                "description": "ISR retenido", "amount": 1600,
                "taxable": 0, "exempt": 0
            },
        ],
    }
    data.update(overrides)
    return data


def test_save_payroll_receipt_creates_a_new_one(repository, cursor):
    cursor.fetchone.return_value = {"id": 100, "created": True}

    result = repository.save_payroll_receipt(_receipt())

    assert result == {"id": 100, "created": True}
    upsert = cursor.execute.call_args_list[0][0][1]
    assert upsert[1] == date(2026, 9, 1)
    assert upsert[2] == date(2026, 9, 30)
    assert upsert[3] == "mensual"
    assert upsert[12] == "admin@cen.com"
    assert upsert[13] == COMPANY


def test_save_payroll_receipt_replaces_the_items(repository, cursor):
    cursor.fetchone.return_value = {"id": 100, "created": False}

    repository.save_payroll_receipt(_receipt())

    queries = _queries(cursor)
    assert any("DELETE FROM payroll_receipt_items" in q for q in queries)
    assert sum(
        "INSERT INTO payroll_receipt_items" in q for q in queries
    ) == 2


def test_save_payroll_receipt_replaces_the_period(repository, cursor):
    cursor.fetchone.return_value = {"id": 100, "created": False}

    result = repository.save_payroll_receipt(_receipt())

    assert result == {"id": 100, "created": False}
    upsert = _queries(cursor)[0]
    assert "ON CONFLICT (employee_id, period_start, period_end)" in upsert
    assert (
        "WHERE payroll_receipts.company_id = EXCLUDED.company_id" in upsert
    )


def test_save_payroll_receipt_of_another_company(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(ReceiptOfAnotherCompanyError):
        repository.save_payroll_receipt(_receipt())

    assert not any("payroll_receipt_items" in q for q in _queries(cursor))


def test_get_password_hash_found(repository, cursor):
    cursor.fetchone.return_value = {"password_hash": "hashed"}

    assert repository.get_password_hash(7) == "hashed"


def test_get_password_hash_for_a_missing_employee(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.get_password_hash(999) is None


def test_update_password_clears_the_forced_change(repository, cursor):
    repository.update_password(7, "nuevo_hash")

    query, params = cursor.execute.call_args[0]
    assert "must_change_password = FALSE" in query
    assert params == ("nuevo_hash", 7)


def test_create_employee_forces_the_first_password_change(repository, cursor):
    cursor.fetchone.return_value = {"id": 10}

    repository.create_employee({
        "name": "Juan Perez",
        "email": "juan@cen.com",
        "role": "employee",
        "base_salary": 12000,
        "password_hash": "hashed"
    }, COMPANY)

    assert "TRUE, %s) RETURNING id" in cursor.execute.call_args[0][0]


def test_create_employee_links_the_employee_to_the_company(
    repository, cursor
):
    cursor.fetchone.return_value = {"id": 10}

    repository.create_employee({
        "name": "Juan Perez",
        "email": "juan@cen.com",
        "role": "employee",
        "base_salary": 12000,
        "password_hash": "hashed"
    }, COMPANY)

    assert cursor.execute.call_args[0][1][-1] == COMPANY
    assert not any("company_admins" in q for q in _queries(cursor))


def test_create_admin_assigns_it_to_the_company(repository, cursor):
    cursor.fetchone.return_value = {"id": 11}

    repository.create_employee({
        "name": "Luis Diaz",
        "email": "luis@cen.com",
        "role": "admin",
        "base_salary": 15000,
        "password_hash": "hashed"
    }, COMPANY, actor_id=7)

    insert, assign = cursor.execute.call_args_list
    assert insert[0][1][-1] is None
    assert "INSERT INTO company_admins" in assign[0][0]
    assert assign[0][1] == (11, COMPANY, 7)


def test_create_superadmin_belongs_to_no_company(repository, cursor):
    cursor.fetchone.return_value = {"id": 12}

    repository.create_employee({
        "name": "Root",
        "email": "root@cen.com",
        "role": "superadmin",
        "base_salary": None,
        "password_hash": "hashed"
    })

    assert cursor.execute.call_count == 1
    assert cursor.execute.call_args[0][1][-1] is None


def test_first_company_id(repository, cursor):
    cursor.fetchone.return_value = {"id": 1}

    assert repository.first_company_id() == 1


def test_update_employee_returns_the_saved_row(repository, cursor):
    cursor.fetchone.side_effect = [_member(), _saved_row()]

    result = repository.update_employee(3, {
        "name": "Ana", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000
    }, COMPANY)

    assert result is not None
    assert result["base_salary"] == 19000
    assert cursor.execute.call_args_list[1][0][1] == (
        "Ana", "ana@cen.com", "employee", 19000, COMPANY, 3
    )


def test_update_employee_to_admin_assigns_the_company(repository, cursor):
    cursor.fetchone.side_effect = [_member(), _saved_row(role="admin")]

    repository.update_employee(3, {
        "name": "Ana", "email": "ana@cen.com",
        "role": "admin", "base_salary": 19000
    }, COMPANY, actor_id=7)

    lock, update, assign = cursor.execute.call_args_list
    assert "FOR UPDATE OF e" in lock[0][0]
    assert update[0][1][4] is None
    assert "INSERT INTO company_admins" in assign[0][0]
    assert assign[0][1] == (3, COMPANY, 7)


def test_update_admin_to_employee_releases_the_assignment(repository, cursor):
    cursor.fetchone.side_effect = [_member(role="admin"), _saved_row()]

    repository.update_employee(3, {
        "name": "Ana", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000
    }, COMPANY)

    release = cursor.execute.call_args_list[-1][0]
    assert "UPDATE company_admins SET is_active = FALSE" in release[0]
    assert release[1] == (3,)


def test_update_employee_for_a_missing_row(repository, cursor):
    cursor.fetchone.return_value = None

    result = repository.update_employee(999, {
        "name": "Ana", "email": "ana@cen.com",
        "role": "employee", "base_salary": 19000
    }, COMPANY)

    assert result is None
    assert cursor.execute.call_count == 1


@pytest.mark.parametrize("action", ["update", "activate", "reset"])
def test_admins_shared_with_other_companies_are_off_limits(
    repository, cursor, action
):
    cursor.fetchone.return_value = _member(is_shared=True, role="admin")

    with pytest.raises(SharedAdminError):
        if action == "update":
            repository.update_employee(3, {
                "name": "Ana", "email": "ana@cen.com",
                "role": "admin", "base_salary": 1
            }, COMPANY)
        elif action == "activate":
            repository.set_employee_active(3, False, COMPANY)
        else:
            repository.reset_password(3, "hash", COMPANY)

    assert cursor.execute.call_count == 1


def test_set_employee_active(repository, cursor):
    cursor.fetchone.side_effect = [_member(), _saved_row(is_active=False)]

    result = repository.set_employee_active(3, False, COMPANY)

    assert result is not None
    assert result["is_active"] is False
    assert cursor.execute.call_args[0][1] == (False, 3)


def test_reset_password_of_another_company(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.reset_password(3, "hash", 2) is None
    assert cursor.execute.call_count == 1


def test_list_employees_puts_the_active_ones_first(repository, cursor):
    cursor.fetchall.return_value = []

    repository.list_employees(COMPANY)

    assert "ORDER BY e.is_active DESC" in cursor.execute.call_args[0][0]


def test_get_receipt_by_id_joins_the_employee(repository, cursor):
    cursor.fetchone.return_value = {
        "id": 42, "employee_id": 3, "employee_name": "Ana",
        "employee_email": "ana@cen.com", "net_salary": 17804.14
    }

    result = repository.get_receipt_by_id(42)

    assert result is not None
    assert result["employee_email"] == "ana@cen.com"
    assert "JOIN employees" in cursor.execute.call_args[0][0]
    assert "r.company_id" in cursor.execute.call_args[0][0]


def test_get_receipt_by_id_not_found(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.get_receipt_by_id(999) is None


def test_get_receipt_by_period_matches_the_exact_range(repository, cursor):
    cursor.fetchone.return_value = {"id": 12, "net_salary": 17862.79}

    result = repository.get_receipt_by_period(
        3, date(2026, 9, 1), date(2026, 9, 30), COMPANY
    )

    assert result is not None
    assert cursor.execute.call_args[0][1] == (
        3, date(2026, 9, 1), date(2026, 9, 30), COMPANY
    )


def test_get_receipt_by_period_when_the_period_is_free(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.get_receipt_by_period(
        3, date(2026, 10, 1), date(2026, 10, 31), COMPANY
    ) is None

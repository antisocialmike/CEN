from datetime import date
from decimal import Decimal

import psycopg2
import pytest

from server.src.config.database import db_cursor
from server.src.repositories.payroll_repository import (
    MIGRATIONS_DIR,
    payroll_repository,
)
from server.tests.integration.conftest import database_before


def _columns(table: str) -> dict:
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT column_name, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_name = %s;",
            (table,),
        )
        return {row["column_name"]: dict(row) for row in cursor.fetchall()}


def test_every_migration_applies_on_an_empty_database(postgres):
    assert postgres == sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))


def test_running_them_again_applies_nothing():
    assert payroll_repository.run_migrations() == []


def test_the_hire_date_is_required_and_starts_today_by_default():
    column = _columns("employments")["hire_date"]

    assert column["is_nullable"] == "NO"
    assert "CURRENT_DATE" in column["column_default"]


def test_reset_codes_are_no_longer_kept_in_clear():
    columns = _columns("password_reset_tokens")

    assert {"code_hash", "attempts"} <= set(columns)
    assert not {"code", "token"} & set(columns)


def test_the_accounts_carry_their_session_version():
    assert _columns("employees")["token_version"]["is_nullable"] == "NO"


def _insert_people(cursor, *emails) -> list:
    ids = []
    for email in emails:
        cursor.execute(
            "INSERT INTO employees (name, email, role, base_salary, "
            "password_hash, company_id) VALUES ('Persona', %s, 'employee', 1, "
            "'x', 1) RETURNING id;", (email,),
        )
        ids.append(cursor.fetchone()["id"])
    return ids


def test_the_emails_are_lowered_unless_two_would_collide():
    with database_before("018") as (connection, migration):
        with connection, connection.cursor() as cursor:
            ids = _insert_people(
                cursor, " Ana.Lopez@CEN.com", "luis@cen.com",
                "Rosa@cen.com", "ROSA@cen.com",
            )
            cursor.execute(migration)
            cursor.execute(
                "SELECT id, email FROM employees WHERE id = ANY(%s) ORDER BY id;",
                (ids,),
            )
            emails = [row["email"] for row in cursor.fetchall()]

    assert emails == [
        "ana.lopez@cen.com", "luis@cen.com", "Rosa@cen.com", "ROSA@cen.com",
    ]


def test_after_the_migration_an_email_in_capitals_is_rejected():
    with pytest.raises(psycopg2.errors.CheckViolation):
        with db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO employees (name, email, role, password_hash) "
                "VALUES ('Persona', 'Nueva@CEN.com', 'employee', 'x');"
            )


def test_the_labor_data_no_longer_lives_in_the_account():
    columns = set(_columns("employees"))

    assert not {
        "company_id", "base_salary", "tipo_regimen", "tipo_jornada",
        "hire_date", "deactivated_at",
    } & columns
    assert {"rfc", "curp", "nss", "is_active"} <= columns


def test_the_employments_start_from_the_accounts_that_existed():
    with database_before("019") as (connection, migration):
        with connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO companies (legal_name) VALUES ('Segunda') "
                "RETURNING id;"
            )
            second = cursor.fetchone()["id"]
            cursor.execute(
                "INSERT INTO employees (name, email, role, base_salary, "
                "password_hash, company_id, hire_date, tipo_regimen, "
                "is_active, deactivated_at) VALUES "
                "('Ana', 'ana@relleno.cen', 'employee', 19000, 'x', 1, "
                "'2020-01-15', '09', FALSE, '2026-08-31'), "
                "('Luis', 'luis@relleno.cen', 'admin', 25000, 'x', NULL, "
                "'2019-03-01', '02', TRUE, NULL), "
                "('Pablo', 'pablo@relleno.cen', 'admin', NULL, 'x', NULL, "
                "'2021-05-10', '02', TRUE, NULL) RETURNING id;"
            )
            ana, luis, pablo = [row["id"] for row in cursor.fetchall()]
            cursor.execute(
                "INSERT INTO company_admins (admin_id, company_id) "
                "VALUES (%s, 1), (%s, %s), (%s, 1);",
                (luis, luis, second, pablo),
            )
            cursor.execute(migration)
            cursor.execute(
                "SELECT employee_id, company_id, base_salary, hire_date, "
                "tipo_regimen, is_active, deactivated_at IS NOT NULL AS left "
                "FROM employments ORDER BY employee_id, company_id;"
            )
            rows = [dict(row) for row in cursor.fetchall()]

    assert rows == [
        {"employee_id": ana, "company_id": 1,
         "base_salary": Decimal("19000.00"), "hire_date": date(2020, 1, 15),
         "tipo_regimen": "09", "is_active": False, "left": True},
        {"employee_id": luis, "company_id": 1,
         "base_salary": Decimal("25000.00"), "hire_date": date(2019, 3, 1),
         "tipo_regimen": "02", "is_active": True, "left": False},
        {"employee_id": luis, "company_id": second,
         "base_salary": Decimal("25000.00"), "hire_date": date(2019, 3, 1),
         "tipo_regimen": "02", "is_active": True, "left": False},
    ]

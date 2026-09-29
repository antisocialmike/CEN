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
    column = _columns("employees")["hire_date"]

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
            _insert_people(cursor, "Nueva@CEN.com")

from server.src.config.database import db_cursor
from server.src.repositories.payroll_repository import (
    MIGRATIONS_DIR,
    payroll_repository,
)


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

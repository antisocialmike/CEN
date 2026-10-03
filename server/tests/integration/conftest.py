import os
import uuid
from contextlib import contextmanager
from unittest.mock import patch

import psycopg2
import pytest
from psycopg2.extensions import make_dsn
from psycopg2.extras import RealDictCursor

from server.src.config import database
from server.src.middlewares.auth_middleware import create_access_token
from server.src.repositories.company_repository import company_repository
from server.src.repositories.payroll_repository import (
    MIGRATIONS_DIR,
    payroll_repository,
)

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")


@pytest.fixture(scope="package", autouse=True)
def postgres():
    if not TEST_DATABASE_URL:
        pytest.skip("Sin TEST_DATABASE_URL no hay PostgreSQL contra el cual probar")

    name = "cen_pruebas_" + uuid.uuid4().hex[:12]
    server = psycopg2.connect(TEST_DATABASE_URL)
    server.autocommit = True
    with server.cursor() as cursor:
        cursor.execute('CREATE DATABASE "{}"'.format(name))

    database.close_pool()
    try:
        with patch.object(
            database, "DATABASE_URL", make_dsn(TEST_DATABASE_URL, dbname=name)
        ):
            yield payroll_repository.run_migrations()
            database.close_pool()
    finally:
        with server.cursor() as cursor:
            cursor.execute('DROP DATABASE IF EXISTS "{}" WITH (FORCE)'.format(name))
        server.close()


@pytest.fixture
def session_state():
    yield None


@pytest.fixture
def rate_limit_window():
    yield None


def unique_email(name: str) -> str:
    return "{}-{}@pruebas.cen".format(name, uuid.uuid4().hex[:8])


def company_with_admin(superadmin: int, owner: int, password_hash: str) -> dict:
    company = company_repository.create_company(
        {"legal_name": "Empresa " + uuid.uuid4().hex[:6]}, owner, superadmin
    )
    admin = company_repository.invite_admin(company, {
        "name": "Admin", "email": unique_email("admin"),
        "password_hash": password_hash,
    }, owner)
    payroll_repository.update_password(admin, password_hash)
    token = create_access_token(data={
        "sub": "admin@pruebas.cen", "role": "admin", "employee_id": admin,
        "ver": 1,
    })
    return {
        "id": company,
        "admin": admin,
        "headers": {
            "Authorization": "Bearer " + token, "X-Company-Id": str(company),
        },
    }


@contextmanager
def database_before(migration_prefix: str):
    name = "cen_relleno_" + uuid.uuid4().hex[:12]
    server = psycopg2.connect(TEST_DATABASE_URL)
    server.autocommit = True
    with server.cursor() as cursor:
        cursor.execute('CREATE DATABASE "{}"'.format(name))
    connection = psycopg2.connect(
        make_dsn(TEST_DATABASE_URL, dbname=name), cursor_factory=RealDictCursor
    )
    try:
        migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
        with connection, connection.cursor() as cursor:
            for path in migrations:
                if path.name < migration_prefix:
                    cursor.execute(path.read_text(encoding="utf-8"))
        target = next(
            path for path in migrations if path.name.startswith(migration_prefix)
        )
        yield connection, target.read_text(encoding="utf-8")
    finally:
        connection.close()
        with server.cursor() as cursor:
            cursor.execute('DROP DATABASE IF EXISTS "{}" WITH (FORCE)'.format(name))
        server.close()

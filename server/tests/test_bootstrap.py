from unittest.mock import patch

from server.src import bootstrap
from server.src.config.settings import ADMIN_EMAIL


def test_bootstrap_creates_the_admin_account_when_missing():
    with patch.object(bootstrap, "payroll_repository") as repository:
        repository.get_employee_by_email.return_value = None

        assert bootstrap.bootstrap_database() is True

    repository.run_migrations.assert_called_once()
    created = repository.create_employee.call_args[0][0]
    assert created["email"] == ADMIN_EMAIL
    assert created["role"] == "admin"
    assert created["password_hash"] != bootstrap.ADMIN_PASSWORD


def test_bootstrap_keeps_an_existing_admin_account():
    with patch.object(bootstrap, "payroll_repository") as repository:
        repository.get_employee_by_email.return_value = {"id": 1}

        assert bootstrap.bootstrap_database() is True

    repository.create_employee.assert_not_called()


def test_bootstrap_survives_an_unavailable_database():
    with patch.object(bootstrap, "payroll_repository") as repository:
        repository.run_migrations.side_effect = OSError("db caida")

        assert bootstrap.bootstrap_database() is False

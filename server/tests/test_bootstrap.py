from unittest.mock import patch

from server.src import bootstrap
from server.src.config.settings import ADMIN_EMAIL


def test_bootstrap_creates_the_admin_account_when_missing():
    with patch.object(bootstrap, "payroll_repository") as repository:
        repository.get_employee_by_email.return_value = None

        assert bootstrap.bootstrap_database() is True

    repository.run_migrations.assert_called_once()
    created, company_id = repository.create_employee.call_args[0]
    assert created["email"] == ADMIN_EMAIL
    assert created["role"] == "admin"
    assert created["password_hash"] != bootstrap.ADMIN_PASSWORD
    assert company_id == repository.first_company_id.return_value


def test_bootstrap_keeps_an_existing_admin_account():
    with patch.object(bootstrap, "payroll_repository") as repository:
        repository.get_employee_by_email.return_value = {"id": 1}

        assert bootstrap.bootstrap_database() is True

    repository.create_employee.assert_not_called()


def test_bootstrap_survives_an_unavailable_database():
    with patch.object(bootstrap, "payroll_repository") as repository:
        repository.run_migrations.side_effect = OSError("db caida")

        assert bootstrap.bootstrap_database() is False


def _bootstrap_with_superadmin(existing=None, password="clave-larga-segura"):
    with patch.object(bootstrap, "payroll_repository") as repository, \
            patch.object(bootstrap, "SUPERADMIN_EMAIL", "root@cen.com"), \
            patch.object(bootstrap, "SUPERADMIN_PASSWORD", password):
        repository.get_employee_by_email.side_effect = (
            lambda email: {"id": 1} if email == ADMIN_EMAIL else existing
        )
        assert bootstrap.bootstrap_database() is True
    return repository


def test_bootstrap_creates_the_superadmin_when_configured():
    repository = _bootstrap_with_superadmin()

    created = repository.create_employee.call_args[0][0]
    assert created["email"] == "root@cen.com"
    assert created["role"] == "superadmin"
    assert created["base_salary"] is None
    assert created["password_hash"] != "clave-larga-segura"


def test_bootstrap_skips_the_superadmin_without_configuration():
    with patch.object(bootstrap, "payroll_repository") as repository, \
            patch.object(bootstrap, "SUPERADMIN_EMAIL", ""):
        repository.get_employee_by_email.return_value = {"id": 1}
        bootstrap.bootstrap_database()

    repository.create_employee.assert_not_called()


def test_bootstrap_rejects_a_short_superadmin_password():
    repository = _bootstrap_with_superadmin(password="corta")

    repository.create_employee.assert_not_called()


def test_bootstrap_does_not_promote_an_existing_account():
    repository = _bootstrap_with_superadmin(
        existing={"id": 3, "role": "admin"}
    )

    repository.create_employee.assert_not_called()

from unittest.mock import patch

import pytest

from server.src import bootstrap
from server.src.config.settings import ADMIN_EMAIL


@pytest.fixture(autouse=True)
def no_optional_accounts():
    # settings.py carga el .env local: sin esto, un superadmin o un dueño
    # configurados ahi se colarian en las pruebas del admin.
    with patch.object(bootstrap, "SUPERADMIN_EMAIL", ""), \
            patch.object(bootstrap, "OWNER_EMAIL", ""):
        yield


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


def test_database_ready_retries_a_pending_bootstrap():
    with patch.object(bootstrap, "_ready", False), \
            patch.object(bootstrap, "payroll_repository") as repository, \
            patch.object(bootstrap, "ping") as ping:
        repository.get_employee_by_email.return_value = {"id": 1}

        assert bootstrap.database_ready() is True
        assert bootstrap._ready is True

    repository.run_migrations.assert_called_once()
    ping.assert_not_called()


def test_database_ready_stays_pending_while_the_database_is_down():
    with patch.object(bootstrap, "_ready", False), \
            patch.object(bootstrap, "payroll_repository") as repository:
        repository.run_migrations.side_effect = OSError("db caida")

        assert bootstrap.database_ready() is False
        assert bootstrap._ready is False


def test_database_ready_only_pings_once_prepared():
    with patch.object(bootstrap, "_ready", True), \
            patch.object(bootstrap, "payroll_repository") as repository, \
            patch.object(bootstrap, "ping") as ping:
        assert bootstrap.database_ready() is True

        ping.side_effect = OSError("db caida")
        assert bootstrap.database_ready() is False

    repository.run_migrations.assert_not_called()


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


def _bootstrap_with_owner(existing=None, password="clave-larga-segura"):
    with patch.object(bootstrap, "payroll_repository") as repository, \
            patch.object(bootstrap, "company_repository") as companies, \
            patch.object(bootstrap, "OWNER_EMAIL", "dueno@cen.com"), \
            patch.object(bootstrap, "OWNER_PASSWORD", password):
        repository.get_employee_by_email.side_effect = (
            lambda email: {"id": 1} if email == ADMIN_EMAIL else existing
        )
        repository.create_employee.return_value = 7
        repository.first_company_id.return_value = 1
        assert bootstrap.bootstrap_database() is True
    return repository, companies


def test_bootstrap_creates_the_owner_of_the_first_company():
    repository, companies = _bootstrap_with_owner()

    created = repository.create_employee.call_args[0][0]
    assert created["email"] == "dueno@cen.com"
    assert created["role"] == "owner"
    assert created["base_salary"] is None
    assert created["password_hash"] != "clave-larga-segura"
    companies.link_owner.assert_called_once_with(7, 1)


def test_bootstrap_rejects_a_short_owner_password():
    repository, companies = _bootstrap_with_owner(password="corta")

    repository.create_employee.assert_not_called()
    companies.link_owner.assert_not_called()


def test_bootstrap_does_not_turn_an_existing_account_into_owner():
    repository, companies = _bootstrap_with_owner(
        existing={"id": 3, "role": "admin"}
    )

    repository.create_employee.assert_not_called()
    companies.link_owner.assert_not_called()

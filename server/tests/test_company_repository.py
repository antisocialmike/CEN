from unittest.mock import MagicMock, patch

import pytest

from server.src.repositories.company_repository import (
    CompanyRepository,
    NotFoundError,
    OrphanedCompanyError,
)


@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.company_repository.db_cursor"
    ) as mock_db_cursor:
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


@pytest.fixture
def repository():
    return CompanyRepository()


def _queries(cursor) -> list:
    return [str(call[0][0]) for call in cursor.execute.call_args_list]


def _audits(cursor) -> list:
    return [
        call[0][1] for call in cursor.execute.call_args_list
        if "platform_audit_log" in str(call[0][0])
    ]


def test_list_owners_only_brings_owners(repository, cursor):
    cursor.fetchall.return_value = []

    assert repository.list_owners() == []
    assert "e.role = 'owner'" in _queries(cursor)[0]


def test_create_owner_forces_the_password_change(repository, cursor):
    cursor.fetchone.return_value = {"id": 5}

    owner_id = repository.create_owner({
        "name": "Laura", "email": "laura@grupo.mx", "password_hash": "hash",
    }, actor_id=99)

    assert owner_id == 5
    insert = _queries(cursor)[0]
    assert "'owner', NULL" in insert
    assert "must_change_password) VALUES" in insert
    actor, action, target_type, target_id, _ = _audits(cursor)[0]
    assert (actor, action, target_type, target_id) == (
        99, "owner.create", "owner", 5
    )


def test_update_a_missing_owner(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.update_owner(7, {"name": "X", "email": "x@x.mx"}, 99)

    assert _audits(cursor) == []


def test_deactivate_an_owner_that_would_orphan_a_company(repository, cursor):
    cursor.fetchall.return_value = [{"id": 1, "legal_name": "Grupo Norte"}]

    with pytest.raises(OrphanedCompanyError) as error:
        repository.set_owner_active(5, False, 99)

    assert error.value.companies[0]["legal_name"] == "Grupo Norte"
    assert "FOR UPDATE OF c" in _queries(cursor)[0]
    assert not any("SET is_active" in q for q in _queries(cursor))


def test_deactivate_an_owner_with_partners(repository, cursor):
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = {"id": 5}

    repository.set_owner_active(5, False, 99)

    assert cursor.execute.call_args_list[0][0][1] == (5, None, None, 5)
    assert _audits(cursor)[0][1] == "owner.deactivate"


def test_activate_an_owner_skips_the_orphan_check(repository, cursor):
    cursor.fetchone.return_value = {"id": 5}

    repository.set_owner_active(5, True, 99)

    assert not any("NOT EXISTS" in q for q in _queries(cursor))
    assert _audits(cursor)[0][1] == "owner.activate"


def test_reset_owner_password_is_scoped_to_owners(repository, cursor):
    cursor.fetchone.return_value = {
        "id": 5, "name": "Laura", "email": "laura@grupo.mx"
    }

    result = repository.reset_owner_password(5, "hash", 99)

    assert result["id"] == 5
    assert "role = 'owner'" in _queries(cursor)[0]
    assert _audits(cursor)[0][1] == "owner.reset_password"


def test_create_company_needs_an_active_owner(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.create_company({"legal_name": "Grupo Norte"}, 404, 99)

    assert not any("INSERT INTO companies" in q for q in _queries(cursor))


def test_create_company_links_its_first_owner(repository, cursor):
    cursor.fetchone.side_effect = [{"id": 5}, {"id": 1}, {"owner_id": 5}]

    company_id = repository.create_company({
        "legal_name": "Grupo Norte", "rfc": "GNO010101AB1",
    }, 5, 99)

    assert company_id == 1
    queries = _queries(cursor)
    assert "FOR SHARE" in queries[0]
    assert "INSERT INTO companies" in queries[1]
    assert "INSERT INTO company_owners" in queries[2]
    assert cursor.execute.call_args_list[2][0][1] == (5, 1)
    assert _audits(cursor)[0][1] == "company.create"


def test_update_a_missing_company(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.update_company(404, {"legal_name": "X"}, 99)


def test_assign_an_owner_twice_audits_once(repository, cursor):
    cursor.fetchone.side_effect = [{"id": 1}, {"id": 5}, None]

    repository.assign_owner(1, 5, 99)

    assert _audits(cursor) == []


def test_assign_owner_to_a_missing_company(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.assign_owner(404, 5, 99)


def test_unassign_the_last_owner(repository, cursor):
    cursor.fetchone.return_value = {"id": 1}
    cursor.fetchall.return_value = [{"id": 1, "legal_name": "Grupo Norte"}]

    with pytest.raises(OrphanedCompanyError):
        repository.unassign_owner(1, 5, 99)

    assert cursor.execute.call_args_list[1][0][1] == (5, 1, 1, 5)
    assert not any("DELETE" in q for q in _queries(cursor))


def test_unassign_an_owner_with_partners(repository, cursor):
    cursor.fetchone.side_effect = [{"id": 1}, {"owner_id": 5}]
    cursor.fetchall.return_value = []

    repository.unassign_owner(1, 5, 99)

    assert any("DELETE FROM company_owners" in q for q in _queries(cursor))
    assert _audits(cursor)[0][1] == "company.unassign_owner"


def test_unassign_an_owner_that_was_not_assigned(repository, cursor):
    cursor.fetchone.side_effect = [{"id": 1}, None]
    cursor.fetchall.return_value = []

    with pytest.raises(NotFoundError):
        repository.unassign_owner(1, 7, 99)


def test_list_owner_companies_only_brings_their_own(repository, cursor):
    cursor.fetchall.return_value = []

    repository.list_owner_companies(20)

    query, params = cursor.execute.call_args[0]
    assert "o.owner_id = %s" in query
    assert "ca.is_active" in query
    assert params == (20,)


def test_get_owner_company(repository, cursor):
    cursor.fetchone.return_value = {"id": 1}

    assert repository.get_owner_company(20, 1) == {"id": 1}
    assert cursor.execute.call_args[0][1] == (20, 1)


@pytest.mark.parametrize("active, action", [
    (False, "company.deactivate"), (True, "company.activate"),
])
def test_set_company_active_is_audited(repository, cursor, active, action):
    cursor.fetchone.return_value = {"id": 1}

    repository.set_company_active(1, active, 20)

    assert cursor.execute.call_args_list[0][0][1] == (active, 1)
    assert _audits(cursor)[0][:4] == (20, action, "company", 1)


def test_set_active_on_a_missing_company(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.set_company_active(404, False, 20)


def test_invite_admin_creates_the_account_and_assigns_it(repository, cursor):
    cursor.fetchone.return_value = {"id": 31}

    admin_id = repository.invite_admin(1, {
        "name": "Pablo", "email": "pablo@norte.mx", "password_hash": "hash",
    }, 20)

    assert admin_id == 31
    insert, assign, _ = cursor.execute.call_args_list
    assert "'admin', NULL" in insert[0][0]
    assert "must_change_password) VALUES" in insert[0][0]
    assert assign[0][1] == (31, 1, 20)
    assert _audits(cursor)[0][1] == "company.invite_admin"


def test_assign_admin_by_email_only_finds_active_admins(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.assign_admin_by_email(1, "empleado@norte.mx", 20)

    lookup = _queries(cursor)[0]
    assert "email = %s AND role = 'admin' AND is_active" in lookup
    assert not any("company_admins" in q for q in _queries(cursor))


def test_assign_admin_by_email_reactivates_the_assignment(repository, cursor):
    cursor.fetchone.return_value = {"id": 3}

    assert repository.assign_admin_by_email(1, "fer@norte.mx", 20) == 3

    assign = cursor.execute.call_args_list[1][0]
    assert "DO UPDATE SET is_active = TRUE" in assign[0]
    assert assign[1] == (3, 1, 20)


def test_unassign_admin_keeps_the_account(repository, cursor):
    cursor.fetchone.return_value = {"admin_id": 3}

    repository.unassign_admin(1, 3, 20)

    release = _queries(cursor)[0]
    assert "UPDATE company_admins SET is_active = FALSE" in release
    assert not any("UPDATE employees" in q for q in _queries(cursor))
    assert _audits(cursor)[0][1] == "company.unassign_admin"


def test_unassign_somebody_who_is_not_assigned(repository, cursor):
    cursor.fetchone.return_value = None

    with pytest.raises(NotFoundError):
        repository.unassign_admin(1, 99, 20)

    assert _audits(cursor) == []

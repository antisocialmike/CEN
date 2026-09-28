from unittest.mock import MagicMock, patch

import pytest

from server.src.repositories.auth_repository import AuthRepository


@pytest.fixture
def cursor():
    with patch(
        "server.src.repositories.auth_repository.db_cursor"
    ) as mock_db_cursor:
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor


@pytest.fixture
def repository():
    return AuthRepository()


def _queries(cursor) -> list:
    return [str(call[0][0]) for call in cursor.execute.call_args_list]


def test_session_state_compares_the_role_of_the_token(repository, cursor):
    cursor.fetchone.return_value = {"same_role": True, "token_version": 2}

    state = repository.session_state(7, "admin")

    query, params = cursor.execute.call_args[0]
    assert "e.role = %s" in query
    assert "token_version" in query
    assert params == ("admin", 7)
    assert state["token_version"] == 2


def test_session_state_of_a_missing_account(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.session_state(7, "admin") is None


def test_hit_rate_limit_counts_within_the_window(repository, cursor):
    cursor.fetchone.return_value = {"hits": 4, "retry_after": 120}

    window = repository.hit_rate_limit("login", "10.0.0.1", 900)

    assert window == {"hits": 4, "retry_after": 120}
    query, params = cursor.execute.call_args_list[0][0]
    assert "ON CONFLICT (bucket, client_key)" in query
    assert params == ("login", "10.0.0.1", 900, 900, 900)
    # A mitad de ventana no se barre nada.
    assert len(_queries(cursor)) == 1


def test_a_new_window_purges_the_expired_ones(repository, cursor):
    cursor.fetchone.return_value = {"hits": 1, "retry_after": 900}

    repository.hit_rate_limit("login", "10.0.0.1", 900)

    purge, params = cursor.execute.call_args_list[1][0]
    assert purge.startswith("DELETE FROM auth_rate_limits")
    assert params == (900,)


def test_issue_reset_code_voids_the_previous_ones(repository, cursor):
    cursor.fetchone.side_effect = [
        {"id": 7}, {"in_cooldown": 0, "in_last_hour": 2},
    ]

    assert repository.issue_reset_code(7, "hash", 15, 60, 5) is True

    queries = _queries(cursor)
    assert "FOR UPDATE" in queries[0]
    assert queries[2].startswith("UPDATE password_reset_tokens SET used_at")
    assert queries[3].startswith("INSERT INTO password_reset_tokens")
    assert cursor.execute.call_args_list[3][0][1] == (7, "hash", 15)


@pytest.mark.parametrize("recent", [
    {"in_cooldown": 1, "in_last_hour": 1},
    {"in_cooldown": 0, "in_last_hour": 5},
])
def test_issue_reset_code_respects_the_cooldown_and_the_hourly_cap(
    recent, repository, cursor
):
    cursor.fetchone.side_effect = [{"id": 7}, recent]

    assert repository.issue_reset_code(7, "hash", 15, 60, 5) is False
    assert not any(q.startswith("INSERT") for q in _queries(cursor))


def test_issue_reset_code_for_a_missing_account(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.issue_reset_code(7, "hash", 15, 60, 5) is False
    assert len(_queries(cursor)) == 1


def test_claim_reset_attempt_spends_one_before_comparing(repository, cursor):
    cursor.fetchone.return_value = {"id": 30, "code_hash": "hash"}

    claimed = repository.claim_reset_attempt(7, 5)

    query, params = cursor.execute.call_args[0]
    assert "attempts = attempts + 1" in query
    assert "employee_id = %s" in query
    assert "attempts < %s" in query
    assert params == (7, 5)
    assert claimed == {"id": 30, "code_hash": "hash"}


def test_claim_reset_attempt_without_a_live_code(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.claim_reset_attempt(7, 5) is None


def test_reset_password_with_code_closes_the_sessions(repository, cursor):
    cursor.fetchone.return_value = {"id": 30}

    assert repository.reset_password_with_code(30, 7, "nuevo_hash") is True

    spend, update = cursor.execute.call_args_list
    assert spend[0][1] == (30, 7)
    assert "used_at IS NULL" in spend[0][0]
    assert "token_version = token_version + 1" in update[0][0]
    assert "locked_until = NULL" in update[0][0]
    assert update[0][1] == ("nuevo_hash", 7)


def test_reset_password_with_a_code_already_spent(repository, cursor):
    cursor.fetchone.return_value = None

    assert repository.reset_password_with_code(30, 7, "nuevo_hash") is False
    assert len(_queries(cursor)) == 1

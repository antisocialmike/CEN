from unittest.mock import MagicMock, patch

import pytest

from server.src.config import database


@pytest.fixture(autouse=True)
def reset_pool():
    database._pool = None
    yield
    database._pool = None


@pytest.fixture
def pool():
    with patch.object(database, "ThreadedConnectionPool") as factory:
        factory.return_value = MagicMock()
        yield factory


def test_connection_kwargs_prefers_database_url():
    with patch.object(database, "DATABASE_URL", "postgres://user@host/db"):
        assert database._connection_kwargs() == {
            "dsn": "postgres://user@host/db"
        }


def test_connection_kwargs_falls_back_to_discrete_variables():
    with patch.object(database, "DATABASE_URL", ""):
        assert database._connection_kwargs()["dbname"] == database.DB_NAME


def test_get_pool_is_created_once(pool):
    assert database.get_pool() is database.get_pool()
    pool.assert_called_once()


def test_db_cursor_commits_and_returns_the_connection(pool):
    connection = pool.return_value.getconn.return_value

    with database.db_cursor() as cursor:
        assert cursor is connection.cursor.return_value.__enter__.return_value

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    pool.return_value.putconn.assert_called_once_with(connection)


def test_db_cursor_rolls_back_on_error(pool):
    connection = pool.return_value.getconn.return_value

    with pytest.raises(RuntimeError):
        with database.db_cursor():
            raise RuntimeError("fallo")

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    pool.return_value.putconn.assert_called_once_with(connection)


def test_close_pool_releases_every_connection(pool):
    database.get_pool()

    database.close_pool()

    pool.return_value.closeall.assert_called_once()
    assert database._pool is None


def test_close_pool_without_pool_is_a_no_op():
    database.close_pool()

    assert database._pool is None

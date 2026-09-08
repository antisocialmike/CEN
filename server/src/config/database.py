import threading
from contextlib import contextmanager
from typing import Iterator, Optional

from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from .settings import (
    DATABASE_URL,
    DB_CONNECT_TIMEOUT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_POOL_MAX,
    DB_POOL_MIN,
    DB_PORT,
    DB_USER,
)

_pool: Optional[ThreadedConnectionPool] = None
_pool_lock = threading.Lock()


def _connection_kwargs() -> dict:
    if DATABASE_URL:
        return {"dsn": DATABASE_URL}
    return {
        "host": DB_HOST,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT,
    }


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = ThreadedConnectionPool(
                    DB_POOL_MIN,
                    DB_POOL_MAX,
                    cursor_factory=RealDictCursor,
                    connect_timeout=DB_CONNECT_TIMEOUT,
                    **_connection_kwargs(),
                )
    return _pool


def close_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.closeall()
            _pool = None


@contextmanager
def db_cursor() -> Iterator:
    pool = get_pool()
    connection = pool.getconn()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        pool.putconn(connection)

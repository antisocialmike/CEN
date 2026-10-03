from typing import Optional

from ..config.database import db_cursor

SELECT_SESSION_STATE = (
    "SELECT (e.role = %s) AS same_role, e.is_active, e.must_change_password, "
    "e.token_version, CASE WHEN e.role = 'employee' THEN EXISTS ("
    "SELECT 1 FROM employments m JOIN companies c ON c.id = m.company_id "
    "WHERE m.employee_id = e.id AND m.is_active AND c.is_active) "
    "END AS company_is_active "
    "FROM employees e WHERE e.id = %s;"
)

HIT_RATE_LIMIT = (
    "INSERT INTO auth_rate_limits AS r (bucket, client_key) VALUES (%s, %s) "
    "ON CONFLICT (bucket, client_key) DO UPDATE SET "
    "hits = CASE WHEN r.window_start > NOW() - make_interval(secs => %s) "
    "THEN r.hits + 1 ELSE 1 END, "
    "window_start = CASE WHEN r.window_start > NOW() - make_interval(secs => %s) "
    "THEN r.window_start ELSE NOW() END "
    "RETURNING hits, GREATEST(1, CEIL(EXTRACT(EPOCH FROM "
    "window_start + make_interval(secs => %s) - NOW())))::int AS retry_after;"
)
PURGE_RATE_LIMITS = (
    "DELETE FROM auth_rate_limits "
    "WHERE window_start <= NOW() - make_interval(secs => %s);"
)

LOCK_EMPLOYEE = "SELECT id FROM employees WHERE id = %s FOR UPDATE;"
COUNT_RECENT_RESET_CODES = (
    "SELECT COUNT(*) FILTER (WHERE created_at > NOW() - make_interval(secs => %s)) "
    "AS in_cooldown, COUNT(*) AS in_last_hour FROM password_reset_tokens "
    "WHERE employee_id = %s AND created_at > NOW() - INTERVAL '1 hour';"
)
VOID_ACTIVE_RESET_CODES = (
    "UPDATE password_reset_tokens SET used_at = NOW() "
    "WHERE employee_id = %s AND used_at IS NULL;"
)
INSERT_RESET_CODE = (
    "INSERT INTO password_reset_tokens (employee_id, code_hash, expires_at) "
    "VALUES (%s, %s, NOW() + make_interval(mins => %s));"
)
CLAIM_RESET_ATTEMPT = (
    "UPDATE password_reset_tokens SET attempts = attempts + 1 "
    "WHERE id = (SELECT id FROM password_reset_tokens WHERE employee_id = %s "
    "AND used_at IS NULL AND expires_at > NOW() "
    "ORDER BY created_at DESC LIMIT 1) "
    "AND used_at IS NULL AND attempts < %s "
    "RETURNING id, code_hash;"
)
SPEND_RESET_CODE = (
    "UPDATE password_reset_tokens SET used_at = NOW() "
    "WHERE id = %s AND employee_id = %s AND used_at IS NULL "
    "AND expires_at > NOW() RETURNING id;"
)
RESET_PASSWORD_WITH_CODE = (
    "UPDATE employees SET password_hash = %s, must_change_password = FALSE, "
    "failed_login_attempts = 0, locked_until = NULL, "
    "token_version = token_version + 1 WHERE id = %s;"
)


class AuthRepository:
    def session_state(self, employee_id: int, role: str) -> Optional[dict]:
        with db_cursor() as cursor:
            cursor.execute(SELECT_SESSION_STATE, (role, employee_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def hit_rate_limit(
        self, bucket: str, client_key: str, window_seconds: int
    ) -> dict:
        with db_cursor() as cursor:
            cursor.execute(HIT_RATE_LIMIT, (
                bucket, client_key, window_seconds, window_seconds, window_seconds,
            ))
            row = dict(cursor.fetchone())
            if row["hits"] == 1:
                cursor.execute(PURGE_RATE_LIMITS, (window_seconds,))
            return row

    def issue_reset_code(
        self, employee_id: int, code_hash: str, expire_minutes: int,
        cooldown_seconds: int, hourly_max: int,
    ) -> bool:
        with db_cursor() as cursor:
            cursor.execute(LOCK_EMPLOYEE, (employee_id,))
            if cursor.fetchone() is None:
                return False

            cursor.execute(
                COUNT_RECENT_RESET_CODES, (cooldown_seconds, employee_id)
            )
            recent = dict(cursor.fetchone())
            if recent["in_cooldown"] > 0 or recent["in_last_hour"] >= hourly_max:
                return False

            cursor.execute(VOID_ACTIVE_RESET_CODES, (employee_id,))
            cursor.execute(
                INSERT_RESET_CODE, (employee_id, code_hash, expire_minutes)
            )
            return True

    def claim_reset_attempt(
        self, employee_id: int, max_attempts: int
    ) -> Optional[dict]:
        with db_cursor() as cursor:
            cursor.execute(CLAIM_RESET_ATTEMPT, (employee_id, max_attempts))
            row = cursor.fetchone()
            return dict(row) if row else None

    def reset_password_with_code(
        self, code_id: int, employee_id: int, password_hash: str
    ) -> bool:
        with db_cursor() as cursor:
            cursor.execute(SPEND_RESET_CODE, (code_id, employee_id))
            if cursor.fetchone() is None:
                return False
            cursor.execute(RESET_PASSWORD_WITH_CODE, (password_hash, employee_id))
            return True


auth_repository = AuthRepository()

import os
from dotenv import load_dotenv

load_dotenv()


def _env_list(name: str, default: str) -> list:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cen_payroll_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cen-secret-payroll-key-for-jwt-tokens")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "8"))

ALLOWED_ORIGINS = _env_list("ALLOWED_ORIGINS", "http://localhost:5173")

LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
TEMPORARY_PASSWORD_LENGTH = int(os.getenv("TEMPORARY_PASSWORD_LENGTH", "12"))

ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@cen.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")
ADMIN_BASE_SALARY = float(os.getenv("ADMIN_BASE_SALARY", "20000"))

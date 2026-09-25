import logging
import threading

from .config.database import ping
from .config.settings import (
    ADMIN_BASE_SALARY,
    ADMIN_EMAIL,
    ADMIN_NAME,
    ADMIN_PASSWORD,
    BOOTSTRAP_MIN_PASSWORD_LENGTH,
    OWNER_EMAIL,
    OWNER_NAME,
    OWNER_PASSWORD,
    SUPERADMIN_EMAIL,
    SUPERADMIN_NAME,
    SUPERADMIN_PASSWORD,
)
from .middlewares.auth_middleware import hash_password
from .repositories.company_repository import company_repository
from .repositories.payroll_repository import payroll_repository

logger = logging.getLogger(__name__)

_ready = False
_ready_lock = threading.Lock()


def bootstrap_database() -> bool:
    global _ready
    with _ready_lock:
        try:
            applied = payroll_repository.run_migrations()
            if applied:
                logger.info("Migraciones aplicadas: %s", ", ".join(applied))
            _ensure_admin_account()
            _ensure_superadmin_account()
            _ensure_owner_account()
            _ready = True
            return True
        except Exception:
            logger.exception(
                "No se pudo preparar la base de datos. "
                "La API arranca igualmente y respondera 503 hasta que este disponible."
            )
            return False


def database_ready() -> bool:
    # Si la base no estaba lista al arrancar, las migraciones y las cuentas
    # iniciales quedaron pendientes: el healthcheck las reintenta hasta lograrlo.
    if not _ready:
        return bootstrap_database()
    try:
        ping()
        return True
    except Exception as error:
        logger.warning("La base de datos no responde: %s", error)
        return False


def _ensure_admin_account() -> None:
    if payroll_repository.get_employee_by_email(ADMIN_EMAIL) is not None:
        return

    payroll_repository.create_employee({
        "name": ADMIN_NAME,
        "email": ADMIN_EMAIL,
        "role": "admin",
        "base_salary": ADMIN_BASE_SALARY,
        "password_hash": hash_password(ADMIN_PASSWORD),
    }, payroll_repository.first_company_id())
    logger.info("Cuenta administradora creada para %s", ADMIN_EMAIL)


def _needs_account(variable: str, email: str, password: str, role: str) -> bool:
    """Dice si hay que crear la cuenta configurada en `variable`_EMAIL/_PASSWORD."""
    if not email or not password:
        return False

    if len(password) < BOOTSTRAP_MIN_PASSWORD_LENGTH:
        logger.error(
            "%s_PASSWORD debe tener al menos %s caracteres; no se creo la cuenta.",
            variable, BOOTSTRAP_MIN_PASSWORD_LENGTH,
        )
        return False

    existing = payroll_repository.get_employee_by_email(email)
    if existing is not None:
        if existing.get("role") != role:
            logger.warning(
                "%s ya existe con rol %s; no se convirtio en %s.",
                email, existing.get("role"), role,
            )
        return False
    return True


def _ensure_superadmin_account() -> None:
    if not _needs_account(
        "SUPERADMIN", SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, "superadmin"
    ):
        return

    payroll_repository.create_employee({
        "name": SUPERADMIN_NAME,
        "email": SUPERADMIN_EMAIL,
        "role": "superadmin",
        "base_salary": None,
        "password_hash": hash_password(SUPERADMIN_PASSWORD),
    })
    logger.info("Cuenta de superadmin creada para %s", SUPERADMIN_EMAIL)


def _ensure_owner_account() -> None:
    # Un dueño para probar el tablero sin pasar por el alta del superadmin.
    # Queda como dueño de la primera empresa, la que crea la migracion 009.
    if not _needs_account("OWNER", OWNER_EMAIL, OWNER_PASSWORD, "owner"):
        return

    owner_id = payroll_repository.create_employee({
        "name": OWNER_NAME,
        "email": OWNER_EMAIL,
        "role": "owner",
        "base_salary": None,
        "password_hash": hash_password(OWNER_PASSWORD),
    })
    company_id = payroll_repository.first_company_id()
    if company_id is not None:
        company_repository.link_owner(owner_id, company_id)
    logger.info("Cuenta de dueño creada para %s", OWNER_EMAIL)

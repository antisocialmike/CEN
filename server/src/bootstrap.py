import logging

from .config.settings import (
    ADMIN_BASE_SALARY,
    ADMIN_EMAIL,
    ADMIN_NAME,
    ADMIN_PASSWORD,
)
from .middlewares.auth_middleware import hash_password
from .repositories.payroll_repository import payroll_repository

logger = logging.getLogger(__name__)


def bootstrap_database() -> bool:
    try:
        applied = payroll_repository.run_migrations()
        if applied:
            logger.info("Migraciones aplicadas: %s", ", ".join(applied))
        _ensure_admin_account()
        return True
    except Exception:
        logger.exception(
            "No se pudo preparar la base de datos. "
            "La API arranca igualmente y respondera 503 hasta que este disponible."
        )
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
    })
    logger.info("Cuenta administradora creada para %s", ADMIN_EMAIL)

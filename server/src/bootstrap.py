import logging

from .config.settings import (
    ADMIN_BASE_SALARY,
    ADMIN_EMAIL,
    ADMIN_NAME,
    ADMIN_PASSWORD,
    SUPERADMIN_EMAIL,
    SUPERADMIN_MIN_PASSWORD_LENGTH,
    SUPERADMIN_NAME,
    SUPERADMIN_PASSWORD,
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
        _ensure_superadmin_account()
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
    }, payroll_repository.first_company_id())
    logger.info("Cuenta administradora creada para %s", ADMIN_EMAIL)


def _ensure_superadmin_account() -> None:
    if not SUPERADMIN_EMAIL or not SUPERADMIN_PASSWORD:
        return

    if len(SUPERADMIN_PASSWORD) < SUPERADMIN_MIN_PASSWORD_LENGTH:
        logger.error(
            "SUPERADMIN_PASSWORD debe tener al menos %s caracteres; "
            "no se creo la cuenta de superadmin.",
            SUPERADMIN_MIN_PASSWORD_LENGTH,
        )
        return

    existing = payroll_repository.get_employee_by_email(SUPERADMIN_EMAIL)
    if existing is not None:
        if existing.get("role") != "superadmin":
            logger.warning(
                "%s ya existe con rol %s; no se convirtio en superadmin.",
                SUPERADMIN_EMAIL, existing.get("role"),
            )
        return

    payroll_repository.create_employee({
        "name": SUPERADMIN_NAME,
        "email": SUPERADMIN_EMAIL,
        "role": "superadmin",
        "base_salary": None,
        "password_hash": hash_password(SUPERADMIN_PASSWORD),
    })
    logger.info("Cuenta de superadmin creada para %s", SUPERADMIN_EMAIL)

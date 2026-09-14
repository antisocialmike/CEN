import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config.settings import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_USE_TLS,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
)

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


def send_password_reset_email(email: str, name: str, code: str) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error(
            "No se envió el código a %s: faltan SMTP_USER y SMTP_PASSWORD.", email
        )
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = email
        msg["Subject"] = "Código para restablecer tu contraseña - CEN Payroll"

        body = f"""Hola {name},

Recibimos una solicitud para restablecer tu contraseña en CEN Payroll.

Tu código de verificación es:

{code}

Este código expira en {PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos.

Si no solicitaste esto, ignora este correo.

—
CEN Payroll"""

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(
            SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS
        ) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception:
        logger.exception("Falló el envío del código a %s", email)
        return False

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_USE_TLS,
)


def send_password_reset_email(email: str, name: str, code: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = email
        msg["Subject"] = "Código para restablecer tu contraseña - CEN Payroll"

        body = f"""Hola {name},

Recibimos una solicitud para restablecer tu contraseña en CEN Payroll.

Tu código de verificación es:

{code}

Este código expira en 15 minutos.

Si no solicitaste esto, ignora este correo.

—
CEN Payroll"""

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

"""Email services module.

Provides SMTP configurations and asynchronous email dispatch services
using fastapi_mail, primarily for registration email verification.
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pathlib import Path
from pydantic import EmailStr
from src.conf.config import config
from src.services.auth import create_email_token

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    USE_CREDENTIALS=config.USE_CREDENTIALS,
    VALIDATE_CERTS=config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str):
    """Generates an email confirmation token and dispatches a verification email.

    Creates a short-lived JWT token containing the recipient's email address,
    populates the HTML template body with verification parameters, and sends
    it via FastMail. Catches and logs SMTP connection errors.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The username of the user receiving the verification email.
        host (str): The base host URL used to construct the verification link
            (e.g., http://localhost:8000/).

    Raises:
        ConnectionErrors: Logged to the standard output if there is an issue
            connecting to the SMTP server.
    """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)

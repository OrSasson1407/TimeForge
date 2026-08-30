"""Real email delivery for registration verification codes, over plain
SMTP (stdlib `smtplib` — no extra dependency for one transactional email).

When no SMTP credentials are configured (`smtp_username`/`smtp_password`
unset — the default for local dev and every test run), `SmtpEmailSender`
does not attempt a network connection at all: it logs the code at WARNING
level instead, which is what local development and the test suite rely on
(docs/07-CODE_STANDARDS.md #22, the same "sanctioned alternative to a live
dependency" pattern used for the Firestore fakes). Configuring real
credentials in `backend/.env` is what switches it over to actually sending
mail — see docs/06-TECH_STACK.md's registration section.
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    def send_verification_code(self, *, to_email: str, code: str, ttl_minutes: int) -> None: ...


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_verification_code(self, *, to_email: str, code: str, ttl_minutes: int) -> None:
        settings = self._settings
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning(
                "SMTP not configured — not sending a real email. "
                "Verification code for %s is %s (valid %d minutes).",
                to_email,
                code,
                ttl_minutes,
            )
            return

        from_email = settings.smtp_from_email or settings.smtp_username
        message = EmailMessage()
        message["Subject"] = "Your TimeForge verification code"
        message["From"] = f"{settings.smtp_from_name} <{from_email}>"
        message["To"] = to_email
        message.set_content(
            "Welcome to TimeForge!\n\n"
            f"Your verification code is: {code}\n\n"
            f"This code expires in {ttl_minutes} minutes. If you didn't request "
            "this, you can safely ignore this email."
        )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        logger.info("Sent verification email to %s", to_email)

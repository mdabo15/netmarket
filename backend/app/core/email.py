"""Outbound email — SMTP only, no external provider SDK.

In dev/docker-compose, SMTP_HOST/PORT default to the mailpit service (see
docker-compose.yml): it accepts anything, sends nothing out, and shows
received mail at http://localhost:8025 — no auth, no TLS.

Set SMTP_USERNAME/SMTP_PASSWORD in .env to go through a real provider instead
(e.g. Gmail: smtp.gmail.com:587, an app-specific password — Gmail requires
2-Step Verification enabled first and won't accept the account's normal
password over SMTP). Their presence is what switches STARTTLS + login on.
"""

import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()


def _send_sync(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_username and settings.smtp_password:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_email(to: str, subject: str, body: str) -> None:
    # smtplib is blocking; keep it off the event loop.
    await asyncio.to_thread(_send_sync, to, subject, body)

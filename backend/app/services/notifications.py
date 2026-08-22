"""Notification dispatch (spec section 7).

Phase 1 implements in-app (DB row, always) + Email (SMTP, if configured).
The Alert.channel field and this dispatcher are the extension point for
WhatsApp/Telegram/Push/SMS - add a new `send_via_<channel>` function and
register it in CHANNEL_SENDERS, no other code needs to change.
"""

from collections.abc import Awaitable, Callable

import aiosmtplib
from email.message import EmailMessage

from app.config import get_settings
from app.core.logging import log
from app.models.alert import Alert
from app.models.enums import AlertChannel

settings = get_settings()


async def send_via_email(alert: Alert, to_email: str) -> tuple[bool, str | None]:
    if not settings.SMTP_HOST:
        return False, "SMTP not configured (set SMTP_HOST/SMTP_USER/SMTP_PASSWORD in .env)"
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = alert.title
    message.set_content(alert.body or "")
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_USE_TLS,
        )
        return True, None
    except Exception as exc:  # noqa: BLE001 - report to caller, never crash the caller
        log.error("email_send_failed", error=str(exc))
        return False, str(exc)


async def send_via_whatsapp(alert: Alert, to: str) -> tuple[bool, str | None]:
    return False, "WhatsApp channel not yet configured - connect a WhatsApp Business API provider via env vars"


async def send_via_telegram(alert: Alert, to: str) -> tuple[bool, str | None]:
    return False, "Telegram channel not yet configured - set TELEGRAM_BOT_TOKEN"


async def send_via_push(alert: Alert, to: str) -> tuple[bool, str | None]:
    return False, "Push channel not yet configured - connect a push provider (e.g. FCM/APNs)"


async def send_via_sms(alert: Alert, to: str) -> tuple[bool, str | None]:
    return False, "SMS channel not yet configured - connect an SMS provider"


CHANNEL_SENDERS: dict[AlertChannel, Callable[[Alert, str], Awaitable[tuple[bool, str | None]]]] = {
    AlertChannel.EMAIL: send_via_email,
    AlertChannel.WHATSAPP: send_via_whatsapp,
    AlertChannel.TELEGRAM: send_via_telegram,
    AlertChannel.PUSH: send_via_push,
    AlertChannel.SMS: send_via_sms,
}

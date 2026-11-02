"""
Sends alert emails via SMTP. No-ops gracefully (logs a warning instead
of raising) if SMTP credentials aren't configured, so a missing email
setup never takes down the monitoring pipeline.
"""

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def send_alert_email(
    patient_name: str,
    alert_type: str,
    message: str,
    screenshot_path: Optional[str] = None,
    to_email: Optional[str] = None,
) -> bool:
    """
    Sends to `to_email` if given (e.g. a specific assigned caregiver's
    address), otherwise falls back to the global
    settings.ALERT_RECIPIENT_EMAIL. No-ops (returns False, logs a
    warning) if SMTP isn't configured or there's no recipient to send
    to — never fakes success.
    """
    recipient = to_email or settings.ALERT_RECIPIENT_EMAIL
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or not recipient:
        logger.warning("SMTP not configured or no recipient — skipping alert email dispatch.")
        return False

    email = EmailMessage()
    email["Subject"] = f"[ALERT] {alert_type.upper()} detected — {patient_name}"
    email["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USERNAME}>"
    email["To"] = recipient
    email.set_content(
        f"Patient: {patient_name}\n"
        f"Alert type: {alert_type}\n"
        f"Details: {message}\n\n"
        f"Please check the monitoring dashboard immediately."
    )

    if screenshot_path:
        local_path = Path(settings.UPLOAD_DIR) / Path(screenshot_path).relative_to("/uploads") \
            if screenshot_path.startswith("/uploads") else Path(screenshot_path)
        if local_path.exists():
            with open(local_path, "rb") as f:
                email.add_attachment(f.read(), maintype="image", subtype="jpeg", filename=local_path.name)

    try:
        # Explicit timeout: without one, smtplib blocks on the OS's default
        # TCP timeout (can be 60s+) if the SMTP host is unreachable/blocked
        # by a firewall — which would otherwise stall the whole alert
        # pipeline (fall/inactivity detection) behind a slow network call.
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(email)
        logger.info("Alert email sent for patient=%s type=%s", patient_name, alert_type)
        return True
    except Exception as exc:
        logger.error("Failed to send alert email: %s", exc)
        return False

"""
alert_sender.py — Outbound alert delivery for Concert Tracker.

Channels (in priority order):
  1. Email via SendGrid REST API     (SENDGRID_API_KEY env var)
  2. Email via SMTP fallback          (SMTP_HOST / SMTP_USER / SMTP_PASSWORD)
  3. SMS via Twilio REST API          (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN /
                                       TWILIO_FROM env vars)

RED alerts:  email + SMS
YELLOW alerts: email only

Rate-limiting: identical alert_type suppressed for 30 minutes to avoid floods.

Environment variables:
  SENDGRID_API_KEY        SendGrid API key (preferred email provider)
  SMTP_HOST               SMTP server hostname (fallback)
  SMTP_USER               SMTP login
  SMTP_PASSWORD           SMTP password
  TWILIO_ACCOUNT_SID      Twilio account SID (SMS)
  TWILIO_AUTH_TOKEN       Twilio auth token
  TWILIO_FROM             Twilio from number (E.164, e.g. +15005550006)
  ALERT_EMAIL_TO          Override recipient email (default: surajgohill@yahoo.com)
  ALERT_SMS_TO            Override recipient SMS number (default: +13104309614)
"""
from __future__ import annotations

import logging
import os
import smtplib
import socket
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_ALERT_EMAIL_TO = "surajgohill@yahoo.com"
_ALERT_SMS_TO = "+13104309614"

# Rate-limit: track last send time per alert_type
_last_sent: dict[str, datetime] = {}
_SUPPRESS_WINDOW = timedelta(minutes=30)


def _is_suppressed(alert_type: str) -> bool:
    last = _last_sent.get(alert_type)
    if last and (datetime.utcnow() - last) < _SUPPRESS_WINDOW:
        return True
    return False


def _mark_sent(alert_type: str) -> None:
    _last_sent[alert_type] = datetime.utcnow()


async def _send_email_sendgrid(subject: str, body: str) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        return False
    to_addr = os.environ.get("ALERT_EMAIL_TO", _ALERT_EMAIL_TO)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_addr}]}],
                    "from": {"email": "alerts@concert-tracker.app", "name": "Concert Tracker"},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
            )
        if r.status_code in (200, 202):
            logger.info("ALERT_EMAIL: sent via SendGrid → %s | subject=%s", to_addr, subject)
            return True
        logger.warning("ALERT_EMAIL: SendGrid %d — %s", r.status_code, r.text[:200])
    except Exception as exc:
        logger.error("ALERT_EMAIL: SendGrid exception — %s", exc)
    return False


def _send_email_smtp(subject: str, body: str) -> bool:
    host = os.environ.get("SMTP_HOST", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    if not (host and user and password):
        return False
    to_addr = os.environ.get("ALERT_EMAIL_TO", _ALERT_EMAIL_TO)
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_addr
        port = int(os.environ.get("SMTP_PORT", "465"))
        if port == 587:
            with smtplib.SMTP(host, port, timeout=10) as srv:
                srv.ehlo()
                srv.starttls()
                srv.login(user, password)
                srv.send_message(msg)
        else:
            with smtplib.SMTP_SSL(host, port, timeout=10) as srv:
                srv.login(user, password)
                srv.send_message(msg)
        logger.info("ALERT_EMAIL: sent via SMTP → %s | subject=%s", to_addr, subject)
        return True
    except Exception as exc:
        logger.error("ALERT_EMAIL: SMTP exception — %s", exc)
    return False


async def _send_sms_twilio(message: str) -> bool:
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_num = os.environ.get("TWILIO_FROM", "")
    if not (sid and token and from_num):
        return False
    to_num = os.environ.get("ALERT_SMS_TO", _ALERT_SMS_TO)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                auth=(sid, token),
                data={"From": from_num, "To": to_num, "Body": message[:1600]},
            )
        if r.status_code == 201:
            logger.info("ALERT_SMS: sent via Twilio → %s", to_num)
            return True
        logger.warning("ALERT_SMS: Twilio %d — %s", r.status_code, r.text[:200])
    except Exception as exc:
        logger.error("ALERT_SMS: Twilio exception — %s", exc)
    return False


async def fire_alert(
    alert_type: str,
    severity: str,
    message: str,
    details: Optional[dict] = None,
    force: bool = False,
) -> dict:
    """
    Fire an alert via all configured channels.

    severity=RED  → email + SMS
    severity=YELLOW → email only

    Rate-limited: same alert_type suppressed for 30 min unless force=True.
    Returns dict with delivery results.
    """
    if not force and _is_suppressed(alert_type):
        logger.debug("ALERT: suppressed (rate-limit) type=%s", alert_type)
        return {"suppressed": True, "alert_type": alert_type}

    hostname = socket.gethostname()
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    body_lines = [
        f"Concert Tracker — {severity} ALERT",
        f"Type: {alert_type}",
        f"Time: {ts}",
        f"Host: {hostname}",
        "",
        message,
    ]
    if details:
        body_lines += ["", "Details:"]
        body_lines += [f"  {k}: {v}" for k, v in details.items()]
    body_lines += [
        "",
        "---",
        "Remediation: check Railway logs and /api/system/reliability",
    ]
    body = "\n".join(body_lines)
    subject = f"[Concert Tracker] {severity}: {alert_type}"

    results: dict = {"email": False, "sms": False}

    # Email: SendGrid first, SMTP fallback
    sent_email = await _send_email_sendgrid(subject, body)
    if not sent_email:
        sent_email = _send_email_smtp(subject, body)
    results["email"] = sent_email

    if not sent_email:
        logger.warning(
            "ALERT: email delivery not configured for %s — "
            "set SENDGRID_API_KEY or SMTP_HOST/SMTP_USER/SMTP_PASSWORD",
            alert_type,
        )

    # SMS: RED severity only
    if severity == "RED":
        sms_body = f"[{severity}] {alert_type}: {message[:100]}"
        results["sms"] = await _send_sms_twilio(sms_body)
        if not results["sms"]:
            logger.warning(
                "ALERT: SMS delivery not configured — "
                "set TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM"
            )

    _mark_sent(alert_type)
    logger.info(
        "ALERT fired: type=%s severity=%s email=%s sms=%s",
        alert_type, severity, results["email"], results.get("sms"),
    )
    return results


def alert_delivery_status() -> dict:
    """Report which alert channels are configured (no secrets exposed)."""
    return {
        "email": {
            "sendgrid": bool(os.environ.get("SENDGRID_API_KEY")),
            "smtp": bool(
                os.environ.get("SMTP_HOST")
                and os.environ.get("SMTP_USER")
                and os.environ.get("SMTP_PASSWORD")
            ),
            "recipient": os.environ.get("ALERT_EMAIL_TO", _ALERT_EMAIL_TO),
        },
        "sms": {
            "twilio": bool(
                os.environ.get("TWILIO_ACCOUNT_SID")
                and os.environ.get("TWILIO_AUTH_TOKEN")
                and os.environ.get("TWILIO_FROM")
            ),
            "recipient": os.environ.get("ALERT_SMS_TO", _ALERT_SMS_TO),
        },
    }

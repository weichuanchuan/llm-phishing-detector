from __future__ import annotations

from pathlib import Path

# Base paths reused across the Python reproduction of MailCheck
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
PUBLIC_DIR = DATA_DIR / "public"
TMP_DIR = DATA_DIR / "tmp"
REPORT_DIR = TMP_DIR / "reports"
FEEDBACK_LOG = TMP_DIR / "feedback.log"
MAIL_DIR = DATA_DIR / "mailserver" / "start"
STATIC_DIR = ROOT_DIR / "app" / "static"

# Analysis configuration
HTTP_TIMEOUT = 8
MAX_REDIRECTS = 5
RATE_LIMIT_PER_HOUR = 5
SAFE_ATTACHMENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
}

SUSPICIOUS_PHRASES = (
    "password reset",
    "verify your account",
    "urgent action required",
    "confirm your identity",
    "banking",
    "invoice",
    "wire transfer",
    "gift card",
)

URL_RED_FLAGS = (
    "login",
    "update",
    "verify",
    "secure",
    "account",
)

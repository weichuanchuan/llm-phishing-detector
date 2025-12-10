from __future__ import annotations

import email
import re
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .config import MAIL_DIR


class EmlEnvelope:
    """Represents a parsed EML file with helper utilities."""

    def __init__(self, message: EmailMessage, source_path: Optional[Path] = None):
        self.message = message
        self.source_path = source_path

    @classmethod
    def from_bytes(cls, raw_bytes: bytes, source_path: Optional[Path] = None) -> "EmlEnvelope":
        message = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        return cls(message, source_path=source_path)

    @classmethod
    def from_path(cls, path: Path) -> "EmlEnvelope":
        raw_bytes = path.read_bytes()
        return cls.from_bytes(raw_bytes, source_path=path)

    @property
    def subject(self) -> Optional[str]:
        return self.message.get("Subject")

    @property
    def sender(self) -> Optional[str]:
        return self.message.get("From")

    @property
    def reply_to(self) -> Optional[str]:
        return self.message.get("Reply-To")

    @property
    def to_addresses(self) -> List[str]:
        raw = self.message.get_all("To", [])
        return [addr for value in raw for addr in value.split(",")]

    @property
    def date(self) -> Optional[str]:
        value = self.message.get("Date")
        return value if value else None

    def parsed_date(self):
        raw = self.date
        return parsedate_to_datetime(raw) if raw else None

    def body_text(self) -> str:
        if self.message.is_multipart():
            for part in self.message.walk():
                if part.get_content_type() == "text/plain" and part.get_content() is not None:
                    return part.get_content()
        content = self.message.get_content()
        return content if content is not None else ""

    def attachments(self) -> Iterable[EmailMessage]:
        for part in self.message.walk():
            if part.get_content_disposition() == "attachment":
                yield part

    def nested_eml_parts(self) -> List["EmlEnvelope"]:
        nested: List[EmlEnvelope] = []
        for part in self.attachments():
            filename = part.get_filename("") or ""
            if filename.lower().endswith(".eml"):
                raw = part.get_payload(decode=True)
                if raw:
                    nested.append(EmlEnvelope.from_bytes(raw))
        return nested

    def header_pairs(self) -> List[tuple[str, str]]:
        return [(k, str(v)) for k, v in self.message.items()]

    def spoofing_detected(self) -> bool:
        # Very light heuristic: flag if Reply-To domain mismatches From domain or Return-Path
        from_domain = _domain_from_address(self.sender)
        reply_domain = _domain_from_address(self.reply_to)
        return_path = _domain_from_address(self.message.get("Return-Path"))
        return bool(
            (from_domain and reply_domain and from_domain != reply_domain)
            or (from_domain and return_path and from_domain != return_path)
        )

    def extract_urls(self) -> List[str]:
        pattern = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
        return [match.group(0).strip().rstrip(".,)") for match in pattern.finditer(self.body_text())]


def ensure_mail_directories() -> None:
    MAIL_DIR.mkdir(parents=True, exist_ok=True)


def _domain_from_address(address: Optional[str]) -> Optional[str]:
    if not address or "@" not in address:
        return None
    return address.split("@")[1].strip().lower()

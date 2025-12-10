from __future__ import annotations

import asyncio
import json
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

import dns.resolver
import tldextract
from rich.console import Console

from .config import SAFE_ATTACHMENT_TYPES, SUSPICIOUS_PHRASES
from .eml_utils import EmlEnvelope
from .models import (
    AnalysisResult,
    AttachmentFinding,
    EnvelopeMetadata,
    HeaderFinding,
    UrlFinding,
    UrlScanResult,
)
from .url_scanner import UrlScan, crawl_urls

console = Console(width=100)


def load_whitelist(path) -> Set[str]:
    from pathlib import Path

    path = Path(path)
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as handle:
        return {line.strip().lower() for line in handle if line.strip() and not line.startswith("#")}


def evaluate_headers(envelope: EmlEnvelope) -> List[HeaderFinding]:
    findings: List[HeaderFinding] = []
    auth_results = envelope.message.get("Authentication-Results", "")
    if auth_results and "fail" in auth_results.lower():
        findings.append(
            HeaderFinding(
                header="Authentication-Results",
                detail="Authentication results include failures (SPF/DKIM/DMARC).",
            )
        )

    spf_header = envelope.message.get("Received-SPF", "")
    if spf_header and "fail" in spf_header.lower():
        findings.append(
            HeaderFinding(
                header="Received-SPF",
                detail="SPF validation reported a failure.",
            )
        )

    if envelope.spoofing_detected():
        findings.append(
            HeaderFinding(
                header="Reply-To",
                detail="Reply-To domain differs from From/Return-Path and may indicate spoofing.",
            )
        )
    return findings


def analyze_urls(urls: Iterable[str], whitelist: Set[str]) -> List[UrlFinding]:
    findings: List[UrlFinding] = []
    for url in urls:
        domain = normalise_domain(url)
        if domain and domain in whitelist:
            continue

        extracted = tldextract.extract(url)
        reasons: List[str] = []
        if extracted.suffix == "":
            reasons.append("URL is missing a valid public suffix.")
        if any(flag in url.lower() for flag in ("@", "..")):
            reasons.append("URL contains uncommon characters.")
        if any(flag in url.lower() for flag in ("%", "+")):
            reasons.append("URL includes encoded characters typical for phishing lures.")
        if url.lower().startswith("http://"):
            reasons.append("Uses insecure HTTP instead of HTTPS.")

        if reasons:
            findings.append(UrlFinding(url=url, reason=" ".join(reasons)))
    return findings


def analyze_attachments(envelope: EmlEnvelope) -> List[AttachmentFinding]:
    findings: List[AttachmentFinding] = []
    for part in envelope.attachments():
        filename = part.get_filename() or "unnamed"
        mimetype = part.get_content_type()
        if mimetype not in SAFE_ATTACHMENT_TYPES:
            findings.append(
                AttachmentFinding(
                    filename=filename,
                    detail=f"Attachment type {mimetype} is uncommon in trusted emails.",
                )
            )
    return findings


def evaluate_keywords(text: str) -> List[str]:
    lower_text = text.lower()
    return [phrase for phrase in SUSPICIOUS_PHRASES if phrase in lower_text]


def compute_score(
    header_findings: List[HeaderFinding],
    url_findings: List[UrlFinding],
    attachment_findings: List[AttachmentFinding],
    keyword_hits: List[str],
    domain_mismatch: bool,
    url_scans: List[UrlScanResult],
) -> Tuple[int, str, str]:
    score = 10 * len(header_findings) + 6 * len(url_findings) + 4 * len(attachment_findings) + 4 * len(keyword_hits)
    score += 3 * sum(1 for scan in url_scans if scan.issues)
    if domain_mismatch:
        score += 12

    if score >= 45:
        level = "high"
        summary = "High risk of phishing detected. Multiple issues require attention."
    elif score >= 25:
        level = "medium"
        summary = "Medium risk. Review the highlighted issues before trusting the message."
    else:
        level = "low"
        summary = "Low risk based on available signals, but still exercise caution."
    return score, level, summary


def domain_from_address(address: Optional[str]) -> Optional[str]:
    if not address or "@" not in address:
        return None
    return normalise_domain(address.split("@")[-1])


def normalise_domain(candidate: str) -> Optional[str]:
    if not candidate:
        return None
    extracted = tldextract.extract(candidate)
    if not extracted.domain:
        return None
    return f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain


def query_spf(domain: Optional[str]) -> Optional[str]:
    if not domain:
        return None
    try:
        answers = dns.resolver.resolve(domain, "TXT")
    except dns.exception.DNSException:
        return None
    for answer in answers:
        txt = "".join([part.decode("utf-8") if isinstance(part, bytes) else str(part) for part in answer.strings])
        if txt.lower().startswith("v=spf1"):
            return txt
    return None


def summarize_url_scans(scans: List[UrlScan]) -> List[UrlScanResult]:
    summary: List[UrlScanResult] = []
    for scan in scans:
        summary.append(
            UrlScanResult(
                url=scan.url,
                final_url=scan.final_url,
                http_status=scan.http_status,
                issues=scan.issues,
                redirects=[f"{hop.status}: {hop.url}" for hop in scan.redirect_chain],
            )
        )
    return summary


async def analyze_email(raw_bytes: bytes, whitelist: Optional[Set[str]] = None, envelope: Optional[EmlEnvelope] = None) -> AnalysisResult:
    whitelist = whitelist or set()
    envelope = envelope or EmlEnvelope.from_bytes(raw_bytes)
    body_text = envelope.body_text()

    from_address = envelope.sender
    reply_to = envelope.reply_to
    from_domain = domain_from_address(from_address)
    reply_domain = domain_from_address(reply_to)
    domain_mismatch = bool(from_domain and reply_domain and from_domain != reply_domain)

    urls = envelope.extract_urls()
    url_findings = analyze_urls(urls, whitelist)
    header_findings = evaluate_headers(envelope)
    attachment_findings = analyze_attachments(envelope)
    keyword_hits = evaluate_keywords(body_text)

    spf_txt = query_spf(from_domain)
    metadata = EnvelopeMetadata(
        subject=envelope.subject,
        sender=from_address,
        reply_to=reply_to,
        to=envelope.to_addresses,
        date=envelope.date,
        spf_record=spf_txt,
        nested_eml_count=len(envelope.nested_eml_parts()),
    )

    url_scans_raw = await crawl_urls(urls, whitelist)
    url_scan_summary = summarize_url_scans(url_scans_raw)

    score, risk_level, summary = compute_score(
        header_findings=header_findings,
        url_findings=url_findings,
        attachment_findings=attachment_findings,
        keyword_hits=keyword_hits,
        domain_mismatch=domain_mismatch,
        url_scans=url_scan_summary,
    )

    warnings: List[str] = []
    if domain_mismatch:
        warnings.append("Reply-To domain differs from From domain, which can indicate spoofing.")
    if not body_text.strip():
        warnings.append("Email body was empty or could not be parsed.")

    raw_headers: Dict[str, str] = {key: str(value) for key, value in envelope.message.items()}

    console.log("Analysis complete", json.dumps({"score": score, "risk": risk_level}))

    return AnalysisResult(
        metadata=metadata,
        score=score,
        risk_level=risk_level,
        summary=summary,
        urls=url_findings,
        url_scans=url_scan_summary,
        header_findings=header_findings,
        attachment_findings=attachment_findings,
        keywords=keyword_hits,
        warnings=warnings,
        raw_headers=raw_headers,
        body_preview=body_text[:500],
    )

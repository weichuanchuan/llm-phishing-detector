from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RedirectHop(BaseModel):
    status: Optional[int]
    url: str


class UrlScanResult(BaseModel):
    url: str
    final_url: str
    http_status: Optional[int]
    issues: List[str] = Field(default_factory=list)
    redirects: List[str] = Field(default_factory=list)


class UrlFinding(BaseModel):
    url: str
    reason: str


class HeaderFinding(BaseModel):
    header: str
    detail: str


class AttachmentFinding(BaseModel):
    filename: str
    detail: str


class EnvelopeMetadata(BaseModel):
    subject: Optional[str] = None
    sender: Optional[str] = None
    reply_to: Optional[str] = None
    to: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    spf_record: Optional[str] = None
    nested_eml_count: int = 0


class AnalysisResult(BaseModel):
    metadata: EnvelopeMetadata
    score: int
    risk_level: str
    summary: str
    body_preview: Optional[str] = None
    urls: List[UrlFinding] = Field(default_factory=list)
    url_scans: List[UrlScanResult] = Field(default_factory=list)
    header_findings: List[HeaderFinding] = Field(default_factory=list)
    attachment_findings: List[AttachmentFinding] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    raw_headers: Dict[str, str] = Field(default_factory=dict)


class PersistRequest(BaseModel):
    uuid: str
    report: AnalysisResult


class Feedback(BaseModel):
    uuid: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ExplainResponse(BaseModel):
    term: str
    explanation: str
    tips: List[str]


class PersistResponse(BaseModel):
    uuid: str
    status: str


class HealthResponse(BaseModel):
    status: str
    detail: str


class AnalyzeResponse(BaseModel):
    uuid: str
    analysis: AnalysisResult
    persisted: bool

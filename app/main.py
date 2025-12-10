from __future__ import annotations

import asyncio
import os
import uuid
from typing import Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .analyzer import analyze_email, load_whitelist
from .config import PUBLIC_DIR, STATIC_DIR
from .eml_utils import EmlEnvelope, ensure_mail_directories
from .models import AnalyzeResponse, ExplainResponse, Feedback, HealthResponse, PersistRequest, PersistResponse
from .rate_limit import RateLimiter
from .storage import ensure_directories, load_report, persist_report, save_feedback
from .watcher import MailDirectoryWatcher

app = FastAPI(title="MailCheck Python", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

GLOSSARY: Dict[str, Dict[str, str]] = {
    "spf": {
        "explanation": "SPF validates that the sending server is allowed to send mail for the domain.",
        "tips": "Review DNS SPF records and ensure they include your outbound mail servers.",
    },
    "dkim": {
        "explanation": "DKIM cryptographically signs messages to prevent tampering.",
        "tips": "Rotate DKIM keys regularly and publish them via DNS.",
    },
    "dmarc": {
        "explanation": "DMARC builds on SPF and DKIM to enforce alignment and reporting.",
        "tips": "Set a policy of quarantine or reject after monitoring reports.",
    },
    "link hygiene": {
        "explanation": "Links should point to trusted domains and use HTTPS.",
        "tips": "Hover over links to inspect the destination before clicking.",
    },
}

rate_limiter = RateLimiter()


async def process_incoming_mail(envelope: EmlEnvelope):
    whitelist = load_whitelist(PUBLIC_DIR / "whitelist.txt")
    if envelope.sender and not rate_limiter.allow(envelope.sender):
        return
    analysis = await analyze_email(envelope.message.as_bytes(), whitelist=whitelist, envelope=envelope)
    persist_report(str(uuid.uuid4()), analysis)


mail_watcher = MailDirectoryWatcher(process=process_incoming_mail)


@app.on_event("startup")
async def bootstrap() -> None:
    ensure_directories()
    ensure_mail_directories()
    loop = asyncio.get_running_loop()
    mail_watcher.start(loop)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    mail_watcher.stop()


@app.get("/", include_in_schema=False)
async def homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", detail="Analyzer is ready")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...), persist: bool = False) -> AnalyzeResponse:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file was empty")

    whitelist = load_whitelist(PUBLIC_DIR / "whitelist.txt")
    analysis = await analyze_email(payload, whitelist=whitelist)
    uid = str(uuid.uuid4())

    persisted = False
    if persist:
        persist_report(uid, analysis)
        persisted = True

    return AnalyzeResponse(uuid=uid, analysis=analysis, persisted=persisted)


@app.post("/persist", response_model=PersistResponse)
async def persist(body: PersistRequest) -> PersistResponse:
    return persist_report(body.uuid, body.report)


@app.get("/persist/{uuid}", response_model=AnalyzeResponse)
async def fetch(uuid: str) -> AnalyzeResponse:
    report = load_report(uuid)
    if not report:
        raise HTTPException(status_code=404, detail="No report found for this UUID")
    return AnalyzeResponse(uuid=uuid, analysis=report, persisted=True)


@app.get("/explain/{term}", response_model=ExplainResponse)
async def explain(term: str) -> ExplainResponse:
    normalized = term.lower()
    if normalized not in GLOSSARY:
        raise HTTPException(status_code=404, detail="Term not found")
    entry = GLOSSARY[normalized]
    tips = [tip.strip() for tip in entry["tips"].split(".") if tip.strip()]
    return ExplainResponse(term=term, explanation=entry["explanation"], tips=tips)


@app.post("/feedback")
async def feedback(feedback: Feedback) -> JSONResponse:
    save_feedback(feedback)
    return JSONResponse({"status": "received"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 3000)),
        reload=False,
    )

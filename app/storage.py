from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from .config import FEEDBACK_LOG, REPORT_DIR, TMP_DIR
from .models import AnalysisResult, Feedback, PersistResponse


def ensure_directories() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_LOG.exists():
        FEEDBACK_LOG.touch()


def persist_report(uuid: str, report: AnalysisResult) -> PersistResponse:
    ensure_directories()
    output_file = REPORT_DIR / f"{uuid}.json"
    output_file.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return PersistResponse(uuid=uuid, status="saved")


def load_report(uuid: str) -> Optional[AnalysisResult]:
    ensure_directories()
    path = REPORT_DIR / f"{uuid}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return AnalysisResult(**data)


def save_feedback(feedback: Feedback) -> None:
    ensure_directories()
    entry = feedback.model_dump(mode="json")
    entry["timestamp"] = datetime.utcnow().isoformat()
    with FEEDBACK_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

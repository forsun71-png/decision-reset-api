"""
로그 저장 서비스 (append-only JSONL)
특허 청구항 10 대응: 결론이 아닌 조건 정보만 저장
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_FILE = LOG_DIR / "reset_log.jsonl"


def log_analyze(
    input_text: str, source_type: str, domain: str,
    score: float, signals: list[str], fixation_detected: bool,
) -> None:
    _append({
        "event":             "analyze",
        "ts":                _now(),
        "source_type":       source_type,
        "domain":            domain,
        "input_length":      len(input_text),
        "fixation_score":    score,
        "signals":           signals,
        "fixation_detected": fixation_detected,
    })


def log_reset(
    input_text: str, source_type: str, domain: str, score: float,
    signals: list[str], reset_applied: bool, mode: str,
    output_count: int, llm_polish_applied: bool,
) -> None:
    _append({
        "event":              "reset",
        "ts":                 _now(),
        "source_type":        source_type,
        "domain":             domain,
        "input_length":       len(input_text),
        "fixation_score":     score,
        "signals":            signals,
        "reset_applied":      reset_applied,
        "mode":               mode,
        "output_count":       output_count,
        "llm_polish_applied": llm_polish_applied,
    })


def read_logs(limit: int = 100) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]]


def _append(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _append(entry: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
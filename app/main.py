from __future__ import annotations

from fastapi import FastAPI
from app.routes.analyze import router as analyze_router
from app.routes.reset import router as reset_router
from app.services.logger import read_logs

app = FastAPI(
    title="Decision Reset API",
    version="0.4.0",
    description=(
        "고착 방지 출력 제어 API\n\n"
        "Pipeline: fixation_detector → baseline_reset → reconstruction "
        "→ release_protection → llm_polish (optional)"
    ),
)

app.include_router(analyze_router)
app.include_router(reset_router)


@app.get("/")
def root() -> dict:
    return {
        "service": "Decision Reset API",
        "version": "0.4.0",
        "status": "ok",
        "pipeline": [
            "fixation_detector",
            "baseline_reset",
            "reconstruction",
            "release_protection",
            "llm_polish (optional)",
        ],
        "endpoints": ["/v1/analyze", "/v1/reset", "/v1/logs"],
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/v1/logs")
def logs(limit: int = 50) -> dict:
    return {"logs": read_logs(limit=limit)}

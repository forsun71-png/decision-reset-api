from __future__ import annotations

from fastapi import FastAPI

from app.routes.analyze import router as analyze_router
from app.routes.reset import router as reset_router
from app.services.logger import read_logs

app = FastAPI(
    title="Decision Reset API",
    description=(
        "고착된 판단을 감지하고, 현재 우선 원칙에 따라 "
        "복수의 판단 경로를 이유와 조건과 함께 제시하는 API"
    ),
    version="0.4.1",
)

# 라우터 등록
app.include_router(analyze_router)
app.include_router(reset_router)


@app.get("/")
def root() -> dict:
    return {
        "service": "Decision Reset API",
        "status": "ok",
        "docs": "/docs",
        "version": "0.4.1",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/logs")
def logs(limit: int = 100) -> list[dict]:
    return read_logs(limit=limit)
from __future__ import annotations

from fastapi import APIRouter

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.fixation_detector import detect_fixation
from app.services.seed_builder import build_seed
from app.services.logger import append_log

router = APIRouter(prefix="/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_judgment(request: AnalyzeRequest) -> AnalyzeResponse:
    # 1) 고착 탐지
    fixation_score, signals = detect_fixation(request.input_text)

    # 2) 고착 여부 판정
    fixation_detected = fixation_score >= 0.45
    intervention_triggered = fixation_detected
    intervention_mode = "reset" if fixation_detected else "keep"

    # 3) seed 생성
    seed = build_seed(request.input_text, request.domain)

    # 4) 로그
    append_log(
        {
            "endpoint": "analyze",
            "input_text": request.input_text,
            "source_type": request.source_type.value,
            "domain": request.domain.value,
            "fixation_detected": fixation_detected,
            "fixation_score": fixation_score,
            "signals": signals,
            "intervention_triggered": intervention_triggered,
        }
    )

    # 5) 응답
    return AnalyzeResponse(
        fixation_detected=fixation_detected,
        fixation_score=fixation_score,
        intervention_triggered=intervention_triggered,
        intervention_mode=intervention_mode,
        signals=signals,
        seed=seed,
    )
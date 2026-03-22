from __future__ import annotations

from fastapi import APIRouter
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.fixation_detector import detect_fixation, is_fixated, build_seed
from app.services import logger

router = APIRouter(prefix="/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    score, signals = detect_fixation(request.input_text)
    fixation_detected = is_fixated(score)
    seed = build_seed(request.input_text, request.domain.value)

    logger.log_analyze(
        input_text=request.input_text,
        source_type=request.source_type.value,
        domain=request.domain.value,
        score=score,
        signals=signals,
        fixation_detected=fixation_detected,
    )

    return AnalyzeResponse(
        fixation_detected=fixation_detected,
        fixation_score=score,
        intervention_triggered=fixation_detected,
        intervention_mode="reset" if fixation_detected else "keep",
        signals=signals,
        seed=seed,
    )

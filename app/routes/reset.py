from __future__ import annotations

from fastapi import APIRouter
from app.schemas import (
    ResetRequest, ResetResponse,
    BaselineReset, ReleaseProtection,
)
from app.services.fixation_detector import detect_fixation, is_fixated, build_seed
from app.services.baseline_reset import apply_baseline_reset
from app.services.reconstruction import get_scenarios
from app.services.release_protection import build_release_protection
from app.services.llm_polish import polish
from app.services import logger

router = APIRouter(prefix="/v1", tags=["reset"])


@router.post("/reset", response_model=ResetResponse)
def reset(request: ResetRequest) -> ResetResponse:

    # ── 1. 고착 감지 ────────────────────────────────────────────────────────
    score, signals = detect_fixation(request.input_text)
    fixation_detected = is_fixated(score)
    seed = build_seed(request.input_text, request.domain.value)

    # ── 2. 고착 미감지: 기존 판단 유지 + 균형 경로 제공 ────────────────────
    if not fixation_detected:
        scenarios = get_scenarios(request.domain, request.mode, fixation_score=score)
        outputs   = [s["summary"] for s in scenarios]
        logger.log_reset(
            request.input_text, request.source_type.value,
            request.domain.value, score, signals,
            False, request.mode.value, len(outputs), False,
        )
        return ResetResponse(
            fixation_detected=False,
            fixation_score=score,
            intervention_triggered=False,
            intervention_mode="keep",
            baseline_reset=BaselineReset(
                applied=False, dependency_cut=False, neutral_state_transition=False,
            ),
            detected_signals=signals,
            seed=seed,
            outputs=outputs,
            scenarios=scenarios,
            release_protection=ReleaseProtection(
                enabled=False, mode="none", anti_reuse_rules=[],
            ),
            llm_polish_applied=False,
        )

    # ── 3. Baseline Reset (Hard Reset) ──────────────────────────────────────
    cut_info = apply_baseline_reset(request.input_text)

    # ── 4. 경로형 재구성 (A안/B안/C안) ─────────────────────────────────────
    scenarios = get_scenarios(request.domain, request.mode, fixation_score=score)
    outputs   = [s["summary"] for s in scenarios]

    # ── 5. 선택적 LLM 표현 보정 (판단 구조 변경 없음) ──────────────────────
    outputs, llm_applied = polish(outputs, domain=request.domain.value)
    # polish 후 outputs과 scenarios summary 동기화
    for i, s in enumerate(scenarios):
        if i < len(outputs):
            s["summary"] = outputs[i]

    # ── 6. 로그 저장 ────────────────────────────────────────────────────────
    logger.log_reset(
        request.input_text, request.source_type.value,
        request.domain.value, score, signals,
        True, request.mode.value, len(outputs), llm_applied,
    )

    return ResetResponse(
        fixation_detected=True,
        fixation_score=score,
        intervention_triggered=True,
        intervention_mode=request.mode.value,
        baseline_reset=BaselineReset(
            applied=cut_info["applied"],
            dependency_cut=cut_info["dependency_cut"],
            neutral_state_transition=cut_info["neutral_state_transition"],
        ),
        detected_signals=signals,
        seed={**seed, **{
            k: v for k, v in cut_info.items()
            if k in ("removed_markers", "compressed_seed_text",
                     "hold_streak", "last_hold_reason")
        }},
        outputs=outputs,
        scenarios=scenarios,
        release_protection=build_release_protection(request.mode, enabled=True),
        llm_polish_applied=llm_applied,
    )

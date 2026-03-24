from __future__ import annotations

from fastapi import APIRouter

from app.schemas import (
    ResetRequest,
    ResetResponse,
    BaselineReset,
    ReleaseProtection,
)
from app.services.fixation_detector import detect_fixation_with_stage
from app.services.response_mode import classify_response_mode
from app.services.seed_builder import build_seed
from app.services.reconstruction import get_scenarios, get_outputs_from_scenarios
from app.services.logger import append_log

router = APIRouter(prefix="/v1", tags=["reset"])


@router.post("/reset", response_model=ResetResponse)
def reset_judgment(request: ResetRequest) -> ResetResponse:
    # 1) 고착 탐지
    fixation_score, detected_signals, fixation_stage = detect_fixation_with_stage(request.input_text)

    # 2) 고착 여부
    fixation_detected = (
        fixation_score >= 0.35
        or "single_path_judgment" in detected_signals
        or "lack_of_alternatives" in detected_signals
    )

    # 3) 응대 모드 분류
    response_mode = classify_response_mode(
        text=request.input_text,
        fixation_score=fixation_score,
        detected_signals=detected_signals,
    )

    # 4) 개입 여부
    intervention_triggered = fixation_detected
    intervention_mode = request.mode.value

    # 5) seed 생성
    seed = build_seed(request.input_text, request.domain)

    # 6) baseline reset
    baseline_reset = BaselineReset(
        applied=intervention_triggered,
        dependency_cut=intervention_triggered,
        neutral_state_transition=intervention_triggered,
    )

    # 7) 시나리오 생성
    scenarios = get_scenarios(
        domain=request.domain.value,
        input_text=request.input_text,
        detected_signals=detected_signals,
    )

    outputs = get_outputs_from_scenarios(scenarios)

    # 8) release protection
    if intervention_triggered:
        release_protection = ReleaseProtection(
            enabled=True,
            mode="strict_hold" if request.mode.value == "strict" else "soft_hold",
            anti_reuse_rules=[
                "no_direct_reuse_of_previous_judgment",
                "must_include_alternative_path",
                "must_reduce_overconfidence_expression",
            ],
        )
    else:
        release_protection = ReleaseProtection(
            enabled=False,
            mode="none",
            anti_reuse_rules=[],
        )

    # 9) 로그 저장
    append_log(
        {
            "endpoint": "reset",
            "input_text": request.input_text,
            "source_type": request.source_type.value,
            "domain": request.domain.value,
            "mode": request.mode.value,
            "fixation_detected": fixation_detected,
            "fixation_score": fixation_score,
            "fixation_stage": fixation_stage,
            "detected_signals": detected_signals,
            "intervention_triggered": intervention_triggered,
            "response_mode": response_mode,
            "scenario_count": len(scenarios),
            "llm_polish_applied": False,
        }
    )

    # 10) 응답
    return ResetResponse(
        fixation_detected=fixation_detected,
        fixation_score=fixation_score,
        fixation_stage=fixation_stage,
        intervention_triggered=intervention_triggered,
        intervention_mode=intervention_mode,
        response_mode=response_mode,
        baseline_reset=baseline_reset,
        detected_signals=detected_signals,
        seed=seed,
        outputs=outputs,
        scenarios=scenarios,
        release_protection=release_protection,
        llm_polish_applied=False,
    )
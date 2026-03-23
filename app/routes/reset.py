from __future__ import annotations

from fastapi import APIRouter

from app.schemas import (
    ResetRequest,
    ResetResponse,
    BaselineReset,
    ReleaseProtection,
)
from app.services.fixation_detector import detect_fixation
from app.services.seed_builder import build_seed
from app.services.reconstruction import get_scenarios, get_outputs_from_scenarios
from app.services.logger import append_log

router = APIRouter(prefix="/v1", tags=["reset"])


@router.post("/reset", response_model=ResetResponse)
def reset_judgment(request: ResetRequest) -> ResetResponse:
    # 1) 고착 탐지
    fixation_score, detected_signals = detect_fixation(request.input_text)

    # 고착 여부 기준
    fixation_detected = fixation_score >= 0.45
    intervention_triggered = fixation_detected

    # 2) seed 생성
    seed = build_seed(request.input_text, request.domain)

    # 3) baseline reset 상태
    baseline_reset = BaselineReset(
        applied=intervention_triggered,
        dependency_cut=intervention_triggered,
        neutral_state_transition=intervention_triggered,
    )

    # 4) 시나리오 생성
    scenarios = get_scenarios(
        domain=request.domain.value,
        input_text=request.input_text,
        detected_signals=detected_signals,
    )

    # 하위 호환용 요약 출력
    outputs = get_outputs_from_scenarios(scenarios)

    # 5) release protection
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

    # 6) 로그
    append_log(
        {
            "endpoint": "reset",
            "input_text": request.input_text,
            "source_type": request.source_type.value,
            "domain": request.domain.value,
            "mode": request.mode.value,
            "fixation_detected": fixation_detected,
            "fixation_score": fixation_score,
            "detected_signals": detected_signals,
            "intervention_triggered": intervention_triggered,
            "scenario_count": len(scenarios),
            "llm_polish_applied": False,
        }
    )

    # 7) 응답
    return ResetResponse(
        fixation_detected=fixation_detected,
        fixation_score=fixation_score,
        intervention_triggered=intervention_triggered,
        intervention_mode=request.mode.value,
        baseline_reset=baseline_reset,
        detected_signals=detected_signals,
        seed=seed,
        outputs=outputs,
        scenarios=scenarios,
        release_protection=release_protection,
        llm_polish_applied=False,
    )
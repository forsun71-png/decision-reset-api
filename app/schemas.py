from __future__ import annotations

from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field


# ── ENUMS ────────────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    user = "user"
    external_ai = "external_ai"


class DomainType(str, Enum):
    general = "general"
    finance = "finance"
    investment = "investment"
    policy = "policy"
    counseling = "counseling"
    strategy = "strategy"


class ResetMode(str, Enum):
    strict = "strict"
    soft = "soft"


# ── REQUEST ──────────────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    fixation_detected: bool
    fixation_score: float
    fixation_stage: str
    intervention_triggered: bool
    intervention_mode: Literal["keep", "reset"]
    signals: List[str]
    seed: dict

class ResetResponse(BaseModel):
    fixation_detected: bool
    fixation_score: float
    fixation_stage: str
    intervention_triggered: bool
    intervention_mode: str
    response_mode: str
    baseline_reset: BaselineReset
    detected_signals: List[str]
    seed: dict
    outputs: List[str]
    scenarios: List[dict]
    release_protection: ReleaseProtection
    llm_polish_applied: bool


# ── RESPONSE ─────────────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    fixation_detected: bool
    fixation_score: float
    fixation_stage: str
    intervention_triggered: bool
    intervention_mode: Literal["keep", "reset"]
    signals: List[str]
    seed: dict


class BaselineReset(BaseModel):
    applied: bool
    dependency_cut: bool
    neutral_state_transition: bool


class ReleaseProtection(BaseModel):
    enabled: bool
    mode: str
    anti_reuse_rules: List[str]


class ResetResponse(BaseModel):
    fixation_detected: bool
    fixation_score: float

    # 개입 여부
    intervention_triggered: bool
    intervention_mode: str

    # 🔥 핵심 추가
    response_mode: str  # expand / guide / step_back / close

    # 구조 정보
    baseline_reset: BaselineReset
    detected_signals: List[str]

    # 내부 상태
    seed: dict

    # 하위 호환 출력
    outputs: List[str]

    # 🔥 핵심 출력
    scenarios: List[dict]

    # 보호 구조
    release_protection: ReleaseProtection

    # 확장 가능성
    llm_polish_applied: bool
from __future__ import annotations

from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field


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


class AnalyzeRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=4000)
    source_type: SourceType = SourceType.user
    domain: DomainType = DomainType.general


class ResetRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=4000)
    source_type: SourceType = SourceType.user
    domain: DomainType = DomainType.general
    mode: ResetMode = ResetMode.strict


class AnalyzeResponse(BaseModel):
    fixation_detected: bool
    fixation_score: float
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
    intervention_triggered: bool
    intervention_mode: str
    baseline_reset: BaselineReset
    detected_signals: List[str]
    seed: dict
    outputs: List[str]
    scenarios: List[dict]
    release_protection: ReleaseProtection
    llm_polish_applied: bool
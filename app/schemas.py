"""
스키마 정의 (schemas.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
변경 이력:
  v0.4 - GPT 버전 용어 통합
    · SourceType, DomainType enum 추가
    · BaselineReset 구조 추가 (neutral_state_transition 포함)
    · intervention_triggered / intervention_mode 필드 통합
    · LLM 보정 여부 응답 필드 추가 (llm_polish_applied)
"""

from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# ─── Enum ────────────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    user        = "user"
    external_ai = "external_ai"


class DomainType(str, Enum):
    general    = "general"
    finance    = "finance"
    investment = "investment"
    policy     = "policy"
    counseling = "counseling"
    strategy   = "strategy"
    medical    = "medical"
    legal      = "legal"


class ResetMode(str, Enum):
    soft   = "soft"
    strict = "strict"


# ─── Request ─────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    input_text:  str        = Field(..., min_length=1, max_length=4000)
    source_type: SourceType = SourceType.user
    domain:      DomainType = DomainType.general


class ResetRequest(BaseModel):
    input_text:  str        = Field(..., min_length=1, max_length=4000)
    source_type: SourceType = SourceType.user
    domain:      DomainType = DomainType.general
    mode:        ResetMode  = ResetMode.strict


# ─── Sub-models ──────────────────────────────────────────────────────────────

class BaselineReset(BaseModel):
    """
    Hard Reset 적용 결과.
    특허 청구항 1(c)(d), 청구항 4 대응.
    """
    applied:                  bool
    dependency_cut:           bool        # 확률적 의존성 차단 여부
    neutral_state_transition: bool        # 중립 상태 전이 여부


class ReleaseProtection(BaseModel):
    """
    보호 구간 구조.
    특허 청구항 1(g), 청구항 7 대응.
    """
    enabled:          bool
    mode:             str
    anti_reuse_rules: list[str]


# ─── Response ─────────────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    fixation_detected:    bool
    fixation_score:       float
    intervention_triggered: bool
    intervention_mode:    Literal["keep", "reset"]
    signals:              list[str]
    seed:                 dict


class ResetResponse(BaseModel):
    fixation_detected:    bool
    fixation_score:       float
    intervention_triggered: bool
    intervention_mode:    str
    baseline_reset:       BaselineReset
    detected_signals:     list[str]
    seed:                 dict
    outputs:              list[str]
    release_protection:   ReleaseProtection
    llm_polish_applied:   bool = False     # LLM 표현 보정 적용 여부
    scenarios:            list[dict] = []  # 경로형 재구성 결과 (A안/B안/C안)

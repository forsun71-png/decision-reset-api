"""
보호 구간 서비스 (Release Protection)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
특허 대응:
  · 청구항 1(g): 보호 구간 유지
  · 청구항 7: 고착 지표 가중치 50% 감쇄
"""

from __future__ import annotations

from app.schemas import ReleaseProtection, ResetMode

PROTECTION_WEIGHT_DECAY = 0.5

ANTI_REUSE_RULES = [
    "no_direct_reuse_of_previous_judgment",
    "must_include_alternative_path",
    "must_reduce_overconfidence_expression",
]


def build_release_protection(mode: ResetMode, enabled: bool = True) -> ReleaseProtection:
    if not enabled:
        return ReleaseProtection(enabled=False, mode="none", anti_reuse_rules=[])

    return ReleaseProtection(
        enabled=True,
        mode="strict_hold" if mode == ResetMode.strict else "soft_hold",
        anti_reuse_rules=ANTI_REUSE_RULES,
    )


def apply_weight_decay(score: float) -> float:
    """보호 구간 내 고착 점수 50% 감쇄 (청구항 7)."""
    return round(score * PROTECTION_WEIGHT_DECAY, 4)

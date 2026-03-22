"""
Baseline Reset 서비스
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPT 버전 용어 적용: baseline_reset, neutral_state_transition
v0.3 로직 유지: dependency_cut, 버퍼 초기화값 반환

역할:
  - 확신·반복 표현 제거 (마커 차단)
  - 판단 결론 제거, 조건 문장만 압축 추출
  - Hard Reset 상태 초기화값 반환

특허 대응:
  · 청구항 1(c): 재사용 차단 상태 전이
  · 청구항 1(d): 누적 판단값 / 이력 버퍼 초기화
  · 청구항 4: hold_streak=0.0, reason_buffer 초기화
"""

from __future__ import annotations

import re

OVERCONFIDENCE_MARKERS = [
    "무조건", "반드시", "확실히", "절대", "100%",
    "틀림없이", "당연히", "분명히", "명백히",
]

OVERCONFIDENCE_PATTERN = re.compile(
    "|".join(re.escape(m) for m in OVERCONFIDENCE_MARKERS)
)


def apply_baseline_reset(input_text: str) -> dict:
    """
    Baseline Reset 적용.

    처리 내용:
      1. 확신 마커 제거 및 기록
      2. 조건 문장만 최대 3개 압축 추출
      3. Hard Reset 상태 초기화값 반환

    Returns:
        baseline_reset_info dict (compressed_seed_text 포함)
    """
    text = input_text.strip()

    # 1. 확신 마커 감지 및 제거
    removed_markers = [m for m in OVERCONFIDENCE_MARKERS if m in text]
    cleaned = OVERCONFIDENCE_PATTERN.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # 2. 조건 문장 압축 (최대 3문장)
    sentences = _split_sentences(cleaned)
    compressed = " ".join(sentences[:3])

    return {
        # BaselineReset 응답 필드
        "applied":                  True,
        "dependency_cut":           True,
        "neutral_state_transition": True,
        # 내부 처리용
        "removed_markers":          removed_markers,
        "compressed_seed_text":     compressed,
        # Hard Reset 상태 초기화 (청구항 4)
        "hold_streak":              0.0,
        "last_hold_reason":         "",
        "hold_reason_buffer":       [],
        "release_protection":       True,
    }


def _split_sentences(text: str) -> list[str]:
    raw = text.replace(".", ".\n").replace("!", "!\n").replace("?", "?\n")
    return [s.strip() for s in raw.splitlines() if s.strip()]

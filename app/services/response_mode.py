from __future__ import annotations

import re
from typing import Dict, List


# ── 패턴 정의 ───────────────────────────────────────────────────────────────

QUESTION_PATTERNS: List[str] = [
    r"\?$",
    r"무엇",
    r"왜",
    r"어떻게",
    r"어떤",
    r"일까",
    r"인가",
]

OPENNESS_PATTERNS: List[str] = [
    r"가능성",
    r"모른다",
    r"궁금",
    r"생각해보면",
    r"일 수도",
    r"일 수 있다",
    r"일지",
    r"같다",
]

RIGID_PATTERNS: List[str] = [
    r"무조건",
    r"반드시",
    r"절대",
    r"그럴 리 없다",
    r"틀림없다",
    r"확실하다",
    r"분명하다",
]

HOSTILE_PATTERNS: List[str] = [
    r"멍청",
    r"한심",
    r"헛소리",
    r"쓸데없는",
    r"답할 가치",
    r"말이 안 된다",
    r"다 틀렸다",
    r"꺼져",
    r"닥쳐",
    r"웃기고 있네",
    r"너 같은",
]

CLOSED_DIALOGUE_PATTERNS: List[str] = [
    r"내 말이 맞다",
    r"더 말할 필요 없다",
    r"논쟁할 필요 없다",
    r"이미 끝난 얘기다",
    r"답은 정해져 있다",
]


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _score_patterns(patterns: List[str], text: str, weight: float = 1.0) -> float:
    score = 0.0
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            score += weight
    return score


# ── 점수 계산 ───────────────────────────────────────────────────────────────

def compute_response_scores(
    text: str,
    fixation_score: float = 0.0,
    detected_signals: List[str] | None = None,
) -> Dict[str, float]:
    raw = text.strip()
    signals = detected_signals or []

    openness = 0.0
    rigidity = 0.0
    hostility = 0.0

    # 열린 질문/탐색성
    openness += _score_patterns(QUESTION_PATTERNS, raw, 0.35)
    openness += _score_patterns(OPENNESS_PATTERNS, raw, 0.20)

    # 닫힌 단정성
    rigidity += _score_patterns(RIGID_PATTERNS, raw, 0.35)
    rigidity += min(fixation_score, 1.0) * 0.6

    # 신호 기반 경직도 가중
    if "overconfidence" in signals:
        rigidity += 0.20
    if "single_path_judgment" in signals:
        rigidity += 0.20
    if "memory_fixation" in signals or "past_anchor" in signals:
        rigidity += 0.15
    if "counterevidence_block" in signals:
        rigidity += 0.20
    if "group_generalization" in signals or "hostile_attribution" in signals:
        rigidity += 0.20
    if "no_suspension" in signals or "memory_to_conclusion" in signals:
        rigidity += 0.15

    # 공격성/소모성
    hostility += _score_patterns(HOSTILE_PATTERNS, raw, 0.50)
    hostility += _score_patterns(CLOSED_DIALOGUE_PATTERNS, raw, 0.35)

    # 점수 범위 정리
    openness = round(min(openness, 1.0), 2)
    rigidity = round(min(rigidity, 1.0), 2)
    hostility = round(min(hostility, 1.0), 2)

    return {
        "openness": openness,
        "rigidity": rigidity,
        "hostility": hostility,
    }


# ── 모드 분류 ───────────────────────────────────────────────────────────────

def classify_response_mode(
    text: str,
    fixation_score: float = 0.0,
    detected_signals: List[str] | None = None,
) -> str:
    scores = compute_response_scores(
        text=text,
        fixation_score=fixation_score,
        detected_signals=detected_signals,
    )

    openness = scores["openness"]
    rigidity = scores["rigidity"]
    hostility = scores["hostility"]

    # 1) 적대/소모 상태 → 종료
    if hostility >= 0.70:
        return "close"

    # 2) 강한 고착 + 수용성 낮음 → 후퇴
    if rigidity >= 0.70 and openness < 0.35:
        return "step_back"

    # 3) 열린 질문 + 경직 낮음 → 확장
    if openness >= 0.45 and rigidity < 0.55:
        return "expand"

    # 4) 나머지 → 유도
    return "guide"
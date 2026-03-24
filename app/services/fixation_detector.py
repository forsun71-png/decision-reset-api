from __future__ import annotations

import re
from typing import Dict, List, Tuple

# ── 확신형 ───────────────────────────────────────────────────────────────────
OVERCONFIDENCE_PATTERNS = [
    r"무조건", r"반드시", r"절대", r"확실히", r"틀림없이", r"100%",
    r"\bdefinitely\b", r"\bguaranteed\b",
]

REPETITION_PATTERNS = [
    r"(같은 말|반복)", r"\balways\b", r"\bnever\b",
]

ALTERNATIVE_HINTS = [
    r"가능성", r"리스크", r"대안", r"반대", r"조건",
    r"uncertain", r"risk", r"alternative", r"scenario",
]

# ── 편향형 ───────────────────────────────────────────────────────────────────
GROUP_GENERALIZATION_PATTERNS = [
    r"사람들은", r"그들은", r"저쪽은", r"지지자들은", r"반대하는 사람들은", r"모두", r"전부",
]

HOSTILE_ATTRIBUTION_PATTERNS = [
    r"갈라치기", r"선동", r"조작", r"속이려", r"일부러", r"악의적",
]

POLITICAL_BIAS_PATTERNS = [
    r"문재인", r"윤석열", r"이재명", r"보수", r"진보", r"좌파", r"우파", r"정권", r"정치",
]

# ── 기억형 ───────────────────────────────────────────────────────────────────
MEMORY_PATTERNS = [
    r"원래 .* 사람",
    r"좋은 사람",
    r"착한 사람",
    r"믿을 수 있는 사람",
    r"예전에 .*",
    r"그동안 .*",
    r"항상 .*",
    r"지금까지 .*",
    r"오래 알아서",
    r"친해서",
    r"잘 알아서",
    r"그럴 리 없다",
    r"아닐 것이다",
    r"그런 사람 아니다",
]

# ── 순서 위반형 ──────────────────────────────────────────────────────────────
CURRENT_PATTERNS = [
    r"지금", r"현재", r"이번", r"오늘", r"방금", r"이번 일", r"실제로", r"확인", r"사실",
]

PAST_PATTERNS = [
    r"원래", r"예전", r"그동안", r"지금까지", r"본래", r"예전에도",
    r"좋은 사람", r"착한 사람", r"믿을 수 있는 사람", r"그런 사람 아니다",
]

SUSPEND_PATTERNS = [
    r"확인해", r"확인이 필요", r"더 봐야", r"모른다", r"가능성", r"단정하기 어렵", r"보류",
]

CONCLUSION_PATTERNS = [
    r"그럴 리 없다", r"문제없다", r"틀림없다", r"맞다", r"갈라치기", r"선동", r"조작", r"아닐 것이다",
]


def _contains_any(patterns: List[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def detect_memory_fixation(text: str) -> Tuple[float, List[str]]:
    score = 0.0
    signals: List[str] = []

    for pattern in MEMORY_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            score += 0.10
            if "memory_fixation" not in signals:
                signals.append("memory_fixation")

    if re.search(r"그럴 리 없다|아닐 것이다", text, flags=re.IGNORECASE):
        score += 0.20
        signals.append("counterevidence_block")

    return min(score, 1.0), signals


def detect_bias_fixation(text: str) -> Tuple[float, List[str]]:
    score = 0.0
    signals: List[str] = []

    if _contains_any(GROUP_GENERALIZATION_PATTERNS, text):
        score += 0.15
        signals.append("group_generalization")

    if _contains_any(HOSTILE_ATTRIBUTION_PATTERNS, text):
        score += 0.20
        signals.append("hostile_attribution")

    if _contains_any(POLITICAL_BIAS_PATTERNS, text):
        score += 0.10
        signals.append("political_bias_frame")

    return min(score, 1.0), signals


def detect_order_violation(text: str) -> Tuple[float, List[str]]:
    score = 0.0
    signals: List[str] = []

    has_current = _contains_any(CURRENT_PATTERNS, text)
    has_past = _contains_any(PAST_PATTERNS, text)
    has_suspend = _contains_any(SUSPEND_PATTERNS, text)
    has_conclusion = _contains_any(CONCLUSION_PATTERNS, text)

    if has_past:
        score += 0.10
        signals.append("past_anchor")

    if not has_current and has_conclusion:
        score += 0.15
        signals.append("current_omission")

    if not has_suspend and has_conclusion:
        score += 0.15
        signals.append("no_suspension")

    if has_past and has_conclusion:
        score += 0.20
        signals.append("memory_to_conclusion")

    return min(score, 1.0), signals


def fixation_stage(score: float, signals: List[str]) -> str:
    s = set(signals)

    if {"memory_fixation", "counterevidence_block", "past_anchor"} & s:
        if "memory_to_conclusion" in s or score >= 0.65:
            return "severe"
        return "deep"

    if {"group_generalization", "hostile_attribution"} & s:
        if score >= 0.50:
            return "progressing"
        return "early"

    if "overconfidence" in s or "repetition_pattern" in s:
        if score >= 0.50:
            return "progressing"

    if "single_path_judgment" in s or "lack_of_alternatives" in s:
        return "early"

    return "none"


def detect_fixation(input_text: str) -> Tuple[float, List[str]]:
    text = input_text.strip()
    lowered = text.lower()
    score = 0.0
    signals: List[str] = []

    # 확신형
    if _contains_any(OVERCONFIDENCE_PATTERNS, text):
        score += 0.25
        signals.append("overconfidence")

    if _contains_any(REPETITION_PATTERNS, text):
        score += 0.10
        signals.append("repetition_pattern")

    if len(text) > 5 and not _contains_any(ALTERNATIVE_HINTS, text):
        score += 0.20
        signals.append("lack_of_alternatives")

    if len(text.split()) <= 10:
        score += 0.20
        signals.append("single_path_judgment")

    if lowered.count("!") >= 1:
        score += 0.05
        signals.append("intensifier")

    # 편향형
    bias_score, bias_signals = detect_bias_fixation(text)
    score += bias_score
    signals.extend(bias_signals)

    # 기억형
    memory_score, memory_signals = detect_memory_fixation(text)
    score += memory_score
    signals.extend(memory_signals)

    # 순서 위반형
    order_score, order_signals = detect_order_violation(text)
    score += order_score
    signals.extend(order_signals)

    # 조합 가산점
    combo_bonus = 0.0

    if "memory_fixation" in signals and "counterevidence_block" in signals:
        combo_bonus += 0.15

    if "past_anchor" in signals and "memory_to_conclusion" in signals:
        combo_bonus += 0.15

    if "group_generalization" in signals and "hostile_attribution" in signals:
        combo_bonus += 0.15

    if "overconfidence" in signals and "single_path_judgment" in signals:
        combo_bonus += 0.10

    if "lack_of_alternatives" in signals and "single_path_judgment" in signals:
        combo_bonus += 0.10

    score = min(round(score + combo_bonus, 2), 1.0)
    signals = list(dict.fromkeys(signals))
    return score, signals


def detect_fixation_with_stage(input_text: str) -> Tuple[float, List[str], str]:
    score, signals = detect_fixation(input_text)
    stage = fixation_stage(score, signals)
    return score, signals, stage
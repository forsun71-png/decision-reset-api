from __future__ import annotations
import re
from datetime import datetime, timezone

OVERCONFIDENCE_PATTERNS = [
    r"무조건", r"반드시", r"확실히", r"100%", r"틀림없이", r"절대로?",
    r"당연히", r"분명히", r"명백히", r"확신한다", r"확신합니다",
    r"의심할 여지가 없", r"오류가 없",
    r"guaranteed", r"definitely", r"only outcome",
]

REPETITION_PATTERNS = [
    r"(같은 말|반복하지만|앞서 말했듯|다시 말하지만)",
    r"이미 설명했듯", r"처음에 말한 것처럼",
    r"\b(always|never)\b",
]

COUNTER_FAILURE_PATTERNS = [
    r"다른 방법은 없", r"대안이 없", r"이것만이", r"유일한 방법",
    r"다른 선택지가 없", r"다른 가능성은",
    r"전혀 없다", r"밖에 없다", r"만이 정답", r"하나다",
    r"전부 틀", r"모두 틀", r"의미가 없다", r"고려할 필요가 없",
    r"장점밖에", r"단점은 없",
]

ALTERNATIVE_HINTS = [
    r"가능성", r"리스크", r"대안", r"반대", r"조건", r"불확실",
    r"risk", r"alternative", r"scenario", r"uncertain",
]

WEIGHTS = {
    "overconfidence":       0.35,
    "repetition_pattern":   0.15,
    "counter_failure":      0.30,
    "lack_of_alternatives": 0.15,
    "single_path_judgment": 0.05,
    "intensifier":          0.05,
}

FIXATION_THRESHOLD = 0.35
UNCERTAINTY_THRESHOLD = 1.1


def _match(patterns, text):
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def detect_fixation(input_text):
    text = input_text.strip()
    score = 0.0
    signals = []

    if _match(OVERCONFIDENCE_PATTERNS, text):
        score += WEIGHTS["overconfidence"]
        signals.append("overconfidence")

    if _match(REPETITION_PATTERNS, text):
        score += WEIGHTS["repetition_pattern"]
        signals.append("repetition_pattern")

    if _match(COUNTER_FAILURE_PATTERNS, text):
        score += WEIGHTS["counter_failure"]
        signals.append("counter_failure")

    if len(text) > 5 and not _match(ALTERNATIVE_HINTS, text):
        score += WEIGHTS["lack_of_alternatives"]
        signals.append("lack_of_alternatives")

    if len(text.split()) <= 8:
        score += WEIGHTS["single_path_judgment"]
        signals.append("single_path_judgment")

    if text.count("!") >= 1:
        score += WEIGHTS["intensifier"]
        signals.append("intensifier")

    return min(round(score, 4), 1.0), signals


def is_fixated(score):
    return score >= FIXATION_THRESHOLD


def build_seed(input_text, domain):
    text = input_text.strip()
    words = text.split()
    claim_type = "neutral"
    if re.search(r"오른다|상승|좋다|bull|buy|increase", text, re.IGNORECASE):
        claim_type = "positive_assertion"
    elif re.search(r"내린다|하락|나쁘다|bear|sell|decrease", text, re.IGNORECASE):
        claim_type = "negative_assertion"
    confidence = "high" if re.search(r"무조건|반드시|확실히|절대|100%", text) else "medium"
    return {
        "domain": domain,
        "claim_type": claim_type,
        "confidence": confidence,
        "input_length": len(text),
        "keyword_count": len(words),
        "condition_snapshot": text[:120] + ("..." if len(text) > 120 else ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

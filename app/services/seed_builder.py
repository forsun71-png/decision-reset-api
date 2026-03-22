from __future__ import annotations

import re
from app.schemas import DomainType


def build_seed(input_text: str, domain: DomainType) -> dict:
    text = input_text.strip()
    claim_type = "neutral"

    if re.search(r"오른다|상승|좋다|bull|buy|increase", text, flags=re.IGNORECASE):
        claim_type = "positive_assertion"
    elif re.search(r"내린다|하락|나쁘다|bear|sell|decrease", text, flags=re.IGNORECASE):
        claim_type = "negative_assertion"

    confidence = "high" if re.search(r"무조건|반드시|확실히|절대|100%", text) else "medium"

    return {
        "domain": domain.value,
        "claim_type": claim_type,
        "confidence": confidence,
        "length": len(text.split()),
    }
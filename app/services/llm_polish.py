"""
LLM 표현 보정 레이어 (선택적 보조)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
원칙:
  - 판단 구조는 reconstruction.py가 결정
  - 이 모듈은 표현 품질만 보정 (문장 다듬기)
  - 실패 시 원본 outputs 그대로 반환 (서비스 무중단)
  - API 키 없어도 전체 서비스 정상 동작

활성화: 환경변수 USE_LLM=true + ANTHROPIC_API_KEY=sk-...

보정 금지:
  - 판단 결론 변경 금지
  - 반대 시나리오 제거 금지
  - 확신 표현 추가 금지
"""

from __future__ import annotations

import os

USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

_SYSTEM = """당신은 판단 재구성 결과의 표현만 다듬는 보조 역할입니다.

엄격한 제한:
1. 판단 결론을 변경하지 마십시오.
2. 반대 시나리오를 제거하지 마십시오.
3. 확신 표현(반드시, 100%, 확실히 등)을 추가하지 마십시오.
4. 각 문장의 핵심 의미를 유지하면서 자연스러운 한국어로만 다듬으십시오.
5. 입력과 동일한 개수의 문장을 JSON 배열로만 반환하십시오.
예: ["문장1", "문장2"]"""


def polish(outputs: list[str], domain: str) -> tuple[list[str], bool]:
    """
    Returns: (outputs, llm_applied)
    """
    if not USE_LLM or not ANTHROPIC_API_KEY:
        return outputs, False

    result = _call_anthropic(outputs, domain)
    return result, result is not outputs


def _call_anthropic(outputs: list[str], domain: str) -> list[str]:
    try:
        import anthropic, json
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        user_msg = f"도메인: {domain}\n입력:\n{json.dumps(outputs, ensure_ascii=False)}"
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text.strip()
        polished = json.loads(raw)
        if isinstance(polished, list) and len(polished) == len(outputs):
            if all(isinstance(s, str) for s in polished):
                return polished
    except Exception:
        pass
    return outputs

from __future__ import annotations

from typing import List, Dict

SIGNAL_REASON_MAP = {
    # 확신형
    "overconfidence": "확정적 표현이 강해 단일 결론으로 닫힐 위험이 있습니다.",
    "single_path_judgment": "하나의 경로만 남기고 다른 가능성을 배제하는 구조가 감지되었습니다.",
    "lack_of_alternatives": "반대 시나리오나 대안 검토가 부족합니다.",
    "repetition_pattern": "같은 결론 구조가 반복되고 있습니다.",
    "intensifier": "감정을 실은 강한 단정 표현이 판단을 밀어붙이고 있습니다.",

    # 편향형
    "group_generalization": "집단 전체를 하나의 성질로 묶는 일반화가 개입되어 있습니다.",
    "hostile_attribution": "상대의 동기를 부정적으로 단정하는 경향이 감지되었습니다.",
    "political_bias_frame": "정치·진영 프레임이 사실 확인보다 먼저 작동하고 있습니다.",

    # 기억형
    "memory_fixation": "과거의 인상이나 기억이 현재 판단의 기준으로 작동하고 있습니다.",
    "counterevidence_block": "반대 증거나 예외 가능성을 차단하는 표현이 포함되어 있습니다.",
    "past_anchor": "과거 평가가 현재 사실보다 먼저 판단 기준으로 쓰이고 있습니다.",
    "current_omission": "현재 확인 가능한 사실보다 해석이나 기억이 앞서고 있습니다.",
    "no_suspension": "판단 유보 없이 바로 결론으로 이동하고 있습니다.",
    "memory_to_conclusion": "과거 인상이 곧바로 현재 결론으로 연결되고 있습니다.",
}

CURRENT_FIRST_REASONS = [
    "현재 확인 가능한 사실을 먼저 분리할 필요가 있습니다.",
    "과거 인상이나 감정보다 현재 정보가 우선되어야 합니다.",
]

SUSPEND_REASONS = [
    "판단을 잠시 유보해야 왜곡을 줄일 수 있습니다.",
]

COMPARE_REASONS = [
    "과거 기억은 기준이 아니라 현재와 비교하는 자료로 사용되어야 합니다.",
]


def build_reasons_from_signals(
    detected_signals: List[str],
    extra: List[str] | None = None,
) -> List[str]:
    reasons: List[str] = []

    for sig in detected_signals:
        mapped = SIGNAL_REASON_MAP.get(sig)
        if mapped and mapped not in reasons:
            reasons.append(mapped)

    if extra:
        for item in extra:
            if item not in reasons:
                reasons.append(item)

    return reasons


def has_memory_order_violation(signals: List[str]) -> bool:
    strong = {"memory_fixation", "counterevidence_block", "past_anchor", "memory_to_conclusion"}
    return len(strong.intersection(set(signals))) >= 2


def get_memory_priority_scenarios(input_text: str, detected_signals: List[str]) -> List[Dict]:
    return [
        {
            "title": "A안 | 현재 사실 우선",
            "summary": "과거 인상과 현재 사실을 분리하고, 지금 확인 가능한 사실을 먼저 봅니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=[
                    "과거 인상이 현재 판단을 선점하고 있습니다.",
                    "현재 사실 확인 없이 결론으로 가는 흐름이 감지되었습니다.",
                    "먼저 현재 사실을 확인한 뒤 과거 기억과 비교해야 합니다.",
                ],
            ),
            "conditions": [
                "현재 사건의 사실관계를 먼저 확인하고 싶을 때",
                "관계보다 사실을 우선하고 싶을 때",
                "기존 인상이 판단을 덮고 있다고 느낄 때",
            ],
        },
        {
            "title": "B안 | 과거-현재 분리",
            "summary": "과거의 좋은 인상과 현재 행동 가능성을 분리해서 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=[
                    "과거 평가는 현재 행동의 면책 근거가 될 수 없습니다.",
                    "기억은 기준이 아니라 비교 자료여야 합니다.",
                    "현재와 과거를 나눠 보아야 변화 여부를 판단할 수 있습니다.",
                ],
            ),
            "conditions": [
                "과거 인상이 강하게 개입되어 있다고 느낄 때",
                "현재와 과거를 따로 판단하고 싶을 때",
                "감정적 방어 대신 비교 검토가 필요할 때",
            ],
        },
        {
            "title": "C안 | 판단 보류",
            "summary": "감정과 기억의 개입을 낮추고 추가 정보 확인 후 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=[
                    "지금 판단은 기억에 의해 급히 닫히고 있습니다.",
                    "유보 단계를 두는 것이 왜곡을 줄입니다.",
                    "현재 정보가 충분해질 때까지 결론을 미루는 것이 안전할 수 있습니다.",
                ],
            ),
            "conditions": [
                "현재 정보가 충분하지 않을 때",
                "감정적으로 방어하려는 느낌이 들 때",
                "추가 확인의 비용이 크지 않을 때",
            ],
        },
    ]


def get_finance_scenarios(input_text: str, detected_signals: List[str]) -> List[Dict]:
    return [
        {
            "title": "A안 | 보수적 접근",
            "summary": "손실 가능성을 먼저 점검하고 진입 조건을 엄격하게 설정합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=CURRENT_FIRST_REASONS + [
                    "금융 판단은 낙관보다 손실 통제가 먼저 필요합니다.",
                ],
            ),
            "conditions": [
                "손실 회피가 가장 중요할 때",
                "변동성이 큰 상황일 때",
                "추가 검증 없이 진입하고 싶지 않을 때",
            ],
        },
        {
            "title": "B안 | 균형 접근",
            "summary": "상승·횡보·하락 시나리오를 함께 비교하며 조건부로 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=SUSPEND_REASONS + [
                    "단일 방향보다 복수 시나리오 비교가 더 적절합니다.",
                ],
            ),
            "conditions": [
                "기회와 위험을 함께 관리하고 싶을 때",
                "단정 대신 조건부 판단을 원할 때",
                "추가 확인을 병행하고 싶을 때",
            ],
        },
        {
            "title": "C안 | 관망 또는 보류",
            "summary": "지금 결론을 내리기보다 정보와 조건이 갖춰질 때까지 보류합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=COMPARE_REASONS + [
                    "현재 정보가 충분하지 않다면 관망도 합리적입니다.",
                ],
            ),
            "conditions": [
                "정보 부족이 클 때",
                "감정 개입이 강할 때",
                "판단을 미뤄도 비용이 크지 않을 때",
            ],
        },
    ]


def get_policy_scenarios(input_text: str, detected_signals: List[str]) -> List[Dict]:
    return [
        {
            "title": "A안 | 부작용 점검",
            "summary": "정책의 의도보다 실제 부작용과 반대 사례를 먼저 검토합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=CURRENT_FIRST_REASONS + [
                    "정책 평가는 찬반보다 실제 효과와 부작용 검토가 우선입니다.",
                ],
            ),
            "conditions": [
                "정책의 현실적 영향이 더 중요할 때",
                "진영 논리보다 결과를 보고 싶을 때",
            ],
        },
        {
            "title": "B안 | 균형 비교",
            "summary": "찬성 논리와 반대 논리를 동시에 놓고 비교합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=SUSPEND_REASONS + [
                    "정치적 판단은 단일 진영 해석보다 복수 관점 비교가 필요합니다.",
                ],
            ),
            "conditions": [
                "한쪽 진영 해석에 치우치고 싶지 않을 때",
                "서로 다른 근거를 함께 보고 싶을 때",
            ],
        },
        {
            "title": "C안 | 추가 검증",
            "summary": "현재 발언이나 정보만으로 결론을 내리지 않고 추가 사실을 확인합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=COMPARE_REASONS + [
                    "정치적 문장은 해석이 빠르게 고착되므로 사실 검증을 추가해야 합니다.",
                ],
            ),
            "conditions": [
                "주장보다 사실 검증이 우선일 때",
                "감정적 반응이 강하게 올라올 때",
            ],
        },
    ]


def get_counseling_scenarios(input_text: str, detected_signals: List[str]) -> List[Dict]:
    return [
        {
            "title": "A안 | 감정 분리",
            "summary": "현재 느끼는 감정과 사실 판단을 먼저 분리합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=CURRENT_FIRST_REASONS + [
                    "감정이 강할수록 현재 사실과 해석을 구분하는 것이 중요합니다.",
                ],
            ),
            "conditions": [
                "감정이 크게 올라온 상태일 때",
                "즉시 결론보다 상태 정리가 먼저 필요할 때",
            ],
        },
        {
            "title": "B안 | 관계 재해석",
            "summary": "상대의 의도 단정 대신 다른 해석 가능성을 함께 검토합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=SUSPEND_REASONS + [
                    "상대의 의도를 단정할수록 관계 판단이 고착되기 쉽습니다.",
                ],
            ),
            "conditions": [
                "상대방 관점을 완전히 배제하고 싶지 않을 때",
                "관계 손상을 줄이고 싶을 때",
            ],
        },
        {
            "title": "C안 | 대화 보류",
            "summary": "즉시 반응하지 않고 상태가 가라앉은 뒤 다시 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=COMPARE_REASONS + [
                    "감정이 강한 상태에선 과거 기억이 현재 판단을 왜곡할 수 있습니다.",
                ],
            ),
            "conditions": [
                "지금 바로 반응하면 악화될 수 있을 때",
                "감정 조절이 먼저 필요할 때",
            ],
        },
    ]


def get_strategy_scenarios(input_text: str, detected_signals: List[str]) -> List[Dict]:
    return [
        {
            "title": "A안 | 리스크 통제",
            "summary": "실행보다 실패 가능성과 자원 손실을 먼저 계산합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=CURRENT_FIRST_REASONS + [
                    "전략 판단은 기대보다 실패 비용을 먼저 보는 것이 안정적입니다.",
                ],
            ),
            "conditions": [
                "실패 비용이 큰 결정일 때",
                "리스크를 먼저 줄이고 싶을 때",
            ],
        },
        {
            "title": "B안 | 조건부 실행",
            "summary": "성공 조건과 실패 조건을 동시에 정의한 뒤 실행 여부를 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=SUSPEND_REASONS + [
                    "단일 낙관 시나리오보다 조건부 실행 구조가 더 견고합니다.",
                ],
            ),
            "conditions": [
                "실행은 하되 통제 장치를 두고 싶을 때",
                "불확실성을 관리하며 추진하고 싶을 때",
            ],
        },
        {
            "title": "C안 | 보류 후 검증",
            "summary": "핵심 가정이 검증될 때까지 전략 결정을 늦춥니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=COMPARE_REASONS + [
                    "전략은 전제 오류 하나로 크게 흔들릴 수 있으므로 보류도 선택지입니다.",
                ],
            ),
            "conditions": [
                "핵심 전제가 검증되지 않았을 때",
                "지금 결정할 필요가 없을 때",
            ],
        },
    ]


def get_general_scenarios(input_text: str, detected_signals: List[str]) -> List[Dict]:
    return [
        {
            "title": "A안 | 현재 사실 우선",
            "summary": "현재 확인 가능한 사실을 먼저 분리하고 해석은 나중으로 미룹니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=CURRENT_FIRST_REASONS + [
                    "지금 결론을 바로 고정하기보다 사실 확인을 우선하는 경로가 적절합니다.",
                ],
            ),
            "conditions": [
                "지금 확인 가능한 정보가 충분할 때",
                "감정보다 사실 검토를 우선하고 싶을 때",
                "기존 인상에서 잠시 떨어져 보고 싶을 때",
            ],
        },
        {
            "title": "B안 | 균형 비교",
            "summary": "하나의 결론을 고정하지 않고 복수 경로를 비교하면서 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=SUSPEND_REASONS + [
                    "하나의 결론 대신 복수 시나리오를 함께 비교하는 것이 더 안정적입니다.",
                ],
            ),
            "conditions": [
                "기회와 위험을 함께 보고 싶을 때",
                "단정 대신 조건부 판단을 원할 때",
                "추가 검토를 병행하며 결론을 좁히고 싶을 때",
            ],
        },
        {
            "title": "C안 | 판단 보류",
            "summary": "현재 정보와 과거 기억을 분리한 뒤 추가 확인 후 판단합니다.",
            "reason": build_reasons_from_signals(
                detected_signals,
                extra=COMPARE_REASONS + [
                    "현재 정보가 충분하지 않다면 판단을 보류하는 경로도 합리적입니다.",
                ],
            ),
            "conditions": [
                "정보 부족이 클 때",
                "감정 개입이 강할 때",
                "지금 당장 결론을 내릴 필요가 없을 때",
            ],
        },
    ]


def get_scenarios(domain: str, input_text: str, detected_signals: List[str]) -> List[Dict]:
    if has_memory_order_violation(detected_signals):
        return get_memory_priority_scenarios(input_text, detected_signals)

    if domain == "finance" or domain == "investment":
        return get_finance_scenarios(input_text, detected_signals)

    if domain == "policy":
        return get_policy_scenarios(input_text, detected_signals)

    if domain == "counseling":
        return get_counseling_scenarios(input_text, detected_signals)

    if domain == "strategy":
        return get_strategy_scenarios(input_text, detected_signals)

    return get_general_scenarios(input_text, detected_signals)


def get_outputs_from_scenarios(scenarios: List[Dict]) -> List[str]:
    return [scenario.get("summary", "") for scenario in scenarios if scenario.get("summary")]
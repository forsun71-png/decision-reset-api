from __future__ import annotations

import requests
import streamlit as st

API_BASE_URL = "https://decision-reset-api.onrender.com"

st.set_page_config(
    page_title="Decision Reset Demo",
    page_icon="🧭",
    layout="centered",
)

st.title("Decision Reset Demo")
st.caption("확신에 갇힌 판단을 깨고, 더 현실적인 판단으로 다시 만들어주는 도구")

with st.sidebar:
    st.header("설정")
    api_base_url = st.text_input("API Base URL", value=API_BASE_URL)
    domain = st.selectbox(
        "도메인",
        ["general", "finance", "policy", "counseling", "strategy"],
        index=1,
    )
    mode = st.selectbox("모드", ["strict", "soft"], index=0)
    source_type = st.selectbox("입력 유형", ["user", "external_ai"], index=0)

examples = [
    "이 종목은 무조건 오른다",
    "이 방법밖에 없다",
    "이 정책이 반드시 맞다",
    "다른 가능성은 전혀 없다",
    "상승 가능성은 있지만 리스크도 있다",
]

selected_example = st.selectbox("예시 문장", ["직접 입력"] + examples)
default_text = "" if selected_example == "직접 입력" else selected_example

st.info("확신하거나 단정적인 문장을 입력해보세요")

input_text = st.text_area(
    "문장을 입력하세요",
    value=default_text,
    height=120,
    placeholder="예: 이 종목은 무조건 오른다",
)

col1, col2 = st.columns(2)
run_analyze = col1.button("문제 확인")
run_reset = col2.button("다시 판단하기", type="primary")


def call_api(endpoint: str, payload: dict) -> tuple[bool, dict]:
    url = f"{api_base_url.rstrip('/')}{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as exc:
        return False, {"error": str(exc), "url": url}


def translate_signal(signal: str) -> str:
    mapping = {
        "overconfidence": "과도한 확신",
        "single_path_judgment": "단일 경로 판단",
        "lack_of_alternatives": "대안 부족",
        "repetition_pattern": "반복 패턴",
        "intensifier": "강한 단정 표현",
    }
    return mapping.get(signal, signal)


payload = {
    "input_text": input_text.strip(),
    "source_type": source_type,
    "domain": domain,
    "mode": mode,
}

if run_analyze or run_reset:
    if not input_text.strip():
        st.warning("먼저 문장을 입력하세요.")
    else:
        endpoint = "/v1/analyze" if run_analyze else "/v1/reset"
        api_payload = payload if run_reset else {
            "input_text": payload["input_text"],
            "source_type": payload["source_type"],
            "domain": payload["domain"],
        }

        ok, data = call_api(endpoint, api_payload)

        if not ok:
            st.error("API 호출에 실패했습니다.")
            st.code(str(data), language="text")
        else:
            st.divider()

            st.subheader("🧠 입력된 판단")
            st.write(input_text)

            if run_analyze:
                st.subheader("분석 결과")

                c1, c2, c3 = st.columns(3)
                c1.metric("고착 감지", "예" if data.get("fixation_detected") else "아니오")
                c2.metric("고착 점수", str(data.get("fixation_score", data.get("score", "-"))))
                c3.metric("개입 트리거", "예" if data.get("intervention_triggered") else "아니오")

                signals = data.get("signals", [])
                if signals:
                    st.subheader("🚨 감지된 문제")
                    for sig in signals:
                        st.write(f"• {translate_signal(sig)}")

                seed = data.get("seed")
                if seed:
                    with st.expander("seed 보기"):
                        st.json(seed)

            if run_reset:
                st.subheader("일부 결과")

                c1, c2, c3 = st.columns(3)
                c1.metric("고착 감지", "예" if data.get("fixation_detected") else "아니오")
                c2.metric("고착 점수", str(data.get("fixation_score", "-")))
                c3.metric("개입 트리거", "예" if data.get("intervention_triggered") else "아니오")

                signals = data.get("detected_signals", [])
                baseline_reset = data.get("baseline_reset", {})
                release_protection = data.get("release_protection", {})
                outputs = data.get("outputs", [])

                if data.get("fixation_detected"):
                    st.warning("👉 이 판단은 확신 또는 단일 결론에 고착된 상태였습니다.")

                if signals:
                    st.subheader("🚨 감지된 문제")
                    for sig in signals:
                        st.write(f"• {translate_signal(sig)}")

                st.subheader("🧩 개입 방식")
                if baseline_reset.get("dependency_cut"):
                    st.write("• 이전 판단 의존성 차단")
                if baseline_reset.get("neutral_state_transition"):
                    st.write("• 중립 상태 전환")
                if release_protection.get("enabled"):
                    st.write("• 재고착 방지 보호 구간 유지")

                st.subheader("✅ 재구성된 판단")
                if outputs:
                    for out in outputs:
                        st.write(f"✔ {out}")
                else:
                    st.info("출력이 비어 있습니다.")

                with st.expander("전체 JSON 보기"):
                    st.json(data)

st.divider()
st.markdown(
    """
### 🔥 바로 테스트해보세요
- 이 종목은 무조건 오른다
- 이 방법밖에 없다
- 이 정책이 반드시 맞다
"""
)

st.caption("변화가 바로 보이는 문장을 넣을수록 이 도구의 차이가 더 잘 드러납니다.")

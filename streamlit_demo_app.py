from __future__ import annotations

import requests
import streamlit as st

API_BASE_URL = "https://decision-reset-api.onrender.com"

st.set_page_config(
    page_title="Decision Reset",
    page_icon="🧭",
    layout="centered",
)

# ── 스타일 ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;600&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans KR', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

h1 {
    font-size: 2rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.03em !important;
    color: #ffffff !important;
    margin-bottom: 0.2rem !important;
}

[data-testid="metric-container"] {
    background: #13131a;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 1rem;
}

[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.4rem !important;
    color: #ffffff !important;
}

[data-testid="stMetricLabel"] {
    color: #6b6b8a !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

.stButton > button {
    background: #13131a !important;
    border: 1px solid #2a2a3a !important;
    color: #e8e8f0 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans KR', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.15s !important;
}

.stButton > button:hover {
    border-color: #4a4a7a !important;
    background: #1a1a2a !important;
}

.stButton > button[kind="primary"] {
    background: #2a2aff !important;
    border-color: #2a2aff !important;
    color: #ffffff !important;
}

.stButton > button[kind="primary"]:hover {
    background: #3a3aff !important;
}

.stTextArea textarea {
    background: #13131a !important;
    border: 1px solid #2a2a3a !important;
    border-radius: 8px !important;
    color: #e8e8f0 !important;
    font-family: 'IBM Plex Sans KR', sans-serif !important;
    font-size: 1rem !important;
}

.stTextArea textarea:focus {
    border-color: #2a2aff !important;
    box-shadow: 0 0 0 2px rgba(42,42,255,0.15) !important;
}

.stSelectbox > div > div {
    background: #13131a !important;
    border: 1px solid #2a2a3a !important;
    border-radius: 6px !important;
    color: #e8e8f0 !important;
}

.before-card {
    background: #1a1015;
    border: 1px solid #3a1a1a;
    border-left: 3px solid #ff4444;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin: 0.5rem 0 1rem 0;
    font-size: 1.05rem;
    line-height: 1.6;
}

.path-card {
    background: #10141c;
    border: 1px solid #24324a;
    border-left: 3px solid #5b8cff;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0 1rem 0;
}

.path-title {
    font-size: 1rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.6rem;
}

.path-summary {
    background: #101a13;
    border: 1px solid #1a3a1a;
    border-left: 3px solid #44ff88;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0 0.8rem 0;
    font-size: 1rem;
    line-height: 1.6;
}

.signal-tag {
    display: inline-block;
    background: #1a1020;
    border: 1px solid #3a1a4a;
    border-radius: 4px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    color: #cc88ff;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-family: 'IBM Plex Mono', monospace;
}

.score-bar-bg {
    background: #1a1a2a;
    border-radius: 4px;
    height: 6px;
    margin: 0.5rem 0 1rem 0;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
}

.rule-item {
    font-size: 0.82rem;
    color: #6b6b8a;
    font-family: 'IBM Plex Mono', monospace;
    padding: 0.15rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
SIGNAL_KO = {
    "overconfidence": "과도한 확신",
    "single_path_judgment": "단일 경로 판단",
    "lack_of_alternatives": "대안 부족",
    "repetition_pattern": "반복 패턴",
    "counter_failure": "반대 가설 생성 실패",
    "intensifier": "강한 단정 표현",
}

FOLLOWUPS = [
    "이 방법밖에 없다",
    "저 사람은 틀렸다",
    "이 선택이 정답이다",
]


def translate_signal(signal: str) -> str:
    return SIGNAL_KO.get(signal, signal)


def call_api(base_url: str, endpoint: str, payload: dict) -> tuple[bool, dict]:
    url = f"{base_url.rstrip('/')}{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as exc:
        return False, {"error": str(exc), "url": url}


def score_color(score: float) -> str:
    if score < 0.35:
        return "#44ff88"
    if score < 0.6:
        return "#ffaa44"
    return "#ff4444"


def normalize_scenarios(data: dict) -> list[dict]:
    scenarios = data.get("scenarios", [])
    if isinstance(scenarios, list) and scenarios:
        return scenarios
    return []


def render_score_bar(score: float) -> None:
    color = score_color(score)
    width = min(max(score * 100, 0), 100)
    st.markdown(
        f"""
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="width:{width:.0f}%; background:{color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("점수가 높을수록 확신/고착 위험이 큽니다.")


def render_signal_tags(signals: list[str]) -> None:
    if not signals:
        return
    tags = " ".join(
        f'<span class="signal-tag">{translate_signal(sig)}</span>' for sig in signals
    )
    st.markdown(f"**감지된 신호** &nbsp; {tags}", unsafe_allow_html=True)


def render_scenario_card(scenario: dict) -> None:
    title = scenario.get("title", "판단 경로")
    summary = scenario.get("summary", "")
    reasons = scenario.get("reason", [])
    conditions = scenario.get("conditions", [])

    st.markdown('<div class="path-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="path-title">{title}</div>', unsafe_allow_html=True)

    if summary:
        st.markdown(
            f'<div class="path-summary">✔ {summary}</div>',
            unsafe_allow_html=True,
        )

    if reasons:
        st.markdown("**왜 이 경로가 나왔는가**")
        for item in reasons:
            st.write(f"- {item}")

    if conditions:
        st.markdown("**언제 이 경로를 선택하는가**")
        for item in conditions:
            st.write(f"- {item}")

    st.markdown("</div>", unsafe_allow_html=True)


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### ⚙️ 설정")
    api_base_url = st.text_input("API URL", value=API_BASE_URL)
    domain = st.selectbox(
        "도메인",
        ["general", "finance", "investment", "policy", "counseling", "strategy"],
        index=1,
    )
    mode = st.selectbox("모드", ["strict", "soft"], index=0)
    source_type = st.selectbox("입력 유형", ["user", "external_ai"], index=0)

# ── 메인 ─────────────────────────────────────────────────────────────────────
st.markdown("# Decision Reset")
st.markdown(
    "<p style='color:#6b6b8a; margin-top:-0.5rem; margin-bottom:1.5rem; font-size:0.95rem;'>"
    "확신에 갇힌 판단을 깨고, 복수의 판단 경로를 이유와 조건과 함께 제시합니다"
    "</p>",
    unsafe_allow_html=True,
)

default_text = st.session_state.get("example_text", "")

st.info("확신하거나 단정적인 문장을 입력해보세요")

input_text = st.text_area(
    "판단 또는 주장을 입력하세요",
    value=default_text,
    height=110,
    placeholder="예: 이 종목은 무조건 오른다",
)

col1, col2 = st.columns(2)
run_analyze = col1.button("🔍 문제 보기", use_container_width=True)
run_reset = col2.button("🧠 판단 리셋", type="primary", use_container_width=True)

# ── 실행 ─────────────────────────────────────────────────────────────────────
if run_analyze or run_reset:
    if not input_text.strip():
        st.warning("먼저 문장을 입력하세요.")
    else:
        endpoint = "/v1/reset"
        payload = {
            "input_text": input_text.strip(),
            "source_type": source_type,
            "domain": domain,
            "mode": mode,
        }

        if run_analyze:
            endpoint = "/v1/analyze"
            payload = {
                "input_text": input_text.strip(),
                "source_type": source_type,
                "domain": domain,
            }

        with st.spinner("분석 중..."):
            ok, data = call_api(api_base_url, endpoint, payload)

        if not ok:
            st.error(f"API 연결 실패: {data.get('error')}")
        else:
            st.divider()

            st.subheader("🧠 입력된 판단")
            st.markdown(
                f'<div class="before-card">⚠️ {input_text.strip()}</div>',
                unsafe_allow_html=True,
            )

            if run_analyze:
                score = data.get("fixation_score", data.get("score", 0.0))
                detected = data.get("fixation_detected", False)
                signals = data.get("signals", [])

                c1, c2, c3 = st.columns(3)
                c1.metric("고착 감지", "감지됨" if detected else "정상")
                c2.metric("고착 점수", f"{score:.2f}")
                c3.metric("권장 조치", "리셋" if detected else "유지")

                render_score_bar(score)
                render_signal_tags(signals)

                if detected:
                    st.warning("👉 이 판단은 확신 또는 단일 결론에 고착된 상태였습니다.")
                else:
                    st.success("👉 이 판단은 현재 고착되지 않은 상태입니다.")
                    st.caption("확신 표현이 낮고, 단일 결론 구조가 강하게 감지되지 않았습니다.")

                with st.expander("상세 데이터"):
                    st.json(data)

            if run_reset:
                score = data.get("fixation_score", 0.0)
                detected = data.get("fixation_detected", False)
                signals = data.get("detected_signals", [])
                baseline_reset = data.get("baseline_reset", {})
                release_protection = data.get("release_protection", {})
                scenarios = normalize_scenarios(data)

                c1, c2, c3 = st.columns(3)
                c1.metric("고착 감지", "감지됨" if detected else "정상")
                c2.metric("고착 점수", f"{score:.2f}")
                c3.metric("개입 여부", "리셋 적용" if detected else "유지")

                render_score_bar(score)
                render_signal_tags(signals)

                st.markdown("### 🔄 판단 변화")

                if detected:
                    st.warning("👉 이 판단은 확신/단일 경로에 고착된 상태였습니다.")
                else:
                    st.success("👉 이 판단은 현재 고착되지 않은 상태입니다. 그래도 복수 경로를 비교해볼 수 있습니다.")
                    st.caption("확신 표현이 낮고, 단일 결론 구조가 강하게 감지되지 않았습니다.")

                st.markdown("### 🧠 재구성된 판단 경로")
                st.caption("아래 경로들은 서로 다른 판단 기준을 반영합니다. 어떤 경로를 선택할지는 당신의 우선순위와 조건에 따라 달라집니다.")

                if scenarios:
                    for scenario in scenarios:
                        render_scenario_card(scenario)
                else:
                    st.info("표시할 판단 경로가 없습니다.")

                if detected:
                    with st.expander("개입 구조 보기"):
                        if baseline_reset.get("dependency_cut"):
                            st.markdown(
                                '<div class="rule-item">✓ dependency_cut — 이전 판단 의존성 차단</div>',
                                unsafe_allow_html=True,
                            )
                        if baseline_reset.get("neutral_state_transition"):
                            st.markdown(
                                '<div class="rule-item">✓ neutral_state_transition — 중립 상태 전환</div>',
                                unsafe_allow_html=True,
                            )
                        if release_protection.get("enabled"):
                            st.markdown(
                                '<div class="rule-item">✓ release_protection — 재고착 방지 구간 활성화</div>',
                                unsafe_allow_html=True,
                            )
                            for rule in release_protection.get("anti_reuse_rules", []):
                                st.markdown(
                                    f'<div class="rule-item" style="padding-left:1rem; color:#4a4a6a;">→ {rule}</div>',
                                    unsafe_allow_html=True,
                                )

                st.markdown("### 👇 당신이 확신하는 다른 생각도 테스트해보세요")
                cols = st.columns(len(FOLLOWUPS))
                for idx, text in enumerate(FOLLOWUPS):
                    if cols[idx].button(text, key=f"followup_{idx}", use_container_width=True):
                        st.session_state["example_text"] = text
                        st.rerun()

                with st.expander("전체 JSON"):
                    st.json(data)

# ── 하단 안내 ────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    """
<p style='color:#3a3a5a; font-size:0.78rem; text-align:center; font-family:"IBM Plex Mono", monospace;'>
Decision Reset API — fixation detection · dependency cut · scenario-based reconstruction
</p>
""",
    unsafe_allow_html=True,
)
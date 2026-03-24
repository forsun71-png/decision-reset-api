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
    font-size: 1.2rem !important;
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
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans KR', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.1rem !important;
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
    font-size: 1.02rem;
    line-height: 1.65;
}

.path-card {
    background: #10141c;
    border: 1px solid #24324a;
    border-left: 3px solid #5b8cff;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.85rem 0 1rem 0;
}

.path-title {
    font-size: 1rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.75rem;
}

.path-summary {
    background: #101a13;
    border: 1px solid #1a3a1a;
    border-left: 3px solid #44ff88;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.45rem 0 0.9rem 0;
    font-size: 1rem;
    line-height: 1.65;
}

.score-bar-bg {
    background: #1a1a2a;
    border-radius: 4px;
    height: 6px;
    margin: 0.55rem 0 0.9rem 0;
    overflow: hidden;
}

.score-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.35s ease;
}

.risk-box {
    background: #111117;
    border: 1px solid #242438;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0 0.8rem 0;
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

# ── 번역 맵 ──────────────────────────────────────────────────────────────────
SIGNAL_KO = {
    "overconfidence": "과도한 확신",
    "single_path_judgment": "단일 경로 판단",
    "lack_of_alternatives": "대안 부족",
    "repetition_pattern": "반복 패턴",
    "intensifier": "강한 단정 표현",
    "group_generalization": "집단 일반화",
    "hostile_attribution": "적대적 동기 단정",
    "political_bias_frame": "정치적 편향 프레임",
    "memory_fixation": "과거 인상 고정",
    "counterevidence_block": "반증 차단",
    "past_anchor": "과거 기억이 현재보다 먼저 작동함",
    "current_omission": "현재 확인 단계가 생략됨",
    "no_suspension": "판단 유보 없이 결론으로 이동함",
    "memory_to_conclusion": "과거 인상이 즉시 결론으로 연결됨",
}

STAGE_KO = {
    "none": "정상",
    "early": "고착 초기",
    "progressing": "고착 진행",
    "deep": "고착 심화",
    "severe": "강한 고착",
}

MODE_KO = {
    "expand": "확장 응답",
    "guide": "유도 응답",
    "step_back": "후퇴",
    "close": "응답 종료",
}

FOLLOWUPS = [
    "이 방법밖에 없다",
    "저 사람은 틀렸다",
    "이 선택이 정답이다",
]

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
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
    st.caption("점수가 높을수록 확신·편향·기억 고착 위험이 큽니다.")


def normalize_scenarios(data: dict) -> list[dict]:
    scenarios = data.get("scenarios", [])
    if isinstance(scenarios, list) and scenarios:
        return scenarios
    return []


def risk_level(count: int) -> str:
    if count == 0:
        return "낮음"
    if count == 1:
        return "주의"
    if count <= 3:
        return "높음"
    return "매우 높음"


def group_signals(signals: list[str]) -> dict:
    groups = {
        "확신 위험": [],
        "편향 위험": [],
        "기억 위험": [],
    }

    confidence = {
        "overconfidence",
        "single_path_judgment",
        "lack_of_alternatives",
        "repetition_pattern",
        "intensifier",
    }
    bias = {
        "group_generalization",
        "hostile_attribution",
        "political_bias_frame",
    }
    memory = {
        "memory_fixation",
        "counterevidence_block",
        "past_anchor",
        "current_omission",
        "no_suspension",
        "memory_to_conclusion",
    }

    for sig in signals:
        if sig in confidence:
            groups["확신 위험"].append(sig)
        elif sig in bias:
            groups["편향 위험"].append(sig)
        elif sig in memory:
            groups["기억 위험"].append(sig)

    return groups


def render_risk_structure(signals: list[str]) -> None:
    grouped = group_signals(signals)
    has_any = any(grouped.values())
    if not has_any:
        return

    st.markdown("### 🚨 감지된 위험 구조")
    for title, items in grouped.items():
        if not items:
            continue
        st.markdown(f"**{title} · {risk_level(len(items))}**")
        st.markdown('<div class="risk-box">', unsafe_allow_html=True)
        for item in items:
            st.write(f"- {translate_signal(item)}")
        st.markdown("</div>", unsafe_allow_html=True)


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


def render_stage_message(stage: str, reset_mode: bool = False) -> None:
    if not reset_mode:
        if stage == "none":
            st.success("👉 현재 판단은 비교적 열려 있습니다.")
        elif stage == "early":
            st.warning("👉 고착이 시작되는 초기 신호가 보입니다.")
        elif stage == "progressing":
            st.warning("👉 고착이 진행 중입니다. 단일 결론으로 닫히고 있습니다.")
        elif stage == "deep":
            st.error("👉 고착이 심화되고 있습니다. 현재보다 기억이나 편향이 먼저 작동합니다.")
        elif stage == "severe":
            st.error("👉 강한 고착 상태입니다. 즉시 판단보다 중단과 재확인이 우선입니다.")
    else:
        if stage == "none":
            st.success("👉 지금은 고착이 거의 없는 상태입니다.")
        elif stage == "early":
            st.warning("👉 고착 초기입니다. 지금 개입하면 더 깊어지기 전에 멈출 수 있습니다.")
        elif stage == "progressing":
            st.warning("👉 고착이 진행 중입니다. 복수 경로 비교가 필요합니다.")
        elif stage == "deep":
            st.error("👉 고착이 심화되었습니다. 과거 기억이나 편향이 현재보다 먼저 작동합니다.")
        elif stage == "severe":
            st.error("👉 강한 고착 상태입니다. 지금은 설명보다 후퇴 또는 종료가 적절할 수 있습니다.")

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
    "고착된 판단을 감지하고, 단계와 응대 모드에 따라 확장·유도·후퇴·종료를 결정합니다"
    "</p>",
    unsafe_allow_html=True,
)

default_text = st.session_state.get("example_text", "")

st.info("확신하거나 단정적인 문장, 또는 열린 질문을 입력해보세요.")

input_text = st.text_area(
    "판단 또는 질문을 입력하세요",
    value=default_text,
    height=110,
    placeholder="예: 이 종목은 무조건 오른다 / 삶이란 무엇일까?",
)

col1, col2 = st.columns(2)
run_analyze = col1.button("🔍 문제 보기", use_container_width=True)
run_reset = col2.button("🧠 응대 보기", type="primary", use_container_width=True)

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
                stage = data.get("fixation_stage", "none")
                signals = data.get("signals", [])

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("고착 감지", "감지됨" if detected else "정상")
                c2.metric("고착 점수", f"{score:.2f}")
                c3.metric("고착 단계", STAGE_KO.get(stage, stage))
                c4.metric("권장 조치", "리셋" if detected else "유지")

                render_score_bar(score)
                render_risk_structure(signals)
                render_stage_message(stage, reset_mode=False)

                with st.expander("상세 데이터"):
                    st.json(data)

            if run_reset:
                score = data.get("fixation_score", 0.0)
                detected = data.get("fixation_detected", False)
                stage = data.get("fixation_stage", "none")
                signals = data.get("detected_signals", [])
                baseline_reset = data.get("baseline_reset", {})
                release_protection = data.get("release_protection", {})
                scenarios = normalize_scenarios(data)
                response_mode = data.get("response_mode", "unknown")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("고착 감지", "감지됨" if detected else "정상")
                c2.metric("고착 점수", f"{score:.2f}")
                c3.metric("고착 단계", STAGE_KO.get(stage, stage))
                c4.metric("개입 여부", "리셋 적용" if detected else "유지")

                render_score_bar(score)
                st.markdown(f"### 🧭 응대 모드: {MODE_KO.get(response_mode, response_mode)}")
                render_risk_structure(signals)
                render_stage_message(stage, reset_mode=True)

                st.markdown("### 🔄 판단 변화")

                if response_mode == "close":
                    st.error("👉 지금은 생산적인 대화가 어렵다고 판단합니다. 여기서 응답을 멈춥니다.")
                    st.caption("공격적이거나 소모적인 상태에서는 더 응답하지 않는 것이 더 이롭습니다.")

                elif response_mode == "step_back":
                    st.warning("👉 지금은 더 설명하기보다 잠시 물러서는 편이 좋습니다.")
                    st.info(
                        "1. 현재 확인 가능한 사실만 따로 적어보세요\n"
                        "2. 과거 인상이나 감정을 잠시 보류하세요\n"
                        "3. 결론은 나중에 다시 보세요"
                    )

                elif response_mode == "expand":
                    st.success("👉 이 질문은 닫힌 판단이 아니라 열린 탐구에 가깝습니다.")
                    st.caption("정답을 고정하기보다 다양한 관점을 함께 비춰보는 방식이 적절합니다.")

                    if scenarios:
                        st.markdown("### 🧠 다양한 관점")
                        for scenario in scenarios:
                            render_scenario_card(scenario)
                    else:
                        st.info("표시할 관점이 없습니다.")

                else:  # guide
                    if detected:
                        st.warning("👉 이 판단은 확신, 편향, 또는 기억 고착이 개입된 상태였습니다.")
                    else:
                        st.success("👉 이 판단은 현재 고착되지 않은 상태입니다. 그래도 복수 경로를 비교해볼 수 있습니다.")

                    st.markdown("### 🧠 재구성된 판단 경로")
                    st.caption("아래 경로들은 서로 다른 판단 기준을 반영합니다. 어떤 경로를 선택할지는 당신의 우선순위와 조건에 따라 달라집니다.")

                    if scenarios:
                        for scenario in scenarios:
                            render_scenario_card(scenario)
                    else:
                        st.info("표시할 판단 경로가 없습니다.")

                if response_mode in ["guide", "expand"]:
                    st.markdown("### 👇 당신이 확신하는 다른 생각도 테스트해보세요")
                    cols = st.columns(len(FOLLOWUPS))
                    for idx, text in enumerate(FOLLOWUPS):
                        if cols[idx].button(text, key=f"followup_{idx}", use_container_width=True):
                            st.session_state["example_text"] = text
                            st.rerun()

                elif response_mode == "step_back":
                    st.markdown("### 👇 지금은 새 결론보다 현재 사실을 다시 적어보는 편이 좋습니다")

                elif response_mode == "close":
                    st.caption("현재 상태에서는 추가 입력보다 대화를 멈추는 것이 적절합니다.")

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

                with st.expander("전체 JSON"):
                    st.json(data)

# ── 하단 안내 ────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    """
<p style='color:#3a3a5a; font-size:0.78rem; text-align:center; font-family:"IBM Plex Mono", monospace;'>
Decision Reset API — fixation detection · fixation stage · response mode routing · scenario-based reconstruction
</p>
""",
    unsafe_allow_html=True,
)
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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;600&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans KR', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }

h1 {
    font-size: 2rem !important; font-weight: 600 !important;
    letter-spacing: -0.03em !important; color: #ffffff !important;
    margin-bottom: 0.2rem !important;
}
h3 { color: #c8c8e0 !important; font-size: 1.05rem !important; margin-top: 1.4rem !important; }

[data-testid="metric-container"] {
    background: #13131a; border: 1px solid #2a2a3a;
    border-radius: 8px; padding: 1rem;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.4rem !important; color: #ffffff !important;
}
[data-testid="stMetricLabel"] {
    color: #6b6b8a !important; font-size: 0.75rem !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
}

.stButton > button {
    background: #13131a !important; border: 1px solid #2a2a3a !important;
    color: #e8e8f0 !important; border-radius: 6px !important;
    font-family: 'IBM Plex Sans KR', sans-serif !important;
    font-size: 0.9rem !important; padding: 0.55rem 1rem !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    border-color: #4a4a7a !important; background: #1a1a2a !important;
}
.stButton > button[kind="primary"] {
    background: #2a2aff !important; border-color: #2a2aff !important; color: #fff !important;
}
.stButton > button[kind="primary"]:hover { background: #3a3aff !important; }

.stTextArea textarea {
    background: #13131a !important; border: 1px solid #2a2a3a !important;
    border-radius: 8px !important; color: #e8e8f0 !important;
    font-family: 'IBM Plex Sans KR', sans-serif !important; font-size: 1rem !important;
}
.stTextArea textarea:focus {
    border-color: #2a2aff !important;
    box-shadow: 0 0 0 2px rgba(42,42,255,0.15) !important;
}
.stSelectbox > div > div {
    background: #13131a !important; border: 1px solid #2a2a3a !important;
    border-radius: 6px !important; color: #e8e8f0 !important;
}

/* 카드 */
.before-card {
    background: #1a1015; border: 1px solid #3a1a1a;
    border-left: 3px solid #ff4444; border-radius: 8px;
    padding: 1.1rem 1.3rem; margin: 0.4rem 0;
    font-size: 1.05rem; line-height: 1.6;
}
.scenario-card {
    background: #101520; border: 1px solid #1e2a3a;
    border-left: 3px solid #2a6aff; border-radius: 8px;
    padding: 1.2rem 1.4rem; margin: 0.8rem 0;
}
.scenario-card-b { border-left-color: #44aaff; }
.scenario-card-c { border-left-color: #44ddaa; }
.scenario-title {
    font-size: 0.78rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #4a8aff;
    font-family: 'IBM Plex Mono', monospace; margin-bottom: 0.5rem;
}
.scenario-title-b { color: #44aaff; }
.scenario-title-c { color: #44ddaa; }
.scenario-summary {
    font-size: 1rem; color: #e8e8f0; line-height: 1.6; margin-bottom: 0.8rem;
}
.scenario-section-label {
    font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: #4a4a6a; font-family: 'IBM Plex Mono', monospace; margin: 0.6rem 0 0.3rem 0;
}
.scenario-item { font-size: 0.88rem; color: #a0a0c0; padding: 0.15rem 0; }

/* 신호 태그 */
.signal-tag {
    display: inline-block; background: #1a1020; border: 1px solid #3a1a4a;
    border-radius: 4px; padding: 0.2rem 0.6rem; font-size: 0.76rem; color: #cc88ff;
    margin: 0.15rem 0.2rem 0.15rem 0; font-family: 'IBM Plex Mono', monospace;
}

/* 점수 바 */
.score-bar-bg {
    background: #1a1a2a; border-radius: 4px;
    height: 6px; margin: 0.5rem 0 1rem 0; overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 4px; }

/* 다음 섹션 */
.next-section {
    background: #0f0f1a; border: 1px solid #1e1e2e;
    border-radius: 10px; padding: 1.1rem 1.3rem; margin-top: 1.5rem;
}
.rule-item {
    font-size: 0.82rem; color: #6b6b8a;
    font-family: 'IBM Plex Mono', monospace; padding: 0.15rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── 상수 ─────────────────────────────────────────────────────────────────────

SIGNAL_KO = {
    "overconfidence":       "과도한 확신",
    "single_path_judgment": "단일 경로 판단",
    "lack_of_alternatives": "대안 부족",
    "repetition_pattern":   "반복 패턴",
    "counter_failure":      "반대 가설 생성 실패",
    "intensifier":          "강한 단정 표현",
}

DOMAIN_FOLLOWUP = {
    "finance":    ("내 투자 판단 테스트", "이 주식은 반드시 오른다"),
    "investment": ("내 투자 판단 테스트", "이 투자는 무조건 성공한다"),
    "policy":     ("내 정치적 확신 테스트", "이 정책이 반드시 맞다"),
    "counseling": ("내 관계 판단 테스트", "저 사람은 분명히 틀렸다"),
    "strategy":   ("내 전략 판단 테스트", "이 방향이 절대적으로 옳다"),
    "general":    ("내 일상 확신 테스트", "이것만이 유일한 방법이다"),
}

CARD_STYLES = [
    ("scenario-card",   "scenario-title",   "A안"),
    ("scenario-card scenario-card-b", "scenario-title scenario-title-b", "B안"),
    ("scenario-card scenario-card-c", "scenario-title scenario-title-c", "C안"),
]


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def translate_signal(s: str) -> str:
    return SIGNAL_KO.get(s, s)


def call_api(base: str, endpoint: str, payload: dict) -> tuple[bool, dict]:
    url = f"{base.rstrip('/')}{endpoint}"
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return True, r.json()
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}


def score_color(score: float) -> str:
    if score < 0.35:
        return "#44ff88"
    if score < 0.6:
        return "#ffaa44"
    return "#ff4444"


def build_path_scenarios_from_legacy(outputs: list[str], signals: list[str]) -> list[dict]:
    """기존 outputs list를 경로형 scenarios로 변환."""
    signal_reasons = [translate_signal(s) for s in signals] if signals else ["고착 신호 감지"]
    base = outputs if outputs else ["추가 정보 확인이 필요합니다."]

    return [
        {
            "title": "A안 | 보수적 접근",
            "summary": base[0] if len(base) > 0 else "리스크 최소화 중심 접근",
            "reason": signal_reasons + ["손실 가능성 또는 과도한 확신을 줄이기 위한 경로"],
            "conditions": [
                "손실 회피가 가장 중요할 때",
                "정보가 아직 충분하지 않을 때",
                "판단에 감정이 섞여 있다고 느껴질 때",
            ],
        },
        {
            "title": "B안 | 균형 접근",
            "summary": base[1] if len(base) > 1 else "기회와 위험을 함께 비교하는 접근",
            "reason": signal_reasons + ["단일 결론보다 복수 시나리오 비교가 더 적절하기 때문"],
            "conditions": [
                "기회와 위험을 함께 관리하고 싶을 때",
                "확정 대신 조건부 판단을 원할 때",
                "추가 확인을 하면서도 판단을 진행하고 싶을 때",
            ],
        },
        {
            "title": "C안 | 관망 또는 보류",
            "summary": base[2] if len(base) > 2 else "판단을 잠시 보류하고 정보 확인을 우선하는 접근",
            "reason": signal_reasons + ["지금 결론을 내리기보다 판단 근거를 더 확인할 필요가 있기 때문"],
            "conditions": [
                "검증 정보가 부족할 때",
                "판단을 미뤄도 비용이 크지 않을 때",
                "감정적 확신이 너무 강하다고 느껴질 때",
            ],
        },
    ]


def normalize_scenarios(data: dict) -> list[dict]:
    """API가 scenarios를 직접 주면 그대로, 아니면 outputs에서 변환."""
    if isinstance(data.get("scenarios"), list) and data["scenarios"]:
        return data["scenarios"]
    outputs = data.get("outputs", [])
    signals = data.get("detected_signals", []) or data.get("signals", [])
    return build_path_scenarios_from_legacy(outputs, signals)


def render_scenario_card(scenario: dict, idx: int) -> None:
    card_cls, title_cls, _ = CARD_STYLES[idx % 3]
    title   = scenario.get("title", f"경로 {idx+1}")
    summary = scenario.get("summary", "")
    reasons = scenario.get("reason", [])
    conds   = scenario.get("conditions", [])

    reasons_html = "".join(f'<div class="scenario-item">• {r}</div>' for r in reasons)
    conds_html   = "".join(f'<div class="scenario-item">• {c}</div>' for c in conds)

    r_block = f'<div class="scenario-section-label">왜 이 경로인가</div>{reasons_html}' if reasons else ""
    c_block = f'<div class="scenario-section-label">언제 선택하는가</div>{conds_html}' if conds else ""

    st.markdown(f"""
    <div class="{card_cls}">
      <div class="{title_cls}">{title}</div>
      <div class="scenario-summary">{summary}</div>
      {r_block}
      {c_block}
    </div>
    """, unsafe_allow_html=True)


def show_followup_section(detected: bool, domain: str) -> None:
    st.markdown("<div class='next-section'>", unsafe_allow_html=True)
    label = "🔁 비슷한 다른 확신도 테스트해보세요" if detected else "👇 다른 확신을 넣어보세요"
    st.markdown(f"#### {label}")

    followups = ["이 방법밖에 없다", "저 사람은 틀렸다", "이 선택이 정답이다"]
    fcols = st.columns(3)
    for i, txt in enumerate(followups):
        if fcols[i].button(txt, key=f"fu_{i}", use_container_width=True):
            st.session_state["example_text"] = txt
            st.rerun()

    dkey = domain if domain in DOMAIN_FOLLOWUP else "general"
    dlabel, dtext = DOMAIN_FOLLOWUP[dkey]
    st.markdown("<p style='color:#4a4a6a; font-size:0.8rem; margin-top:0.8rem;'>다른 영역도 테스트해보세요</p>", unsafe_allow_html=True)
    if st.button(f"→ {dlabel}", key="domain_fu", use_container_width=True):
        st.session_state["example_text"] = dtext
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def show_emotion_tags() -> None:
    st.markdown("<p style='color:#6b6b8a; font-size:0.85rem; margin-top:1.2rem; margin-bottom:0.4rem;'>이 판단에서 가장 강한 감정은 무엇인가요?</p>", unsafe_allow_html=True)
    ecols = st.columns(4)
    for i, em in enumerate(["두려움", "분노", "확신", "불안"]):
        if ecols[i].button(em, key=f"em_{em}", use_container_width=True):
            st.toast(f"'{em}' — 같은 감정이 담긴 다른 확신도 넣어보세요.")


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
    st.divider()
    st.markdown("#### 📌 빠른 테스트")
    for ex in [
        "이 종목은 무조건 오른다",
        "이 방법밖에 없다",
        "이 정책이 반드시 맞다",
        "다른 가능성은 전혀 없다",
        "상승 가능성은 있지만 리스크도 있다",
    ]:
        if st.button(ex, key=f"side_{ex}", use_container_width=True):
            st.session_state["example_text"] = ex
            st.rerun()


# ── 메인 ─────────────────────────────────────────────────────────────────────

st.markdown("# Decision Reset")
st.markdown(
    "<p style='color:#6b6b8a; margin-top:-0.5rem; margin-bottom:1.5rem; font-size:0.95rem;'>"
    "고착된 판단을 감지하고, 복수의 판단 경로로 다시 구성합니다</p>",
    unsafe_allow_html=True,
)

default_text = st.session_state.get("example_text", "")

input_text = st.text_area(
    "판단 또는 주장을 입력하세요",
    value=default_text,
    height=110,
    placeholder="예: 이 종목은 무조건 오른다",
)

col1, col2 = st.columns(2)
run_analyze = col1.button("🔍 고착 확인", use_container_width=True)
run_reset   = col2.button("🧠 판단 리셋", type="primary", use_container_width=True)


# ── 실행 ─────────────────────────────────────────────────────────────────────

if run_analyze or run_reset:
    if not input_text.strip():
        st.warning("먼저 문장을 입력하세요.")
    else:
        if run_analyze:
            endpoint = "/v1/analyze"
            payload  = {"input_text": input_text.strip(), "source_type": source_type, "domain": domain}
        else:
            endpoint = "/v1/reset"
            payload  = {"input_text": input_text.strip(), "source_type": source_type, "domain": domain, "mode": mode}

        with st.spinner("분석 중..."):
            ok, data = call_api(api_base_url, endpoint, payload)

        if not ok:
            st.error(f"API 연결 실패: {data.get('error')}")
        else:
            st.divider()

            # ── 고착 확인 ────────────────────────────────────────────────────
            if run_analyze:
                score    = data.get("fixation_score", data.get("score", 0))
                detected = data.get("fixation_detected", False)
                signals  = data.get("signals", [])

                c1, c2, c3 = st.columns(3)
                c1.metric("고착 감지", "감지됨" if detected else "정상")
                c2.metric("고착 점수", f"{score:.2f}")
                c3.metric("권장 조치", "리셋" if detected else "유지")

                bar_color = score_color(score)
                st.markdown(
                    f'<div class="score-bar-bg"><div class="score-bar-fill" '
                    f'style="width:{min(score*100,100):.0f}%; background:{bar_color};"></div></div>',
                    unsafe_allow_html=True,
                )

                if detected:
                    st.warning("이 판단은 고착 상태입니다. **판단 리셋**을 사용해보세요.")
                    if signals:
                        tags = " ".join(f'<span class="signal-tag">{translate_signal(s)}</span>' for s in signals)
                        st.markdown(f"**감지된 신호** &nbsp; {tags}", unsafe_allow_html=True)
                    show_emotion_tags()
                else:
                    st.success("이 판단은 비교적 균형 잡힌 상태입니다.")

                with st.expander("상세 데이터"):
                    st.json(data)

                show_followup_section(detected, domain)

            # ── 판단 리셋 ────────────────────────────────────────────────────
            if run_reset:
                score    = data.get("fixation_score", 0)
                detected = data.get("fixation_detected", False)
                signals  = data.get("detected_signals", [])
                br       = data.get("baseline_reset", {})
                rp       = data.get("release_protection", {})

                # 메트릭
                c1, c2, c3 = st.columns(3)
                c1.metric("고착 감지", "감지됨" if detected else "정상")
                c2.metric("고착 점수", f"{score:.2f}")
                c3.metric("개입 여부", "리셋 적용" if detected else "유지")

                bar_color = score_color(score)
                st.markdown(
                    f'<div class="score-bar-bg"><div class="score-bar-fill" '
                    f'style="width:{min(score*100,100):.0f}%; background:{bar_color};"></div></div>',
                    unsafe_allow_html=True,
                )

                if signals:
                    tags = " ".join(f'<span class="signal-tag">{translate_signal(s)}</span>' for s in signals)
                    st.markdown(f"**감지된 신호** &nbsp; {tags}", unsafe_allow_html=True)

                # ── Before ───────────────────────────────────────────────────
                st.markdown("### 🔄 판단 변화")
                st.markdown("**입력된 판단**")
                st.markdown(
                    f'<div class="before-card">⚠️ {input_text.strip()}</div>',
                    unsafe_allow_html=True,
                )

                if detected:
                    st.warning("👉 이 판단은 확신/단일 경로에 고착된 상태였습니다.")
                else:
                    st.success("👉 이 판단은 현재 고착되지 않은 상태입니다. 그래도 복수 경로를 비교해볼 수 있습니다.")

                # ── 경로형 After ─────────────────────────────────────────────
                st.markdown("### 🧠 재구성된 판단 경로")
                st.caption("아래 경로들은 서로 다른 판단 기준을 반영합니다. 어떤 경로를 선택할지는 당신의 우선순위와 조건에 따라 달라집니다.")

                scenarios = normalize_scenarios(data)
                for idx, scenario in enumerate(scenarios):
                    render_scenario_card(scenario, idx)

                # 감정 태그
                if detected:
                    show_emotion_tags()

                # 개입 구조
                if detected:
                    with st.expander("개입 구조 보기"):
                        if br.get("dependency_cut"):
                            st.markdown('<div class="rule-item">✓ dependency_cut — 이전 판단 의존성 차단</div>', unsafe_allow_html=True)
                        if br.get("neutral_state_transition"):
                            st.markdown('<div class="rule-item">✓ neutral_state_transition — 중립 상태 전환</div>', unsafe_allow_html=True)
                        if rp.get("enabled"):
                            st.markdown('<div class="rule-item">✓ release_protection — 재고착 방지 구간 활성화</div>', unsafe_allow_html=True)
                            for rule in rp.get("anti_reuse_rules", []):
                                st.markdown(f'<div class="rule-item" style="padding-left:1rem; color:#4a4a6a;">→ {rule}</div>', unsafe_allow_html=True)

                with st.expander("전체 JSON"):
                    st.json(data)

                # 다음 입력 유도
                show_followup_section(detected, domain)

# ── 하단 ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='color:#3a3a5a; font-size:0.78rem; text-align:center; "
    "font-family:\"IBM Plex Mono\", monospace;'>"
    "Decision Reset API — fixation detection · dependency cut · condition-based reconstruction"
    "</p>",
    unsafe_allow_html=True,
)

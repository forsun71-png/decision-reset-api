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
    font-size: 0.9rem !important; padding: 0.6rem 1.2rem !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    border-color: #4a4a7a !important; background: #1a1a2a !important;
}
.stButton > button[kind="primary"] {
    background: #2a2aff !important; border-color: #2a2aff !important;
    color: #ffffff !important;
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

.before-card {
    background: #1a1015; border: 1px solid #3a1a1a;
    border-left: 3px solid #ff4444; border-radius: 8px;
    padding: 1.2rem 1.4rem; margin: 0.5rem 0;
    font-size: 1.05rem; line-height: 1.6;
}
.after-card {
    background: #101a13; border: 1px solid #1a3a1a;
    border-left: 3px solid #44ff88; border-radius: 8px;
    padding: 1.2rem 1.4rem; margin: 0.5rem 0;
    font-size: 1.05rem; line-height: 1.6;
}
.signal-tag {
    display: inline-block; background: #1a1020;
    border: 1px solid #3a1a4a; border-radius: 4px;
    padding: 0.2rem 0.6rem; font-size: 0.78rem; color: #cc88ff;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-family: 'IBM Plex Mono', monospace;
}
.score-bar-bg {
    background: #1a1a2a; border-radius: 4px;
    height: 6px; margin: 0.5rem 0 1rem 0; overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 4px; }
.rule-item {
    font-size: 0.82rem; color: #6b6b8a;
    font-family: 'IBM Plex Mono', monospace; padding: 0.15rem 0;
}
.next-section {
    background: #0f0f1a; border: 1px solid #1e1e2e;
    border-radius: 10px; padding: 1.2rem 1.4rem; margin-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

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


def show_followup_section(detected: bool, domain: str) -> None:
    """결과 아래 반복 입력 유도 섹션."""
    st.markdown("<div class='next-section'>", unsafe_allow_html=True)

    if detected:
        st.markdown("#### 🔁 비슷한 다른 확신도 테스트해보세요")
    else:
        st.markdown("#### 👇 다른 확신을 넣어보세요")

    followups = ["이 방법밖에 없다", "저 사람은 틀렸다", "이 선택이 정답이다"]
    fcols = st.columns(3)
    for i, txt in enumerate(followups):
        if fcols[i].button(txt, key=f"fu_{i}", use_container_width=True):
            st.session_state["example_text"] = txt
            st.rerun()

    # 도메인 기반 버튼
    dkey = domain if domain in DOMAIN_FOLLOWUP else "general"
    dlabel, dtext = DOMAIN_FOLLOWUP[dkey]
    st.markdown("<p style='color:#4a4a6a; font-size:0.8rem; margin-top:0.8rem;'>다른 영역도 테스트해보세요</p>", unsafe_allow_html=True)
    if st.button(f"→ {dlabel}", key="domain_fu", use_container_width=True):
        st.session_state["example_text"] = dtext
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def show_emotion_tags() -> None:
    """고착 감지 시 감정 태그."""
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
    "고착된 판단을 감지하고, 조건 기반으로 다시 구성합니다</p>",
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
                outputs  = data.get("outputs", [])

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

                # Before / After
                st.markdown("### 🔄 판단 변화")
                st.markdown("**Before**")
                st.markdown(f'<div class="before-card">{input_text.strip()}</div>', unsafe_allow_html=True)
                st.markdown("**After**")
                if outputs:
                    after_html = "<br>".join(f"✔ {o}" for o in outputs)
                    st.markdown(f'<div class="after-card">{after_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("출력이 없습니다.")

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
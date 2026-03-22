"""
Decision Reset API — 자동 평가 실행기 (run_eval.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용법:
  # API 서버 먼저 실행
  python run.py

  # 다른 터미널에서 평가 실행
  python tests/run_eval.py

  # 서버 주소 변경 시
  python tests/run_eval.py --base-url http://localhost:8000

옵션:
  --base-url   API 서버 주소 (기본: http://127.0.0.1:8000)
  --cases      테스트 케이스 파일 경로 (기본: tests/test_cases.json)
  --out        리포트 출력 디렉토리 (기본: tests/reports)
  --verbose    각 케이스 상세 출력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ─── HTTP 헬퍼 (외부 의존성 없음) ─────────────────────────────────────────

def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── 단일 케이스 실행 ──────────────────────────────────────────────────────

def run_case(base_url: str, case: dict) -> dict:
    payload = {
        "input_text":  case["input_text"],
        "source_type": case["source_type"],
        "domain":      case["domain"],
        "mode":        case.get("mode", "strict"),
    }

    try:
        analyze = _post(f"{base_url}/v1/analyze", payload)
        reset   = _post(f"{base_url}/v1/reset",   payload)
    except urllib.error.URLError as e:
        return {
            "id": case["id"], "category": case["category"],
            "error": str(e), "passed": False,
        }

    # ── 결과 추출 ──────────────────────────────────────────────────────────
    br = reset.get("baseline_reset", {})
    rp = reset.get("release_protection", {})
    outputs = reset.get("outputs", [])

    uncertainty_hold = any(
        "[UNCERTAINTY_HOLD]" in o for o in outputs
    )

    actual = {
        "fixation_detected":        reset.get("fixation_detected", False),
        "fixation_score":           reset.get("fixation_score", 0.0),
        "intervention_triggered":   reset.get("intervention_triggered", False),
        "baseline_reset_applied":   br.get("applied", False),
        "dependency_cut":           br.get("dependency_cut", False),
        "neutral_state_transition": br.get("neutral_state_transition", False),
        "release_protection_enabled": rp.get("enabled", False),
        "uncertainty_hold":         uncertainty_hold,
        "output_count":             len(outputs),
        "outputs":                  outputs,
        "signals":                  reset.get("detected_signals", []),
        "llm_polish_applied":       reset.get("llm_polish_applied", False),
    }

    # ── 기대값 비교 ────────────────────────────────────────────────────────
    expected = case["expected"]
    failures: list[str] = []

    for field, exp_val in expected.items():
        act_val = actual.get(field)
        if act_val != exp_val:
            failures.append(f"{field}: expected={exp_val}, actual={act_val}")

    # ── 정성 평가 (텍스트 기반) ────────────────────────────────────────────
    qualitative = _qualitative_check(outputs, actual["fixation_detected"])

    passed = len(failures) == 0

    return {
        "id":          case["id"],
        "category":    case["category"],
        "input_text":  case["input_text"],
        "domain":      case["domain"],
        "mode":        case.get("mode", "strict"),
        "passed":      passed,
        "failures":    failures,
        "actual":      actual,
        "qualitative": qualitative,
    }


# ─── 정성 평가 ─────────────────────────────────────────────────────────────

OVERCONFIDENCE_WORDS = ["반드시", "무조건", "100%", "절대", "틀림없이", "확실히"]
ALTERNATIVE_WORDS    = ["반대", "시나리오", "리스크", "대안", "가능성", "실패"]


def _qualitative_check(outputs: list[str], fixation_detected: bool) -> dict:
    if not outputs:
        return {"reuse_detected": False, "has_alternative": False, "overconfidence_reduced": True}

    text = " ".join(outputs)

    reuse_detected       = False   # 기존 결론 그대로 반복 여부 (수동 확인 필요)
    has_alternative      = any(w in text for w in ALTERNATIVE_WORDS)
    overconfidence_found = any(w in text for w in OVERCONFIDENCE_WORDS)

    return {
        "reuse_detected":        reuse_detected,
        "has_alternative":       has_alternative,
        "overconfidence_reduced": not overconfidence_found,
        "note": "reuse_detected는 수동 확인 필요" if fixation_detected else "",
    }


# ─── 리포트 생성 ───────────────────────────────────────────────────────────

def build_report(results: list[dict]) -> dict:
    total   = len(results)
    passed  = sum(1 for r in results if r["passed"])
    failed  = total - passed
    errors  = sum(1 for r in results if "error" in r)

    by_category: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if r["passed"]:
            by_category[cat]["passed"] += 1

    failed_cases = [
        {
            "id":       r["id"],
            "category": r["category"],
            "input":    r.get("input_text", ""),
            "failures": r.get("failures", []),
            "error":    r.get("error", ""),
        }
        for r in results if not r["passed"]
    ]

    qual_issues = [
        {
            "id":    r["id"],
            "input": r.get("input_text", ""),
            "issue": r.get("qualitative", {}),
        }
        for r in results
        if r.get("actual", {}).get("fixation_detected")
        and not r.get("qualitative", {}).get("has_alternative", True)
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total":  total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{passed/total*100:.1f}%" if total else "0%",
        },
        "by_category": {
            cat: f"{v['passed']}/{v['total']}"
            for cat, v in by_category.items()
        },
        "failed_cases":  failed_cases,
        "qualitative_issues": qual_issues,
        "all_results":   results,
    }


def print_summary(report: dict) -> None:
    s = report["summary"]
    print("\n" + "━" * 50)
    print("  Decision Reset API — 평가 결과")
    print("━" * 50)
    print(f"  총 테스트 : {s['total']}")
    print(f"  성공      : {s['passed']}")
    print(f"  실패      : {s['failed']}")
    print(f"  오류      : {s['errors']}")
    print(f"  통과율    : {s['pass_rate']}")
    print()
    print("  [카테고리별]")
    for cat, score in report["by_category"].items():
        print(f"  {cat:<20} {score}")

    if report["failed_cases"]:
        print()
        print("  [실패 케이스]")
        for fc in report["failed_cases"]:
            if fc["error"]:
                print(f"  {fc['id']} — ERROR: {fc['error']}")
            else:
                for f in fc["failures"]:
                    print(f"  {fc['id']} — {f}")

    if report["qualitative_issues"]:
        print()
        print("  [정성 평가 주의]")
        for qi in report["qualitative_issues"]:
            print(f"  {qi['id']} — 반대 시나리오 부족: {qi['input'][:40]}")

    print("━" * 50 + "\n")


def print_verbose(result: dict) -> None:
    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"\n  {status}  [{result['id']}] {result['category']}")
    print(f"  입력: {result.get('input_text', '')[:60]}")
    if "error" in result:
        print(f"  오류: {result['error']}")
        return
    a = result.get("actual", {})
    print(f"  fixation_detected={a.get('fixation_detected')}  "
          f"score={a.get('fixation_score')}  "
          f"signals={a.get('signals')}")
    print(f"  intervention={a.get('intervention_triggered')}  "
          f"baseline_reset={a.get('baseline_reset_applied')}  "
          f"llm_polish={a.get('llm_polish_applied')}")
    print(f"  outputs ({a.get('output_count')}):")
    for i, o in enumerate(a.get("outputs", []), 1):
        print(f"    {i}. {o}")
    if result["failures"]:
        print(f"  실패 이유: {result['failures']}")


# ─── 메인 ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Decision Reset API Evaluator")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--cases",    default="tests/test_cases.json")
    parser.add_argument("--out",      default="tests/reports")
    parser.add_argument("--verbose",  action="store_true")
    args = parser.parse_args()

    # ── 서버 헬스 체크 ──────────────────────────────────────────────────────
    try:
        with urllib.request.urlopen(f"{args.base_url}/health", timeout=5) as r:
            pass
    except Exception:
        print(f"\n❌ 서버에 연결할 수 없습니다: {args.base_url}")
        print("   python run.py 로 서버를 먼저 실행하세요.\n")
        sys.exit(1)

    # ── 케이스 로드 ─────────────────────────────────────────────────────────
    cases_path = Path(args.cases)
    if not cases_path.exists():
        print(f"❌ 테스트 케이스 파일 없음: {cases_path}")
        sys.exit(1)

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    print(f"\n  총 {len(cases)}개 케이스 평가 시작 ({args.base_url})")

    # ── 실행 ────────────────────────────────────────────────────────────────
    results: list[dict] = []
    for i, case in enumerate(cases, 1):
        print(f"  [{i:02d}/{len(cases)}] {case['id']} ... ", end="", flush=True)
        result = run_case(args.base_url, case)
        results.append(result)
        print("✅" if result["passed"] else "❌")
        if args.verbose:
            print_verbose(result)

    # ── 리포트 생성 ─────────────────────────────────────────────────────────
    report = build_report(results)
    print_summary(report)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"results_{ts}.json"
    md_path   = out_dir / "latest_summary.md"
    latest_path = out_dir / "latest_results.json"

    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Markdown 요약 ────────────────────────────────────────────────────────
    s = report["summary"]
    md_lines = [
        "# Decision Reset API — 평가 요약",
        f"\n생성: {report['generated_at']}",
        f"\n## 결과\n",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 총 테스트 | {s['total']} |",
        f"| 성공 | {s['passed']} |",
        f"| 실패 | {s['failed']} |",
        f"| 통과율 | {s['pass_rate']} |",
        f"\n## 카테고리별\n",
        "| 카테고리 | 결과 |",
        "|----------|------|",
    ]
    for cat, score in report["by_category"].items():
        md_lines.append(f"| {cat} | {score} |")

    if report["failed_cases"]:
        md_lines.append("\n## 실패 케이스\n")
        for fc in report["failed_cases"]:
            md_lines.append(f"- **{fc['id']}**: {', '.join(fc['failures'] or [fc['error']])}")

    if report["qualitative_issues"]:
        md_lines.append("\n## 정성 평가 주의\n")
        for qi in report["qualitative_issues"]:
            md_lines.append(f"- **{qi['id']}**: 반대 시나리오 부족")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"  리포트 저장: {json_path}")
    print(f"  요약 저장:   {md_path}\n")


if __name__ == "__main__":
    main()

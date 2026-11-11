"""eval/results/ 의 결과 JSON을 설정별로 비교하는 표를 만든다 (설정마다 가장 최근 결과 사용).

사용: python eval/compare.py
"""

import json
import sys
from pathlib import Path
from typing import Any

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def latest_per_config() -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[str, dict[str, Any]]] = {}
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data["meta"]["config"]
        latest[name] = (path.name, data)
    return {name: data for name, (_, data) in latest.items()}


def summarize(records: list[dict[str, Any]]) -> dict[str, str]:
    with_expected = [r for r in records if r["hit"] is not None]
    hits = [r for r in with_expected if r["hit"]]
    top1 = [r for r in hits if r["hit_rank"] == 1]
    answerable = [r for r in records if r["expected_behavior"] == "answer"]
    cited = [r for r in answerable if r["cited"]]
    no_answer = [r for r in records if r["expected_behavior"] in ("inquiry", "scope")]
    inquiry_ok = [
        r for r in no_answer if r["mentions_inquiry"] or r["expected_behavior"] == "scope"
    ]
    n = len(records)
    return {
        "검색 적중(top-3)": f"{len(hits)}/{len(with_expected)}",
        "1순위 적중": f"{len(top1)}/{len(with_expected)}",
        "답변형 출처 표기": f"{len(cited)}/{len(answerable)}",
        "답변불가형 문의 안내": f"{len(inquiry_ok)}/{len(no_answer)}",
        "평균 응답(초)": f"{sum(r['latency_s'] for r in records) / n:.2f}",
        "평균 입력 토큰": f"{sum(r['input_tokens'] for r in records) / n:.0f}",
        "평균 출력 토큰": f"{sum(r['output_tokens'] for r in records) / n:.0f}",
    }


def main() -> None:
    results = latest_per_config()
    if not results:
        sys.stdout.write("results/ 에 결과가 없어요.\n")
        return
    summaries = {name: summarize(d["records"]) for name, d in results.items()}
    names = list(summaries)
    rows = list(next(iter(summaries.values())))
    lines = ["| 지표 | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for row in rows:
        lines.append(f"| {row} | " + " | ".join(summaries[n][row] for n in names) + " |")

    # 설정 간 검색 결과가 달라진 질문만 따로 보여 준다
    first = results[names[0]]["records"]
    diffs = ["", "### 검색 결과가 설정마다 다른 질문", ""]
    for i, rec in enumerate(first):
        sets = {n: results[n]["records"][i]["hit"] for n in names}
        if len(set(sets.values())) > 1:
            marks = ", ".join(f"{n}={'O' if v else 'X'}" for n, v in sets.items())
            diffs.append(f"- {rec['id']} {rec['question']} → {marks}")
    text = "\n".join(lines + diffs) + "\n"
    (RESULTS_DIR / "comparison.md").write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()

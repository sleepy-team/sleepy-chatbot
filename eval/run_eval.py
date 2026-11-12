"""개발용 평가 세트를 설정 파일 하나로 실행해 결과를 eval/results/ 에 저장한다.

사용 (backend/ 에서): uv run python ../eval/run_eval.py ../configs/rag/hybrid-v1.yaml
정답/부분 정답/오답/근거 없는 답변 분류는 CSV의 grade 칸을 사람이 채운다.
"""

import argparse
import asyncio
import csv
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent / "backend"))  # rag 패키지를 import하기 위해

from langchain_core.callbacks import UsageMetadataCallbackHandler  # noqa: E402

from rag_so.chain import create_pipeline  # noqa: E402
from rag_so.config import load_config  # noqa: E402

QUESTIONS_PATH = EVAL_DIR / "dev_questions.json"
RESULTS_DIR = EVAL_DIR / "results"
CITATION_RE = re.compile(r"\[출처:\s*([^\]]+)\]")
INQUIRY_RE = re.compile(r"고객센터|1:1|문의|상담")
CSV_FIELDS = [
    "id",
    "category",
    "question",
    "expected_behavior",
    "expected_sources",
    "retrieved",
    "hit",
    "hit_rank",
    "answer",
    "cited",
    "mentions_inquiry",
    "latency_s",
    "input_tokens",
    "output_tokens",
    "grade",
    "note",
]


def hit_info(expected: list[str], retrieved: list[str]) -> tuple[bool | None, int | None]:
    if not expected:
        return None, None
    ranks = [retrieved.index(e) + 1 for e in expected if e in retrieved]
    return (True, min(ranks)) if ranks else (False, None)


async def run(config_path: str) -> Path:
    config = load_config(config_path)
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]
    pipeline = await create_pipeline(config)

    records: list[dict[str, Any]] = []
    for item in questions:
        usage = UsageMetadataCallbackHandler()
        start = time.perf_counter()
        response = await pipeline.agenerate(item["question"], run_config={"callbacks": [usage]})
        latency = time.perf_counter() - start

        retrieved = [d.metadata.get("source_label", "") for d in response.sources]
        hit, rank = hit_info(item["expected_sources"], retrieved)
        totals = list(usage.usage_metadata.values())
        records.append(
            {
                **item,
                "retrieved": retrieved,
                "hit": hit,
                "hit_rank": rank,
                "answer": response.answer,
                "cited": [
                    c.strip() for m in CITATION_RE.findall(response.answer) for c in m.split(",")
                ],
                "mentions_inquiry": bool(INQUIRY_RE.search(response.answer)),
                "latency_s": round(latency, 2),
                # 질문 임베딩 토큰은 포함되지 않는다 (LLM 호출분만)
                "input_tokens": sum(u.get("input_tokens", 0) for u in totals),
                "output_tokens": sum(u.get("output_tokens", 0) for u in totals),
                "grade": "",
                "note": "",
            }
        )

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = RESULTS_DIR / f"{config.name}-{stamp}"
    meta = {
        "config": config.name,
        "config_path": str(config_path),
        "embedding_model": config.embedding.model,
        "llm_model": config.llm.model,
        "retrieval": config.retrieval.model_dump(),
        "ran_at": stamp,
    }
    base.with_suffix(".json").write_text(
        json.dumps({"meta": meta, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with base.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow({k: ", ".join(v) if isinstance(v, list) else v for k, v in r.items()})
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description="개발용 평가 세트 실행")
    parser.add_argument("config", help="configs/rag/ 아래 YAML 경로")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    base = asyncio.run(run(args.config))
    sys.stdout.write(f"저장: {base}.json / {base}.csv\n")


if __name__ == "__main__":
    main()

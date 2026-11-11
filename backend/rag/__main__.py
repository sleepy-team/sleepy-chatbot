"""CLI: 인덱스를 구축한 뒤 질문을 실행한다.

사용: uv run python -m rag [--config 경로] "질문1" "질문2"
"""

import argparse
import asyncio
import logging
import sys

from rag.chain import create_pipeline
from rag.config import load_config


async def run(config_path: str | None, questions: list[str]) -> None:
    config = load_config(config_path)
    pipeline = await create_pipeline(config)
    out = sys.stdout
    out.write(
        f"설정: {config.name} | 임베딩: {config.embedding.model} | LLM: {config.llm.model}"
        f" | 검색: {config.retrieval.method}\n"
    )
    for question in questions:
        response = await pipeline.agenerate(question)
        out.write(f"\n질문: {question}\n답변: {response.answer}\n검색된 문서:\n")
        for doc in response.sources:
            score = doc.metadata.get("score")
            score_text = f" (score={score:.3f})" if score is not None else ""
            out.write(f"  - {doc.metadata.get('source_label')}{score_text}\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="rag")
    parser.add_argument("--config", default=None, help="configs/rag/ 아래 YAML 경로")
    parser.add_argument("questions", nargs="+")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run(args.config, args.questions))


if __name__ == "__main__":
    main()

"""data/ 의 JSON을 Document로 변환한다. 파일 수·항목 수·문구에 의존하지 않는다."""

import json
import logging
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

QUESTION_KEYS = ("question", "q", "질문")
ANSWER_KEYS = ("answer", "a", "답변")
ID_KEYS = ("id", "number", "no", "faq_id")
TITLE_KEYS = ("title", "name", "제목")
TEXT_KEYS = ("content", "text", "body", "본문")
SKIPPED_STATUSES = {"pending"}
# 원본에 실제로 있을 때만 메타데이터로 옮기는 플래그
FLAG_KEYS = ("company_provided", "support_required")


def _pick(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _collect_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if not isinstance(data, dict):
        return []
    if _pick(data, QUESTION_KEYS) or _pick(data, TEXT_KEYS):
        return [data]
    records: list[dict[str, Any]] = []
    for value in data.values():
        if isinstance(value, list):
            records.extend(r for r in value if isinstance(r, dict))
    return records


def _faq_label(raw_id: Any) -> str:
    text = str(raw_id).strip()
    return f"FAQ {text}" if text.upper().startswith("Q") else f"FAQ Q{text}"


def _record_to_document(record: dict[str, Any], file_name: str) -> Document | None:
    if str(record.get("status", "")).lower() in SKIPPED_STATUSES:
        return None
    flags = {k: record[k] for k in FLAG_KEYS if k in record}
    category = record.get("category")

    question, answer = _pick(record, QUESTION_KEYS), _pick(record, ANSWER_KEYS)
    if question is not None:
        if answer is None:
            return None  # 답변이 비어 있으면 인덱싱하지 않는다
        raw_id = _pick(record, ID_KEYS)
        label = _faq_label(raw_id) if raw_id is not None else f"FAQ {question}"
        metadata = {
            "doc_type": "faq",
            "source_label": label,
            "source_file": file_name,
            "category": category,
            "question": str(question),
            **flags,
        }
        return Document(page_content=f"질문: {question}\n답변: {answer}", metadata=metadata)

    text = _pick(record, TEXT_KEYS)
    if text is not None:
        title = _pick(record, TITLE_KEYS) or Path(file_name).stem
        metadata = {
            "doc_type": "product",
            "source_label": str(title),
            "source_file": file_name,
            "category": category,
            **flags,
        }
        return Document(page_content=str(text), metadata=metadata)
    return None


def load_documents(data_dir: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(data_dir.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        for record in _collect_records(data):
            doc = _record_to_document(record, path.name)
            if doc is not None:
                documents.append(doc)
    logger.info("문서 %d개 로드 (%s)", len(documents), data_dir)
    return documents

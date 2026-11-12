"""대화 흐름: RAG 호출, 답변 유형 판별, 로그 기록."""

import logging
import re
import time
import uuid
from typing import Protocol

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig

from app.repositories.chat_log_repository import ChatLogRepository
from app.schemas.chat import ChatMessage, ChatMode, ChatResponse, SourceItem
from rag.chain import RAGResponse

logger = logging.getLogger(__name__)

EXCERPT_LENGTH = 200
CITATION_RE = re.compile(r"\[출처:")
INQUIRY_RE = re.compile(r"고객센터|1:1|상담원")
OFFTOPIC_RE = re.compile(r"관련 없")


class RAGPipelineLike(Protocol):
    async def agenerate(
        self,
        query: str,
        run_config: RunnableConfig | None = None,
        history: list[tuple[str, str]] | None = None,
    ) -> RAGResponse: ...


def classify_answer(answer: str) -> tuple[ChatMode, bool]:
    """답변 문구로 유형을 추정한다. 프롬프트가 구조화 출력을 내도록 바뀌면 대체한다."""
    cited = bool(CITATION_RE.search(answer))
    needs_inquiry = bool(INQUIRY_RE.search(answer))
    if cited:
        return ("partial" if needs_inquiry else "answer"), needs_inquiry
    if OFFTOPIC_RE.search(answer):
        return "offtopic", False
    return "unknown", True


def resolve_mode(response: RAGResponse) -> tuple[ChatMode, bool]:
    """모델이 유형을 직접 냈으면 그 값을 쓰고, 아니면 답변 문구로 추정한다."""
    if response.mode is None:
        return classify_answer(response.answer)
    mode: ChatMode = response.mode
    # 답했더라도 고객센터 문의를 함께 안내했다면 문의 버튼을 보여 준다
    if mode == "answer" and INQUIRY_RE.search(response.answer):
        mode = "partial"
    return mode, mode in ("partial", "unknown")


def to_source_item(doc: Document) -> SourceItem:
    meta = doc.metadata
    return SourceItem(
        label=str(meta.get("source_label", "")),
        title=str(meta.get("question") or meta.get("source_label", "")),
        excerpt=doc.page_content[:EXCERPT_LENGTH],
        score=meta.get("score"),
    )


class ChatService:
    def __init__(
        self,
        pipeline: RAGPipelineLike,
        repository: ChatLogRepository,
        config_name: str,
        history_turns: int = 0,
    ) -> None:
        self._pipeline = pipeline
        self._repository = repository
        self._config_name = config_name
        self._history_turns = history_turns

    async def _load_history(self, session_id: str) -> list[tuple[str, str]] | None:
        """같은 세션의 최근 대화. 초기화한 대화와 다른 세션은 포함하지 않는다."""
        if self._history_turns <= 0:
            return None
        messages = await self._repository.list_by_session(session_id)
        recent = messages[-self._history_turns :]
        return [(m.question, m.answer) for m in recent] or None

    async def ask(self, message: str, session_id: str | None) -> ChatResponse:
        session_id = session_id or uuid.uuid4().hex
        history = await self._load_history(session_id)
        usage = UsageMetadataCallbackHandler()
        start = time.perf_counter()
        response = await self._pipeline.agenerate(
            message, run_config={"callbacks": [usage]}, history=history
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        mode, needs_inquiry = resolve_mode(response)
        # 모델이 인용한 문서만 화면에 보여 준다 (구조화 출력이 아니면 검색된 전체)
        shown = response.cited_sources if response.cited_sources is not None else response.sources
        sources = [to_source_item(d) for d in shown]
        totals = list(usage.usage_metadata.values())
        await self._repository.add(
            session_id=session_id,
            question=message,
            answer=response.answer,
            mode=mode,
            needs_inquiry=needs_inquiry,
            sources=sources,
            latency_ms=latency_ms,
            input_tokens=sum(u.get("input_tokens", 0) for u in totals),
            output_tokens=sum(u.get("output_tokens", 0) for u in totals),
            config_name=self._config_name,
        )
        return ChatResponse(
            session_id=session_id,
            answer=response.answer,
            mode=mode,
            needs_inquiry=needs_inquiry,
            sources=sources,
            latency_ms=latency_ms,
        )

    async def history(self, session_id: str) -> list[ChatMessage]:
        return await self._repository.list_by_session(session_id)

    async def reset(self, session_id: str) -> None:
        count = await self._repository.reset_session(session_id)
        logger.info("세션 %s 초기화 (%d건)", session_id, count)

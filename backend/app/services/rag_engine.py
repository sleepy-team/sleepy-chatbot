"""RAG 엔진 선택과 어댑터.

챗봇 서비스(ChatService)는 `agenerate(query, run_config, history) -> RAGResponse` 하나만 안다.
엔진마다 응답 형식이 달라서, 팀 채택 엔진(rag.pipeline.RagPipeline)은 어댑터로 그 형태에 맞춘다.

- team(기본): 팀이 채택한 RAG (configs/rag/default.yaml).
  임베딩 4 + 키워드 1 검색, 용어 사전, 판단과 답변을 LLM 1회로 처리
- so: 이 저장소에서 실험한 RAG (rag_so, configs/rag/hybrid-v*.yaml)
"""

import logging
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig

from app.core.config import Settings
from app.services.chat_service import RAGPipelineLike
from rag.schemas import RagResponse as TeamResponse
from rag.schemas import Source
from rag_so.chain import RAGResponse

logger = logging.getLogger(__name__)


def source_label(faq_id: str) -> str:
    """화면의 출처 칩에 보일 이름. FAQ는 'FAQ Q01', 제품 정보는 '제품 정보 P01'."""
    return f"FAQ {faq_id}" if faq_id.upper().startswith("Q") else f"제품 정보 {faq_id}"


def to_document(source: Source) -> Document:
    return Document(
        page_content=source.excerpt,
        metadata={
            "source_label": source_label(source.faq_id),
            "question": source.title,
            "category": source.category,
            "score": source.score,
        },
    )


def to_rag_response(team: TeamResponse) -> RAGResponse:
    """팀 엔진 응답을 서비스가 쓰는 형태로 바꾼다. greeting은 화면에서 chitchat으로 다룬다."""
    documents = [to_document(s) for s in team.sources]
    return RAGResponse(
        answer=team.answer,
        sources=documents,
        mode="chitchat" if team.mode == "greeting" else team.mode,
        cited_sources=documents,  # 팀 엔진의 sources는 답변이 인용한 FAQ만 담는다
        show_contact=team.show_contact,
        prompt_tokens=team.prompt_tokens,
        completion_tokens=team.completion_tokens,
    )


class TeamRagAdapter:
    """팀 RagPipeline을 RAGPipelineLike로 감싼다."""

    def __init__(self, pipeline) -> None:  # noqa: ANN001  (rag.pipeline.RagPipeline)
        self._pipeline = pipeline

    async def agenerate(
        self,
        query: str,
        run_config: RunnableConfig | None = None,
        history: list[tuple[str, str]] | None = None,
    ) -> RAGResponse:
        # 팀 계약의 history는 앞선 '질문' 목록이다. 몇 개를 쓸지는 팀 설정(history_turns)이 정한다
        previous = [question for question, _ in history or []]
        return to_rag_response(await self._pipeline.aanswer(query, previous))

    def close(self) -> None:
        self._pipeline.close()


@dataclass
class Engine:
    pipeline: RAGPipelineLike
    name: str
    history_turns: int
    close: object = None  # 종료할 때 부를 함수 (없으면 None)


async def build_engine(settings: Settings) -> Engine:
    if settings.rag_engine == "so":
        from rag_so.chain import create_pipeline
        from rag_so.config import load_config

        config = load_config()  # RAG_CONFIG 환경변수가 없으면 hybrid-v1
        return Engine(await create_pipeline(config), f"so-{config.name}", config.history_turns)

    from rag.config import load_config as load_team_config
    from rag.pipeline import RagPipeline

    team_config = load_team_config(settings.team_rag_config)
    adapter = TeamRagAdapter(RagPipeline(team_config))
    return Engine(
        adapter, f"team-{team_config.name}", team_config.retrieval.history_turns, adapter.close
    )

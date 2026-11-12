"""LCEL 체인과 메인 함수 generate_rag_response."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field, SecretStr

from rag.config import RagConfig, get_openai_api_key, load_config
from rag.loaders import load_documents
from rag.prompts import format_context, format_history, load_prompt
from rag.retrievers import build_retriever
from rag.splitters import split_documents
from rag.vectorstore import build_index, create_client

logger = logging.getLogger(__name__)

# "그건 어디에 문의해요?"처럼 짧은 후속 질문은 직전 질문을 붙여 검색한다
SHORT_FOLLOW_UP_LENGTH = 25

AnswerMode = Literal["answer", "partial", "unknown", "offtopic", "chitchat", "clarify"]


class StructuredAnswer(BaseModel):
    """answer_format: structured 일 때 모델이 내는 값. 유형 판별 규칙은 시스템 프롬프트에 있다."""

    mode: AnswerMode = Field(
        description="답변 유형: answer, partial, unknown, offtopic, chitchat, clarify 중 하나"
    )
    answer: str = Field(
        description="고객에게 그대로 보여 줄 답변 본문 ([출처: ...] 표시는 쓰지 않는다)"
    )
    used_sources: list[str] = Field(
        default_factory=list,
        description="답변에 실제로 사용한 [참고 자료]의 출처 라벨 목록. 사용하지 않았으면 빈 목록",
    )


@dataclass
class RAGResponse:
    answer: str
    sources: list[Document]
    mode: AnswerMode | None = None  # structured 일 때만 값이 있다
    # 답변에 실제로 인용한 문서. structured 일 때만 값이 있고(인용이 없으면 빈 목록),
    # sources(검색된 전체)는 평가를 위해 그대로 둔다
    cited_sources: list[Document] | None = None


def build_retrieval_query(
    query: str,
    history: list[tuple[str, str]] | None,
    synonyms: dict[str, str] | None = None,
) -> str:
    """검색용 질문을 만든다 (LLM 호출 없음).

    짧은 후속 질문에는 직전 질문을 붙이고, 설정의 구어·오타 사전으로 표준어로 바꾼다.
    """
    if history and len(query) <= SHORT_FOLLOW_UP_LENGTH:
        query = f"{history[-1][0]} {query}"
    for wrong, standard in (synonyms or {}).items():
        query = query.replace(wrong, standard)
    return query


def valid_source_labels(result: StructuredAnswer, sources: list[Document]) -> list[str]:
    """모델이 낸 출처 라벨 중 실제로 검색된 문서의 라벨만 순서대로 남긴다."""
    retrieved = {doc.metadata.get("source_label") for doc in sources}
    return list(dict.fromkeys(label for label in result.used_sources if label in retrieved))


def resolve_mode(result: StructuredAnswer, sources: list[Document]) -> AnswerMode:
    """검색된 자료를 근거로 답했는데 근거 없는 유형으로 표시한 모순을 바로잡는다.

    예: 보증 내용을 답하면서 mode를 offtopic으로 낸 경우. 인사·범위 밖·되묻기는 출처를 쓰지 않는다.
    """
    if result.mode in ("offtopic", "chitchat", "clarify") and valid_source_labels(result, sources):
        return "answer"
    return result.mode


def append_citation(result: StructuredAnswer, sources: list[Document]) -> str:
    """답변 유형이 근거 답변이면 검증된 출처 라벨을 답변 끝에 붙인다."""
    if resolve_mode(result, sources) not in ("answer", "partial"):
        return result.answer
    labels = valid_source_labels(result, sources)
    if not labels:
        return result.answer
    return f"{result.answer.rstrip()}\n\n[출처: {', '.join(labels)}]"


@dataclass
class RAGPipeline:
    config: RagConfig
    retriever: BaseRetriever
    chain: Runnable[dict[str, Any], Any]

    async def agenerate(
        self,
        query: str,
        run_config: RunnableConfig | None = None,
        history: list[tuple[str, str]] | None = None,
    ) -> RAGResponse:
        """run_config는 평가 시 토큰 사용량 콜백 등을 전달하기 위한 값이다.

        history는 같은 세션의 이전 (질문, 답변) 목록이다. history_turns가 0이면 무시한다.
        """
        turns = self.config.history_turns
        history = history[-turns:] if history and turns > 0 else None

        retrieval_query = build_retrieval_query(
            query, history, self.config.retrieval.query_synonyms
        )
        found = await self.retriever.ainvoke(retrieval_query)
        sources = found[: self.config.retrieval.top_k]
        result = await self.chain.ainvoke(
            {
                "context": format_context(sources),
                "question": query,
                "history": format_history(history),
            },
            config=run_config,
        )
        if isinstance(result, StructuredAnswer):
            mode = resolve_mode(result, sources)
            if mode in ("answer", "partial") and not valid_source_labels(result, sources):
                # 검색된 자료를 근거로 쓰지 않고 답한 경우다. 평가에서 찾을 수 있게 남긴다
                logger.warning("검색된 자료에 없는 출처로 답변: %s", result.used_sources)
            used = set(valid_source_labels(result, sources))
            cited = (
                [d for d in sources if d.metadata.get("source_label") in used]
                if mode in ("answer", "partial")
                else []
            )
            return RAGResponse(
                answer=append_citation(result, sources),
                sources=sources,
                mode=mode,
                cited_sources=cited,
            )
        return RAGResponse(answer=result, sources=sources)


def _network_kwargs(timeout: float | None, max_retries: int | None) -> dict[str, Any]:
    """설정에 값이 있을 때만 넘겨서, 없으면 라이브러리 기본값을 그대로 쓴다."""
    kwargs: dict[str, Any] = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    if max_retries is not None:
        kwargs["max_retries"] = max_retries
    return kwargs


async def create_pipeline(config: RagConfig) -> RAGPipeline:
    """인덱스를 한 번 구축하고 질의용 파이프라인을 만든다."""
    api_key = SecretStr(get_openai_api_key())
    embeddings = OpenAIEmbeddings(
        model=config.embedding.model,
        api_key=api_key,
        **_network_kwargs(config.embedding.timeout, config.embedding.max_retries),
    )
    llm = ChatOpenAI(
        model=config.llm.model,
        temperature=config.llm.temperature,
        api_key=api_key,
        **_network_kwargs(config.llm.timeout, config.llm.max_retries),
    )

    documents = split_documents(load_documents(config.data_path), config.chunking)
    client = create_client(config.qdrant)
    await build_index(client, embeddings, documents, config.qdrant.collection)

    retriever = build_retriever(
        config.retrieval, documents, client, embeddings, config.qdrant.collection
    )
    prompt = load_prompt(config.prompt_path)
    chain: Runnable[dict[str, Any], Any]
    if config.answer_format == "structured":
        chain = prompt | llm.with_structured_output(StructuredAnswer)
    else:
        chain = prompt | llm | StrOutputParser()
    return RAGPipeline(config=config, retriever=retriever, chain=chain)


_pipeline: RAGPipeline | None = None
_lock = asyncio.Lock()


async def generate_rag_response(query: str) -> RAGResponse:
    """기본 설정(RAG_CONFIG 환경변수 또는 hybrid-v1.yaml)의 파이프라인으로 답한다."""
    global _pipeline
    async with _lock:
        if _pipeline is None:
            _pipeline = await create_pipeline(load_config())
    return await _pipeline.agenerate(query)

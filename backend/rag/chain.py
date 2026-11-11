"""LCEL 체인과 메인 함수 generate_rag_response."""

import asyncio
import logging
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from rag.config import RagConfig, get_openai_api_key, load_config
from rag.loaders import load_documents
from rag.prompts import format_context, load_prompt
from rag.retrievers import build_retriever
from rag.splitters import split_documents
from rag.vectorstore import build_index, create_client

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    answer: str
    sources: list[Document]


@dataclass
class RAGPipeline:
    config: RagConfig
    retriever: BaseRetriever
    chain: Runnable[dict[str, str], str]

    async def agenerate(self, query: str, run_config: RunnableConfig | None = None) -> RAGResponse:
        """run_config는 평가 시 토큰 사용량 콜백 등을 전달하기 위한 값이다."""
        found = await self.retriever.ainvoke(query)
        sources = found[: self.config.retrieval.top_k]
        answer = await self.chain.ainvoke(
            {"context": format_context(sources), "question": query}, config=run_config
        )
        return RAGResponse(answer=answer, sources=sources)


async def create_pipeline(config: RagConfig) -> RAGPipeline:
    """인덱스를 한 번 구축하고 질의용 파이프라인을 만든다."""
    api_key = SecretStr(get_openai_api_key())
    embeddings = OpenAIEmbeddings(model=config.embedding.model, api_key=api_key)
    llm = ChatOpenAI(model=config.llm.model, temperature=config.llm.temperature, api_key=api_key)

    documents = split_documents(load_documents(config.data_path), config.chunking)
    client = create_client(config.qdrant)
    await build_index(client, embeddings, documents, config.qdrant.collection)

    retriever = build_retriever(
        config.retrieval, documents, client, embeddings, config.qdrant.collection
    )
    chain = load_prompt(config.prompt_path) | llm | StrOutputParser()
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

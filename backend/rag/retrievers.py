"""검색기: vector / bm25 / hybrid. 설정 값 하나로 고른다."""

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict
from qdrant_client import AsyncQdrantClient

from rag.config import RetrievalConfig
from rag.vectorstore import CONTENT_KEY, METADATA_KEY


class AsyncQdrantRetriever(BaseRetriever):
    """AsyncQdrantClient로 검색하는 비동기 전용 retriever."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: AsyncQdrantClient
    embeddings: Embeddings
    collection: str
    k: int

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        raise NotImplementedError("비동기 클라이언트 전용이에요. ainvoke를 사용해 주세요.")

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> list[Document]:
        vector = await self.embeddings.aembed_query(query)
        result = await self.client.query_points(
            self.collection, query=vector, limit=self.k, with_payload=True
        )
        return [
            Document(
                page_content=point.payload[CONTENT_KEY],
                metadata={**point.payload[METADATA_KEY], "score": point.score},
            )
            for point in result.points
        ]


def build_retriever(
    config: RetrievalConfig,
    documents: list[Document],
    client: AsyncQdrantClient,
    embeddings: Embeddings,
    collection: str,
) -> BaseRetriever:
    def make_vector() -> BaseRetriever:
        return AsyncQdrantRetriever(
            client=client, embeddings=embeddings, collection=collection, k=config.top_k
        )

    def make_bm25() -> BaseRetriever:
        # 기본 토크나이저는 공백 기준이라 한국어 조사에 약하다 (개선은 추후 제안)
        return BM25Retriever.from_documents(documents, k=config.top_k)

    if config.method == "vector":
        return make_vector()
    if config.method == "bm25":
        return make_bm25()
    return EnsembleRetriever(
        retrievers=[make_bm25(), make_vector()],
        weights=[config.bm25_weight, config.vector_weight],
    )

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

from rag_so.config import RetrievalConfig
from rag_so.tokenizers import get_tokenizer
from rag_so.vectorstore import CONTENT_KEY, METADATA_KEY


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
    # 앙상블에서 합치기 전에 넉넉히 가져오고, 마지막(파이프라인)에서 top_k로 자른다
    fetch_k = config.top_k * config.candidate_multiplier

    def make_vector() -> BaseRetriever:
        return AsyncQdrantRetriever(
            client=client, embeddings=embeddings, collection=collection, k=fetch_k
        )

    def make_bm25() -> BaseRetriever:
        # whitespace는 한국어 조사 때문에 "제품의"와 "제품"이 다른 단어로 취급된다
        return BM25Retriever.from_documents(
            documents,
            k=fetch_k,
            preprocess_func=get_tokenizer(config.bm25_tokenizer),
        )

    if config.method == "vector":
        return make_vector()
    if config.method == "bm25":
        return make_bm25()
    return EnsembleRetriever(
        retrievers=[make_bm25(), make_vector()],
        weights=[config.bm25_weight, config.vector_weight],
    )

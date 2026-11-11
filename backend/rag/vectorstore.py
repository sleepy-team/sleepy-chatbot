"""AsyncQdrantClient 컬렉션 생성과 인덱싱.

langchain-qdrant의 QdrantVectorStore는 동기 클라이언트 기반이라 비동기 클라이언트를
직접 쓰기 위해 얇게 직접 구현했다.
"""

import logging

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from qdrant_client import AsyncQdrantClient, models

from rag.config import QdrantConfig, resolve_repo_path

logger = logging.getLogger(__name__)

CONTENT_KEY = "page_content"
METADATA_KEY = "metadata"


def create_client(config: QdrantConfig) -> AsyncQdrantClient:
    if config.url:
        return AsyncQdrantClient(url=config.url)
    if config.path:
        return AsyncQdrantClient(path=str(resolve_repo_path(config.path)))
    return AsyncQdrantClient(location=config.location or ":memory:")


async def build_index(
    client: AsyncQdrantClient,
    embeddings: Embeddings,
    documents: list[Document],
    collection: str,
) -> None:
    """컬렉션을 새로 만들고 문서를 임베딩해 넣는다. 질문마다 호출하지 않는다."""
    if not documents:
        raise ValueError("인덱싱할 문서가 없어요. data/ 를 확인해 주세요.")
    vectors = await embeddings.aembed_documents([d.page_content for d in documents])

    if await client.collection_exists(collection):
        await client.delete_collection(collection)
    await client.create_collection(
        collection,
        vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE),
    )
    points = [
        models.PointStruct(
            id=i,
            vector=vector,
            payload={CONTENT_KEY: doc.page_content, METADATA_KEY: doc.metadata},
        )
        for i, (doc, vector) in enumerate(zip(documents, vectors, strict=True))
    ]
    await client.upsert(collection, points=points)
    logger.info("컬렉션 %s에 %d개 인덱싱", collection, len(points))

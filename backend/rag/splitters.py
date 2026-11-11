"""FAQ는 그대로 두고, 긴 텍스트(제품 정보 등)만 분할한다."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import ChunkingConfig


def split_documents(documents: list[Document], config: ChunkingConfig) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
    )
    chunks: list[Document] = []
    for doc in documents:
        if doc.metadata.get("doc_type") == "faq":
            chunks.append(doc)  # FAQ 1개 = 청크 1개
        else:
            chunks.extend(splitter.split_documents([doc]))
    return chunks

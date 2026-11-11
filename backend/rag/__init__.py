"""슬리비 고객상담 RAG 모듈. FastAPI에 의존하지 않는다."""

from rag.chain import RAGResponse, generate_rag_response

__all__ = ["RAGResponse", "generate_rag_response"]

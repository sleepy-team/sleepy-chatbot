from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig

from app.core.database import init_db
from app.main import create_app
from rag_so.chain import RAGResponse


class FakePipeline:
    """OpenAI 호출 없이 질문 문자열에 따라 정해진 답을 돌려준다."""

    def __init__(self) -> None:
        self.histories: list[list[tuple[str, str]] | None] = []
        self.cited_only = False

    async def agenerate(
        self,
        query: str,
        run_config: RunnableConfig | None = None,
        history: list[tuple[str, str]] | None = None,
    ) -> RAGResponse:
        self.histories.append(history)
        if "안녕" in query:
            # 구조화 출력처럼 모델이 유형을 직접 낸 경우
            return RAGResponse(
                answer="안녕하세요! 궁금한 점을 말씀해 주세요.", sources=[], mode="chitchat"
            )
        if "날씨" in query:
            return RAGResponse(answer="슬리비와 관련 없는 질문에는 답변할 수 없어요.", sources=[])
        if "색상" in query:
            return RAGResponse(
                answer="확인할 수 없어요. 슬리피 고객센터 1:1 문의를 이용해 주세요.", sources=[]
            )
        doc = Document(
            page_content="질문: 앱이 필요한가요?\n답변: 아니요.",
            metadata={"source_label": "FAQ Q3", "question": "앱이 필요한가요?", "score": 0.5},
        )
        if self.cited_only:
            # 구조화 출력처럼 검색된 문서 중 일부만 인용한 경우
            other = Document(
                page_content="질문: 소리가 들리나요?\n답변: 작게 들려요.",
                metadata={"source_label": "FAQ Q5", "question": "소리가 들리나요?"},
            )
            return RAGResponse(
                answer="아니요. [출처: FAQ Q3]",
                sources=[doc, other],
                mode="answer",
                cited_sources=[doc],
            )
        return RAGResponse(answer="아니요. [출처: FAQ Q3]", sources=[doc])


@pytest.fixture
def pipeline() -> FakePipeline:
    return FakePipeline()


@pytest.fixture
async def client(tmp_path: Path, pipeline: FakePipeline) -> AsyncIterator[AsyncClient]:
    db_path = str(tmp_path / "test.sqlite3")
    await init_db(db_path)
    app = create_app()
    # lifespan(실제 RAG 구축)은 실행하지 않고 가짜 의존성을 직접 넣는다
    app.state.db_path = db_path
    app.state.config_name = "fake"
    app.state.history_turns = 3
    app.state.pipeline = pipeline
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

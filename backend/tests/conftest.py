from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig

from app.core.database import init_db
from app.main import create_app
from rag.chain import RAGResponse


class FakePipeline:
    """OpenAI 호출 없이 질문 문자열에 따라 정해진 답을 돌려준다."""

    async def agenerate(self, query: str, run_config: RunnableConfig | None = None) -> RAGResponse:
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
        return RAGResponse(answer="아니요. [출처: FAQ Q3]", sources=[doc])


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[AsyncClient]:
    db_path = str(tmp_path / "test.sqlite3")
    await init_db(db_path)
    app = create_app()
    # lifespan(실제 RAG 구축)은 실행하지 않고 가짜 의존성을 직접 넣는다
    app.state.db_path = db_path
    app.state.config_name = "fake"
    app.state.pipeline = FakePipeline()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

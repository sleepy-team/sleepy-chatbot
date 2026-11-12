"""실행: uv run uvicorn app.main:app --reload (backend/ 에서)"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, inquiry
from app.core.config import get_settings
from app.core.database import init_db
from rag.chain import create_pipeline
from rag.config import load_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    rag_config = load_config()  # RAG_CONFIG 환경변수가 없으면 hybrid-v1
    await init_db(settings.db_path)
    app.state.db_path = settings.db_path
    app.state.config_name = rag_config.name
    app.state.history_turns = rag_config.history_turns
    app.state.pipeline = await create_pipeline(rag_config)  # 인덱스는 시작할 때 한 번만 만든다
    logger.info("RAG 설정 %s 로 시작", rag_config.name)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Sleeby Chatbot API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat.router)
    app.include_router(inquiry.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

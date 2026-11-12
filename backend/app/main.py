"""실행: uv run uvicorn app.main:app --reload (backend/ 에서)"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, inquiry
from app.core.config import get_settings
from app.core.database import init_db
from app.services.rag_engine import build_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    await init_db(settings.db_path)
    engine = await build_engine(settings)  # 인덱스·검색기는 시작할 때 한 번만 만든다
    app.state.db_path = settings.db_path
    app.state.config_name = engine.name
    app.state.history_turns = engine.history_turns
    app.state.pipeline = engine.pipeline
    logger.info("RAG 엔진 %s 로 시작 (%s)", engine.name, settings.rag_engine)
    yield
    if callable(engine.close):
        engine.close()


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

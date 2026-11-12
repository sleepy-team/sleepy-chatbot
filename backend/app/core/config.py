"""앱 설정. 환경변수와 저장소 루트 .env 에서 읽는다."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from rag.config import REPO_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # backend/ 에서 실행하면 gitignore 대상인 db.sqlite3 로 저장된다
    db_path: str = "db.sqlite3"
    cors_origins: list[str] = ["http://localhost:5173"]
    # team: 팀 채택 RAG(configs/rag/default.yaml), so: 이 저장소의 실험 RAG(RAG_CONFIG 설정)
    rag_engine: Literal["team", "so"] = "team"
    team_rag_config: str = "configs/rag/default.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""앱 설정. 환경변수와 저장소 루트 .env 에서 읽는다."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from rag.config import REPO_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # backend/ 에서 실행하면 gitignore 대상인 db.sqlite3 로 저장된다
    db_path: str = "db.sqlite3"
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

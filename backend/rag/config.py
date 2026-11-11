"""RAG 설정 파일(YAML)과 .env(API 키) 로드."""

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "rag" / "hybrid-v1.yaml"
CONFIG_ENV_VAR = "RAG_CONFIG"


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    openai_api_key: SecretStr | None = None


class EmbeddingConfig(BaseModel):
    model: str


class LLMConfig(BaseModel):
    model: str
    temperature: float = 0.0


class ChunkingConfig(BaseModel):
    chunk_size: int = 400
    chunk_overlap: int = 50


class QdrantConfig(BaseModel):
    location: str | None = ":memory:"
    path: str | None = None
    url: str | None = None
    collection: str = "sleeby"


class RetrievalConfig(BaseModel):
    method: Literal["vector", "bm25", "hybrid"] = "hybrid"
    top_k: int = 3
    bm25_weight: float = 0.4
    vector_weight: float = 0.6


class RagConfig(BaseModel):
    name: str
    data_dir: str = "data"
    prompt_file: str = "backend/rag/prompts/system.md"
    embedding: EmbeddingConfig
    llm: LLMConfig
    chunking: ChunkingConfig = ChunkingConfig()
    qdrant: QdrantConfig = QdrantConfig()
    retrieval: RetrievalConfig = RetrievalConfig()

    @property
    def data_path(self) -> Path:
        return resolve_repo_path(self.data_dir)

    @property
    def prompt_path(self) -> Path:
        return resolve_repo_path(self.prompt_file)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: str | Path | None = None) -> RagConfig:
    config_path = Path(path or os.environ.get(CONFIG_ENV_VAR) or DEFAULT_CONFIG_PATH)
    with config_path.open(encoding="utf-8") as f:
        return RagConfig.model_validate(yaml.safe_load(f))


def get_openai_api_key() -> str:
    key = EnvSettings().openai_api_key
    if key is None or not key.get_secret_value():
        raise RuntimeError("OPENAI_API_KEY가 없어요. 저장소 루트 .env에 설정해 주세요.")
    return key.get_secret_value()

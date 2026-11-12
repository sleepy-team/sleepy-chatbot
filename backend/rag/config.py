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
    timeout: float | None = None
    max_retries: int | None = None


class LLMConfig(BaseModel):
    model: str
    temperature: float = 0.0
    # 네트워크가 불안정할 때를 위한 값. None이면 라이브러리 기본값을 쓴다(기존 동작)
    timeout: float | None = None
    max_retries: int | None = None


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
    # 검색 전에 질문 속 구어·오타를 표준어로 바꾼다 (예: 어플 -> 앱). LLM에는 원문 질문을 보낸다
    query_synonyms: dict[str, str] = {}
    # 기존 설정(v1)의 동작을 바꾸지 않도록 기본값은 이전 동작과 같다
    bm25_tokenizer: Literal["whitespace", "kiwi"] = "whitespace"
    # 앙상블 전에 각 검색기가 top_k의 몇 배를 가져올지 (마지막에 top_k로 자른다)
    candidate_multiplier: int = 1


class RagConfig(BaseModel):
    name: str
    data_dir: str = "data"
    prompt_file: str = "backend/rag/prompts/system.md"
    embedding: EmbeddingConfig
    llm: LLMConfig
    chunking: ChunkingConfig = ChunkingConfig()
    qdrant: QdrantConfig = QdrantConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    # structured: 모델이 답변 유형(mode)과 답변을 함께 낸다. text: 답변 문장만 낸다(기존 동작)
    answer_format: Literal["text", "structured"] = "text"
    # 같은 세션의 최근 몇 턴을 프롬프트에 넣을지 (0이면 사용하지 않는다: 기존 동작)
    history_turns: int = 0

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

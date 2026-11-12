import pytest

from rag_so.config import REPO_ROOT, RetrievalConfig, load_config
from rag_so.tokenizers import get_tokenizer, whitespace_tokenize


def test_기존_설정은_이전_동작을_유지한다() -> None:
    config = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v1.yaml")
    assert config.retrieval.bm25_tokenizer == "whitespace"
    assert config.retrieval.candidate_multiplier == 1
    assert config.retrieval.top_k == 3


def test_hybrid_v2_설정은_새_프롬프트와_top_k를_쓴다() -> None:
    config = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v2.yaml")
    assert config.prompt_path.name == "system-v2.md"
    assert config.prompt_path.exists()
    assert config.retrieval.top_k == 5
    assert config.retrieval.candidate_multiplier == 2


def test_hybrid_v3_설정은_구조화_출력과_대화_이력을_쓴다() -> None:
    config = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v3.yaml")
    assert config.answer_format == "structured"
    assert config.history_turns == 3
    assert config.prompt_path.name == "system-v3.md"
    assert config.prompt_path.exists()
    assert config.llm.model == "gpt-4o-mini"
    assert config.llm.timeout == 30
    assert config.llm.max_retries == 4


def test_hybrid_v4_설정은_새_프롬프트와_오타_사전을_쓴다() -> None:
    config = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v4.yaml")
    assert config.prompt_path.name == "system-v4.md"
    assert config.prompt_path.exists()
    assert config.answer_format == "structured"
    assert config.retrieval.query_synonyms["어플"] == "앱"


def test_hybrid_v5_설정은_v4와_프롬프트만_다르다() -> None:
    v4 = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v4.yaml")
    v5 = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v5.yaml")
    assert v5.prompt_path.name == "system-v5.md"
    assert v5.prompt_path.exists()
    assert v5.retrieval == v4.retrieval
    assert v5.llm == v4.llm


def test_hybrid_v6_설정은_v5와_프롬프트와_보정_사전만_다르다() -> None:
    v5 = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v5.yaml")
    v6 = load_config(REPO_ROOT / "configs" / "rag" / "hybrid-v6.yaml")
    assert v6.prompt_path.name == "system-v6.md"
    assert v6.prompt_path.exists()
    assert v6.retrieval.typo_corrections["베터리"] == "배터리"
    assert v6.retrieval.top_k == v5.retrieval.top_k
    assert v6.llm == v5.llm
    assert v5.retrieval.typo_corrections == {}


def test_이전_설정은_오타_사전을_쓰지_않는다() -> None:
    for name in ("hybrid-v1", "hybrid-v2", "hybrid-v3"):
        config = load_config(REPO_ROOT / "configs" / "rag" / f"{name}.yaml")
        assert config.retrieval.query_synonyms == {}


def test_기존_설정은_텍스트_출력과_이력_없음을_유지한다() -> None:
    for name in ("hybrid-v1", "hybrid-v2"):
        config = load_config(REPO_ROOT / "configs" / "rag" / f"{name}.yaml")
        assert config.answer_format == "text"
        assert config.history_turns == 0
        assert config.llm.timeout is None


def test_공백_토크나이저는_str_split과_같다() -> None:
    assert get_tokenizer("whitespace") is whitespace_tokenize
    assert whitespace_tokenize("이 제품의 특징이 뭐야?") == ["이", "제품의", "특징이", "뭐야?"]


def test_kiwi_토크나이저는_조사와_흔한_말을_뗀다() -> None:
    tokens = get_tokenizer("kiwi")("이 제품의 특징이 뭐야?")
    assert tokens == ["제품", "특징"]


def test_알_수_없는_토크나이저_이름은_설정에서_거부된다() -> None:
    with pytest.raises(ValueError):
        RetrievalConfig(bm25_tokenizer="unknown")  # type: ignore[arg-type]

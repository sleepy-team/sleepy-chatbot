"""BM25용 토크나이저. 설정 값(whitespace | kiwi)으로 고른다."""

from collections.abc import Callable
from functools import lru_cache
from typing import Literal

# 검색에 쓸 품사: 일반·고유명사, 어근, 동사·형용사 어간, 외국어, 숫자
# (조사·어미·"이/뭐" 같은 흔한 말은 점수를 왜곡하므로 버린다)
KIWI_KEEP_TAGS = ("NNG", "NNP", "NR", "XR", "VV", "VA", "SL", "SN")


def whitespace_tokenize(text: str) -> list[str]:
    return text.split()


@lru_cache(maxsize=1)
def _load_kiwi():  # noqa: ANN202
    try:
        from kiwipiepy import Kiwi
    except ImportError as e:
        raise RuntimeError(
            "bm25_tokenizer: kiwi 를 쓰려면 kiwipiepy 설치가 필요해요 (uv add kiwipiepy)."
        ) from e
    return Kiwi()


def kiwi_tokenize(text: str) -> list[str]:
    tokens = _load_kiwi().tokenize(text)
    return [t.form for t in tokens if t.tag.startswith(KIWI_KEEP_TAGS)]


def get_tokenizer(name: Literal["whitespace", "kiwi"]) -> Callable[[str], list[str]]:
    return kiwi_tokenize if name == "kiwi" else whitespace_tokenize

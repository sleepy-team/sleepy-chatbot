from langchain_core.documents import Document

from rag_so.chain import StructuredAnswer, append_citation, resolve_mode


def _docs(*labels: str) -> list[Document]:
    return [Document(page_content="x", metadata={"source_label": label}) for label in labels]


def test_검색된_문서의_라벨만_출처로_붙인다() -> None:
    result = StructuredAnswer(
        mode="answer", answer="아니요.", used_sources=["FAQ Q3", "FAQ Q999", "제품소개서"]
    )

    answer = append_citation(result, _docs("FAQ Q3", "제품소개서", "FAQ Q5"))

    assert answer == "아니요.\n\n[출처: FAQ Q3, 제품소개서]"


def test_중복_라벨은_한_번만_붙인다() -> None:
    result = StructuredAnswer(mode="answer", answer="네.", used_sources=["FAQ Q3", "FAQ Q3"])

    assert append_citation(result, _docs("FAQ Q3")).endswith("[출처: FAQ Q3]")


def test_인사나_범위_밖에는_출처를_붙이지_않는다() -> None:
    for mode in ("chitchat", "offtopic", "clarify", "unknown"):
        result = StructuredAnswer(mode=mode, answer="안녕하세요.", used_sources=[])

        assert append_citation(result, _docs("FAQ Q3")) == "안녕하세요."


def test_확인_불가_답변은_출처가_있어도_붙이지_않는다() -> None:
    result = StructuredAnswer(mode="unknown", answer="확인이 안 돼요.", used_sources=["FAQ Q3"])

    assert append_citation(result, _docs("FAQ Q3")) == "확인이 안 돼요."


def test_근거를_쓰고도_범위_밖으로_표시하면_answer로_바로잡고_출처를_붙인다() -> None:
    result = StructuredAnswer(mode="offtopic", answer="보증은 1년이에요.", used_sources=["FAQ Q78"])
    sources = _docs("FAQ Q78")

    assert resolve_mode(result, sources) == "answer"
    assert append_citation(result, sources).endswith("[출처: FAQ Q78]")


def test_검색되지_않은_출처만_썼다면_유형을_바꾸지_않는다() -> None:
    result = StructuredAnswer(mode="chitchat", answer="안녕하세요.", used_sources=["FAQ Q999"])

    assert resolve_mode(result, _docs("FAQ Q3")) == "chitchat"


def test_사용한_출처가_없으면_출처를_붙이지_않는다() -> None:
    result = StructuredAnswer(mode="answer", answer="네.", used_sources=[])

    assert append_citation(result, _docs("FAQ Q3")) == "네."

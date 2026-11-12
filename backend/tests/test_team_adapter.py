"""팀 엔진 어댑터: OpenAI 호출 없이 팀 응답 -> 서비스 응답 변환과 연결을 검증한다."""

from httpx import AsyncClient

from app.services.chat_service import resolve_mode
from app.services.rag_engine import TeamRagAdapter, source_label, to_rag_response
from rag.schemas import RagResponse, Source


def _source(faq_id: str = "Q03") -> Source:
    return Source(
        faq_id=faq_id,
        title="앱이 필요한가요?",
        category="제품 소개·기능",
        score=0.82,
        excerpt="아니요. 앱 없이 사용할 수 있어요.",
    )


def test_출처_라벨은_FAQ와_제품_정보를_구분한다() -> None:
    assert source_label("Q03") == "FAQ Q03"
    assert source_label("P01") == "제품 정보 P01"


def test_팀_응답을_서비스_응답으로_바꾼다() -> None:
    team = RagResponse(
        mode="answer",
        answer="아니요.",
        sources=[_source()],
        show_contact=False,
        prompt_tokens=120,
        completion_tokens=30,
    )

    response = to_rag_response(team)

    assert response.mode == "answer"
    assert response.show_contact is False
    assert (response.prompt_tokens, response.completion_tokens) == (120, 30)
    assert [d.metadata["source_label"] for d in response.cited_sources or []] == ["FAQ Q03"]
    assert response.cited_sources[0].metadata["question"] == "앱이 필요한가요?"
    assert response.cited_sources[0].metadata["score"] == 0.82


def test_인사_모드는_chitchat으로_바뀐다() -> None:
    response = to_rag_response(RagResponse(mode="greeting", answer="안녕하세요!"))

    assert response.mode == "chitchat"
    assert resolve_mode(response) == ("chitchat", False)


def test_엔진이_담당자_문의를_정하면_그대로_따른다() -> None:
    # 근거 답변이어도 상담원 연결이 필요한 FAQ면 문의 버튼을 보여 준다
    team = RagResponse(mode="answer", answer="네.", sources=[_source()], show_contact=True)

    assert resolve_mode(to_rag_response(team)) == ("answer", True)
    unknown = to_rag_response(
        RagResponse(mode="unknown", answer="확인이 안 돼요.", show_contact=True)
    )
    assert resolve_mode(unknown) == ("unknown", True)


class FakeTeamPipeline:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    async def aanswer(self, question: str, history: list[str] | None = None) -> RagResponse:
        self.calls.append((question, list(history or [])))
        return RagResponse(mode="answer", answer="아니요.", sources=[_source()])

    def close(self) -> None:
        pass


async def test_어댑터는_이전_대화에서_질문만_골라_팀_엔진에_넘긴다() -> None:
    fake = FakeTeamPipeline()
    adapter = TeamRagAdapter(fake)

    await adapter.agenerate(
        "그럼 충전은요?", history=[("앱이 필요한가요?", "아니요."), ("색상은?", "x")]
    )

    assert fake.calls == [("그럼 충전은요?", ["앱이 필요한가요?", "색상은?"])]


async def test_API로_팀_엔진_응답과_출처_칩이_내려간다(client: AsyncClient) -> None:
    client._transport.app.state.pipeline = TeamRagAdapter(FakeTeamPipeline())  # type: ignore[attr-defined]

    body = (await client.post("/api/chats", json={"message": "앱이 필요한가요?"})).json()

    assert (body["mode"], body["needs_inquiry"]) == ("answer", False)
    assert body["answer"] == "아니요."
    assert [s["label"] for s in body["sources"]] == ["FAQ Q03"]
    assert body["sources"][0]["title"] == "앱이 필요한가요?"

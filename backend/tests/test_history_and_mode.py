from httpx import AsyncClient

from app.services.chat_service import resolve_mode
from rag_so.chain import RAGResponse, apply_corrections, build_retrieval_query
from tests.conftest import FakePipeline


async def test_같은_세션의_이전_대화가_파이프라인에_전달된다(
    client: AsyncClient, pipeline: FakePipeline
) -> None:
    first = (await client.post("/api/chats", json={"message": "앱 설치가 필요한가요?"})).json()
    await client.post(
        "/api/chats", json={"message": "그럼 충전은요?", "session_id": first["session_id"]}
    )

    assert pipeline.histories[0] is None
    assert pipeline.histories[1] == [("앱 설치가 필요한가요?", "아니요. [출처: FAQ Q3]")]


async def test_다른_세션의_대화는_섞이지_않는다(
    client: AsyncClient, pipeline: FakePipeline
) -> None:
    await client.post("/api/chats", json={"message": "앱 설치가 필요한가요?", "session_id": "a"})
    await client.post("/api/chats", json={"message": "그거 얼마예요?", "session_id": "b"})

    assert pipeline.histories[1] is None


async def test_초기화한_대화는_이력에_포함되지_않는다(
    client: AsyncClient, pipeline: FakePipeline
) -> None:
    await client.post("/api/chats", json={"message": "질문1", "session_id": "s"})
    await client.delete("/api/chats/s")
    await client.post("/api/chats", json={"message": "질문2", "session_id": "s"})

    assert pipeline.histories[-1] is None


async def test_이력은_최근_3턴만_전달한다(client: AsyncClient, pipeline: FakePipeline) -> None:
    for i in range(5):
        await client.post("/api/chats", json={"message": f"질문{i}", "session_id": "s"})

    assert [q for q, _ in pipeline.histories[-1] or []] == ["질문1", "질문2", "질문3"]


async def test_모델이_낸_유형은_그대로_쓰고_문의_버튼은_뜨지_않는다(client: AsyncClient) -> None:
    body = (await client.post("/api/chats", json={"message": "안녕!"})).json()

    assert (body["mode"], body["needs_inquiry"]) == ("chitchat", False)


async def test_모델이_인용한_문서만_화면용_출처로_내려준다(
    client: AsyncClient, pipeline: FakePipeline
) -> None:
    pipeline.cited_only = True

    body = (await client.post("/api/chats", json={"message": "앱 설치가 필요한가요?"})).json()

    assert [s["label"] for s in body["sources"]] == ["FAQ Q3"]


def test_답했어도_문의를_안내하면_partial로_바뀐다() -> None:
    response = RAGResponse(
        answer="보증은 1년이에요. 자세한 건 고객센터로 문의해 주세요. [출처: FAQ Q78]",
        sources=[],
        mode="answer",
    )

    assert resolve_mode(response) == ("partial", True)


def test_유형이_없으면_문구로_추정한다() -> None:
    assert resolve_mode(RAGResponse(answer="아니요. [출처: FAQ Q3]", sources=[])) == (
        "answer",
        False,
    )


def test_명백한_오타는_바로잡고_설정이_없으면_그대로_둔다() -> None:
    corrections = {"베터리": "배터리", "보증기긴": "보증기간"}

    assert apply_corrections("슬리비 베터리 얼마나 가?", corrections) == "슬리비 배터리 얼마나 가?"
    assert apply_corrections("보증기긴 머야?", corrections) == "보증기간 머야?"
    assert apply_corrections("슬리비 베터리 얼마나 가?", None) == "슬리비 베터리 얼마나 가?"


def test_검색_전에_구어와_오타를_표준어로_바꾼다() -> None:
    synonyms = {"어플": "앱", "베터리": "배터리"}

    assert build_retrieval_query("어플 꼭 깔아야댐?", None, synonyms) == "앱 꼭 깔아야댐?"
    assert build_retrieval_query("슬리비 베터리 얼마나 가?", None, synonyms) == (
        "슬리비 배터리 얼마나 가?"
    )
    assert build_retrieval_query("어플 필요해?", None, None) == "어플 필요해?"


def test_짧은_후속_질문에만_직전_질문을_붙여_검색한다() -> None:
    history = [("보증기간 알려주세요.", "1년이에요.")]

    assert build_retrieval_query("그건 어디에 문의해요?", history) == (
        "보증기간 알려주세요. 그건 어디에 문의해요?"
    )
    assert build_retrieval_query(
        "슬리비를 처음 사용할 때 어떻게 준비하고 어떤 순서로 착용해야 하나요?", history
    ) == ("슬리비를 처음 사용할 때 어떻게 준비하고 어떤 순서로 착용해야 하나요?")
    assert build_retrieval_query("그건요?", None) == "그건요?"

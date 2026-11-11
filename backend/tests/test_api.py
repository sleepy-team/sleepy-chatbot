from httpx import AsyncClient


async def test_chat_returns_answer_and_sources(client: AsyncClient) -> None:
    response = await client.post("/api/chats", json={"message": "앱 설치가 필요한가요?"})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "answer"
    assert body["needs_inquiry"] is False
    assert body["session_id"]
    assert body["sources"][0]["label"] == "FAQ Q3"


async def test_chat_unknown_and_offtopic_modes(client: AsyncClient) -> None:
    unknown = (await client.post("/api/chats", json={"message": "색상이 뭐예요?"})).json()
    offtopic = (await client.post("/api/chats", json={"message": "오늘 날씨 어때?"})).json()

    assert (unknown["mode"], unknown["needs_inquiry"]) == ("unknown", True)
    assert (offtopic["mode"], offtopic["needs_inquiry"]) == ("offtopic", False)


async def test_chat_rejects_empty_message(client: AsyncClient) -> None:
    response = await client.post("/api/chats", json={"message": ""})

    assert response.status_code == 422


async def test_session_history_and_reset(client: AsyncClient) -> None:
    first = (await client.post("/api/chats", json={"message": "질문1"})).json()
    session_id = first["session_id"]
    await client.post("/api/chats", json={"message": "질문2", "session_id": session_id})

    history = (await client.get(f"/api/chats/{session_id}")).json()
    assert [m["question"] for m in history] == ["질문1", "질문2"]

    reset = await client.delete(f"/api/chats/{session_id}")
    assert reset.status_code == 204
    assert (await client.get(f"/api/chats/{session_id}")).json() == []

    # 초기화 뒤에도 같은 세션으로 다시 질문할 수 있다
    again = await client.post("/api/chats", json={"message": "질문3", "session_id": session_id})
    assert again.status_code == 200
    assert len((await client.get(f"/api/chats/{session_id}")).json()) == 1


async def test_inquiry_created_with_conversation(client: AsyncClient) -> None:
    chat = (await client.post("/api/chats", json={"message": "색상이 뭐예요?"})).json()

    response = await client.post(
        "/api/inquiries",
        json={
            "name": "홍길동",
            "email": "hong@example.com",
            "content": "색상 문의",
            "session_id": chat["session_id"],
            "include_conversation": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1


async def test_inquiry_rejects_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/inquiries", json={"name": "홍길동", "email": "not-an-email", "content": "문의"}
    )

    assert response.status_code == 422

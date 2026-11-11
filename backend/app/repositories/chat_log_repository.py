import json
from datetime import UTC, datetime

from app.core.database import connect
from app.schemas.chat import ChatMessage, SourceItem


class ChatLogRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def add(
        self,
        *,
        session_id: str,
        question: str,
        answer: str,
        mode: str,
        needs_inquiry: bool,
        sources: list[SourceItem],
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
        config_name: str,
    ) -> int:
        sources_json = json.dumps([s.model_dump() for s in sources], ensure_ascii=False)
        async with connect(self._db_path) as db:
            cursor = await db.execute(
                "INSERT INTO chat_logs (session_id, question, answer, mode, needs_inquiry,"
                " sources_json, latency_ms, input_tokens, output_tokens, config_name, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    question,
                    answer,
                    mode,
                    int(needs_inquiry),
                    sources_json,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    config_name,
                    datetime.now(UTC).isoformat(),
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def list_by_session(self, session_id: str) -> list[ChatMessage]:
        async with connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM chat_logs WHERE session_id = ? AND is_reset = 0 ORDER BY id",
                (session_id,),
            )
            rows = await cursor.fetchall()
        return [
            ChatMessage(
                id=row["id"],
                question=row["question"],
                answer=row["answer"],
                mode=row["mode"],
                needs_inquiry=bool(row["needs_inquiry"]),
                sources=[SourceItem(**s) for s in json.loads(row["sources_json"])],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def reset_session(self, session_id: str) -> int:
        """대화 초기화: 화면용 이력만 숨기고 로그 행은 남긴다."""
        async with connect(self._db_path) as db:
            cursor = await db.execute(
                "UPDATE chat_logs SET is_reset = 1 WHERE session_id = ? AND is_reset = 0",
                (session_id,),
            )
            await db.commit()
            return cursor.rowcount

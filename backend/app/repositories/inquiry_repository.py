import json
from datetime import UTC, datetime

from app.core.database import connect
from app.schemas.chat import ChatMessage
from app.schemas.inquiry import InquiryResponse


class InquiryRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def add(
        self,
        *,
        name: str,
        email: str,
        content: str,
        session_id: str | None,
        conversation: list[ChatMessage] | None,
    ) -> InquiryResponse:
        created_at = datetime.now(UTC).isoformat()
        conversation_json = (
            json.dumps([m.model_dump() for m in conversation], ensure_ascii=False)
            if conversation is not None
            else None
        )
        async with connect(self._db_path) as db:
            cursor = await db.execute(
                "INSERT INTO inquiries (name, email, content, session_id, conversation_json,"
                " created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, content, session_id, conversation_json, created_at),
            )
            await db.commit()
            return InquiryResponse(id=cursor.lastrowid or 0, created_at=created_at)

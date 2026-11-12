from typing import Literal

from pydantic import BaseModel, Field

# chitchat: 인사·감사·챗봇 소개, clarify: 뜻이 불분명해 되묻는 답변
ChatMode = Literal["answer", "partial", "unknown", "offtopic", "chitchat", "clarify"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str | None = None


class SourceItem(BaseModel):
    label: str
    title: str
    excerpt: str
    score: float | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    mode: ChatMode
    needs_inquiry: bool
    sources: list[SourceItem]
    latency_ms: int


class ChatMessage(BaseModel):
    id: int
    question: str
    answer: str
    mode: ChatMode
    needs_inquiry: bool
    sources: list[SourceItem]
    created_at: str

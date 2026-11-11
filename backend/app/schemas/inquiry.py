from pydantic import BaseModel, EmailStr, Field


class InquiryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    content: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    include_conversation: bool = False


class InquiryResponse(BaseModel):
    id: int
    created_at: str

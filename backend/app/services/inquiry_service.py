from app.repositories.chat_log_repository import ChatLogRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.schemas.inquiry import InquiryCreate, InquiryResponse


class InquiryService:
    def __init__(
        self, inquiry_repository: InquiryRepository, chat_log_repository: ChatLogRepository
    ) -> None:
        self._inquiries = inquiry_repository
        self._chat_logs = chat_log_repository

    async def create(self, data: InquiryCreate) -> InquiryResponse:
        conversation = None
        if data.include_conversation and data.session_id:
            conversation = await self._chat_logs.list_by_session(data.session_id)
        return await self._inquiries.add(
            name=data.name,
            email=str(data.email),
            content=data.content,
            session_id=data.session_id,
            conversation=conversation,
        )

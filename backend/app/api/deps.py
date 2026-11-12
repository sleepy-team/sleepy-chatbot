"""Depends 로 주입하는 서비스. 파이프라인과 DB 경로는 app.state 에서 가져온다."""

from fastapi import Depends, Request

from app.repositories.chat_log_repository import ChatLogRepository
from app.repositories.inquiry_repository import InquiryRepository
from app.services.chat_service import ChatService
from app.services.inquiry_service import InquiryService


def get_chat_log_repository(request: Request) -> ChatLogRepository:
    return ChatLogRepository(request.app.state.db_path)


def get_chat_service(
    request: Request, repository: ChatLogRepository = Depends(get_chat_log_repository)
) -> ChatService:
    return ChatService(
        request.app.state.pipeline,
        repository,
        request.app.state.config_name,
        history_turns=request.app.state.history_turns,
    )


def get_inquiry_service(
    request: Request, chat_logs: ChatLogRepository = Depends(get_chat_log_repository)
) -> InquiryService:
    return InquiryService(InquiryRepository(request.app.state.db_path), chat_logs)

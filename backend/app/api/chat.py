from fastapi import APIRouter, Depends, status

from app.api.deps import get_chat_service
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("", response_model=ChatResponse)
async def ask(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """질문에 답한다. session_id가 없으면 새 세션을 만든다. 같은 session_id로 재질문할 수 있다."""
    return await service.ask(request.message, request.session_id)


@router.get("/{session_id}", response_model=list[ChatMessage])
async def history(session_id: str, service: ChatService = Depends(get_chat_service)):
    return await service.history(session_id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reset(session_id: str, service: ChatService = Depends(get_chat_service)) -> None:
    """대화 초기화."""
    await service.reset(session_id)

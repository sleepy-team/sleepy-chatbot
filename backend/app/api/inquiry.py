from fastapi import APIRouter, Depends, status

from app.api.deps import get_inquiry_service
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.services.inquiry_service import InquiryService

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
async def create_inquiry(
    request: InquiryCreate, service: InquiryService = Depends(get_inquiry_service)
):
    return await service.create(request)

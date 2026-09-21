"""Endpoint kiểm tra trạng thái hoạt động của Backend Service. Phụ trách: TV3."""

from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Kiểm tra dịch vụ có đang chạy bình thường hay không."""
    return HealthResponse(status="ok")

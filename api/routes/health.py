"""Endpoint kiểm tra trạng thái sức khỏe dịch vụ. Phụ trách: TV3."""

from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Kiểm tra dịch vụ có đang hoạt động bình thường hay không."""
    return HealthResponse(status="healthy", version="0.1.0")

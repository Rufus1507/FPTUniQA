"""Định nghĩa Pydantic Request / Response models cho API. Phụ trách: TV3."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema dữ liệu đầu vào cho yêu cầu hỏi đáp."""
    query: str = Field(..., min_length=2, example="Sinh viên được đăng ký tối đa bao nhiêu tín chỉ một kỳ?")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Số lượng tài liệu trích xuất")
    conversation_id: Optional[str] = Field(default=None, description="Mã phiên hội thoại đa lượt")


class CitationModel(BaseModel):
    """Schema thông tin nguồn trích dẫn."""
    doc_id: str = Field(..., example="doc_001")
    title: str = Field(..., example="Quy chế đào tạo theo tín chỉ")
    section: Optional[str] = Field(default=None, example="Điều 12")
    snippet: str = Field(..., example="Mỗi học kỳ chính, sinh viên được đăng ký tối thiểu 14...")


class DocumentModel(BaseModel):
    """Schema tài liệu tra cứu được."""
    id: str
    title: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """Schema phản hồi câu trả lời hoàn chỉnh."""
    query: str
    normalized_query: str
    intent: str
    answer: str
    citations: List[CitationModel] = Field(default_factory=list)
    retrieved_documents: List[DocumentModel] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Schema trạng thái dịch vụ."""
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"

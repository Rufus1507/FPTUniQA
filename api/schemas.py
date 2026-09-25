"""Định nghĩa Pydantic Models cho API Request / Response (Schemas). Phụ trách: TV3.

Đồng bộ trực tiếp với api/contracts.py để đảm bảo tính nhất quán của hợp đồng dữ liệu.
"""

from api.contracts import (
    Citation,
    DocumentChunk,
    GenerationOutput,
    HealthResponse,
    ParsedQuery,
    QueryRequest,
    QueryResponse,
    RetrievalResponse,
)

__all__ = [
    "QueryRequest",
    "Citation",
    "QueryResponse",
    "HealthResponse",
    "GenerationOutput",
    "DocumentChunk",
    "RetrievalResponse",
    "ParsedQuery",
]

"""Endpoint tiếp nhận và xử lý câu hỏi hỏi đáp RAG. Phụ trách: TV3."""

from fastapi import APIRouter, HTTPException, Request
from api.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/v1", tags=["Question Answering"])


@router.post("/query", response_model=QueryResponse)
async def answer_query(request_body: QueryRequest, request: Request) -> QueryResponse:
    """Tiếp nhận câu hỏi từ người dùng và trả về câu trả lời tổng hợp kèm trích dẫn."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG Pipeline chưa sẵn sàng hoặc đang khởi động.")

    try:
        result = pipeline.run(query=request_body.query, top_k=request_body.top_k or 5)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi trong quá trình xử lý câu hỏi: {str(e)}")

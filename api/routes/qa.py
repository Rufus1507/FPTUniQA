"""Endpoint tiếp nhận và xử lý câu hỏi hỏi đáp RAG. Phụ trách: TV3."""

from fastapi import APIRouter, HTTPException, status
from api.schemas import Citation, QueryRequest, QueryResponse
from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.api.qa")

router = APIRouter(prefix="/api/v1", tags=["Question Answering"])

# Khởi tạo singleton pipeline cho ứng dụng API
_pipeline_instance: RAGPipeline = RAGPipeline()


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def answer_query(request: QueryRequest) -> QueryResponse:
    """Tiếp nhận câu hỏi từ client, thực thi pipeline RAG và trả về câu trả lời kèm trích dẫn."""
    logger.info(f"Nhận request hỏi đáp: '{request.query}'")
    try:
        result = _pipeline_instance.answer(request.query, session_id=request.session_id)

        # Định dạng danh sách citations theo schema Pydantic
        structured_citations = [
            Citation(
                doc_id=c.get("doc_id", "UNKNOWN"),
                title=c.get("title", "Tài liệu học vụ"),
                source=c.get("source", "Tài liệu quy chế"),
            )
            for c in result.get("citations", [])
        ]

        return QueryResponse(
            answer=result.get("answer", ""),
            citations=structured_citations,
            route=result.get("route"),
            rewritten_query=result.get("rewritten_query"),
            session_id=result.get("session_id"),
            possible_hallucination=result.get("possible_hallucination", False),
        )

    except Exception as exc:
        error_detail = f"Lỗi trong quá trình xử lý câu hỏi tại RAG Pipeline: {str(exc)}"
        logger.error(error_detail, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        )

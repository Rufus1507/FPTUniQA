"""Khởi chạy ứng dụng FastAPI và cấu hình CORS Middleware. Phụ trách: TV3."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.qa import router as qa_router
from university_qa.utils.config import config
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.api.main")

app = FastAPI(
    title="FPT University Academic QA API",
    description="Hệ thống RAG giải đáp quy chế, học vụ và đào tạo Đại học FPT - Tuần 1",
    version="0.1.0",
)

# Cấu hình CORS cho phép frontend Streamlit (localhost) gọi vào
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "*",  # Cho phép trong giai đoạn dev cục bộ
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router endpoints
app.include_router(health_router)
app.include_router(qa_router)

# Endpoint alias /query trỏ trực tiếp đến handler /api/v1/query
from api.routes.qa import answer_query
from api.contracts import QueryResponse
app.add_api_route("/query", answer_query, methods=["POST"], response_model=QueryResponse, tags=["Question Answering"])


@app.on_event("startup")
async def on_startup():
    logger.info(f"FastAPI Server khởi động thành công trên môi trường: {config.environment}")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("FastAPI Server đang tắt...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
    )

"""Khởi chạy ứng dụng FastAPI và Middleware. Phụ trách: TV3."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.qa import router as qa_router
from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.utils.config import load_config
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và đóng ứng dụng."""
    logger.info("Đang khởi động University QA Backend Service...")
    config = load_config()
    pipeline = RAGPipeline(config=config)
    try:
        pipeline.load_corpus()
        logger.info("Đã nạp và lập chỉ mục corpus thành công!")
    except Exception as e:
        logger.warning(f"Chưa thể nạp corpus lúc khởi động: {e}")

    app.state.pipeline = pipeline
    yield
    logger.info("Đang dừng dịch vụ University QA API...")


app = FastAPI(
    title="University QA System API",
    description="Hệ thống hỏi đáp đào tạo, tuyển sinh và quy chế đại học ứng dụng RAG tiên tiến.",
    version="0.1.0",
    lifespan=lifespan,
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(health_router)
app.include_router(qa_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

import threading
import time
from typing import Dict, List, Tuple

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from api.routes.health import router as health_router
from api.routes.qa import router as qa_router
from api.web_ui import CHAT_HTML_PAGE
from FPTUniQA.utils.config import config
from FPTUniQA.utils.logger import get_logger
from FPTUniQA.utils.metrics import metrics

logger = get_logger("FPTUniQA.api.main")


class RateLimiter:
    """Bộ giới hạn tần suất request (Sliding Window Rate Limiter) theo địa chỉ IP."""

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._lock = threading.Lock()
        self._history: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - 60.0
        with self._lock:
            timestamps = self._history.get(client_ip, [])
            valid_ts = [t for t in timestamps if t > window_start]
            if len(valid_ts) >= self.rpm:
                self._history[client_ip] = valid_ts
                retry_after = int(60.0 - (now - valid_ts[0])) + 1
                return False, max(1, retry_after)
            valid_ts.append(now)
            self._history[client_ip] = valid_ts
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._history.clear()


rate_limiter = RateLimiter(requests_per_minute=config.rate_limit_rpm)

app = FastAPI(
    title="FPT University Academic QA API",
    description="Hệ thống RAG giải đáp quy chế, học vụ và đào tạo Đại học FPT - Tuần 1",
    version="0.1.0",
)


# Middleware ghi log access, đo thời gian xử lý và kiểm soát bảo mật (Rate Limit & Payload Size)
@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    # 1. Kiểm tra kích thước payload (Max Payload Size Guard)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > config.max_payload_bytes:
        logger.warning(f"Từ chối request vượt dung lượng ({content_length} bytes > {config.max_payload_bytes})")
        return JSONResponse(
            status_code=413,
            content={"detail": "Payload Too Large: Dung lượng yêu cầu vượt quá giới hạn cho phép."},
        )

    # 2. Kiểm tra Rate Limiting theo IP (Bỏ qua health check và metrics)
    client_ip = request.client.host if request.client else "127.0.0.1"
    if request.url.path not in ["/healthz", "/health", "/api/v1/health", "/metrics"]:
        allowed, retry_after = rate_limiter.is_allowed(client_ip)
        if not allowed:
            logger.warning(f"Rate limit exceeded cho IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too Many Requests: Vượt quá giới hạn {config.rate_limit_rpm} req/phút. Thử lại sau {retry_after}s."},
                headers={"Retry-After": str(retry_after)},
            )

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
        metrics.record_request(
            route=request.url.path,
            latency_ms=duration_ms,
            success=response.status_code < 400,
        )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        logger.error(f"{request.method} {request.url.path} FAILED ({duration_ms}ms): {exc}")
        metrics.record_request(
            route=request.url.path,
            latency_ms=duration_ms,
            success=False,
        )
        raise exc


# Cấu hình CORS Whitelist chặt chẽ theo môi trường
cors_origins = list(config.cors_origins)
if config.environment.lower() != "production":
    cors_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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


@app.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def web_interface():
    """Giao diện Web Chat tương tác trực quan."""
    return CHAT_HTML_PAGE


@app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
async def prometheus_metrics():
    """Endpoint xuất thông số hiệu năng hệ thống định dạng Prometheus."""
    return metrics.export_prometheus()



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

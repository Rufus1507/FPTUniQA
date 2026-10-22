"""Integration tests cho FastAPI Backend Service (Contract 1)."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoints(client):
    """Kiểm tra các endpoint health check."""
    for path in ["/healthz", "/health", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"


def test_query_validation_error_missing_fields(client):
    """Kiểm tra mã lỗi 422 khi payload thiếu cả query lẫn question."""
    response = client.post("/api/v1/query", json={})
    assert response.status_code == 422


def test_query_validation_error_empty_string(client):
    """Kiểm tra mã lỗi 422 khi query rỗng hoàn toàn."""
    response = client.post("/api/v1/query", json={"query": ""})
    assert response.status_code == 422


@patch("api.routes.qa._pipeline_instance")
def test_query_success_with_mock_pipeline(mock_pipeline, client):
    """Kiểm tra gọi /api/v1/query thành công với mock RAG Pipeline."""
    mock_pipeline.answer.return_value = {
        "answer": "Điều kiện cảnh báo học vụ là ĐTBHK < 1.0 [Nguồn 1].",
        "citations": [
            {
                "doc_id": "FPTU-QC-001",
                "title": "Quy chế đào tạo ĐH FPT",
                "source": "Mục 4.1, trang 15",
            }
        ],
        "route": "rag_pipeline",
        "rewritten_query": "Điều kiện cảnh báo học vụ ĐH FPT",
        "session_id": "test-session-123",
        "possible_hallucination": False,
    }

    payload = {
        "query": "Điều kiện bị cảnh cáo học vụ là gì?",
        "session_id": "test-session-123",
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cảnh báo học vụ" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["doc_id"] == "FPTU-QC-001"
    assert data["route"] == "rag_pipeline"
    assert data["session_id"] == "test-session-123"


@patch("api.routes.qa._pipeline_instance")
def test_query_alias_endpoint(mock_pipeline, client):
    """Kiểm tra endpoint alias /query chuyển tiếp đúng."""
    mock_pipeline.answer.return_value = {
        "answer": "Học phí KTPM khóa 2026 là 28,700,000 VNĐ.",
        "citations": [],
        "route": "structured_lookup",
        "rewritten_query": None,
        "session_id": None,
        "possible_hallucination": False,
    }

    payload = {"question": "Học phí KTPM 2026?"}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "structured_lookup"
    assert "28,700,000" in data["answer"]


def test_payload_too_large(client):
    """Kiểm tra mã lỗi 413 khi dung lượng vượt quá giới hạn cấu hình."""
    response = client.post(
        "/api/v1/query",
        content=b"test" * 10,
        headers={"Content-Length": "99999999"},
    )
    assert response.status_code == 413
    assert "Payload Too Large" in response.json().get("detail", "")


def test_rate_limiting_exceeded(client):
    """Kiểm tra trả về 429 khi vượt quá rate limit."""
    from api.main import rate_limiter
    rate_limiter.reset()

    # Tạm thời đặt rpm nhỏ để kiểm tra
    original_rpm = rate_limiter.rpm
    rate_limiter.rpm = 3
    try:
        # Gửi 3 requests hợp lệ
        for _ in range(3):
            client.post("/query", json={})
        # Request thứ 4 phải bị chặn với 429
        resp = client.post("/query", json={})
        assert resp.status_code == 429
        assert "Too Many Requests" in resp.json().get("detail", "")
        assert "Retry-After" in resp.headers
    finally:
        rate_limiter.rpm = original_rpm
        rate_limiter.reset()


def test_cors_headers(client):
    """Kiểm tra phản hồi CORS preflight options."""
    response = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_metrics_endpoint(client):
    """Kiểm tra endpoint /metrics xuất dữ liệu Prometheus."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "fptuniqa_requests_total" in response.text


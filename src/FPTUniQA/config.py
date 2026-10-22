"""Hệ thống quản lý cấu hình tập trung cho FPTUniQA sử dụng Pydantic BaseSettings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"


class Settings(BaseSettings):
    """Cấu hình toàn diện cho hệ thống FPTUniQA, hỗ trợ nạp từ biến môi trường, .env và YAML."""

    model_config = SettingsConfigDict(
        env_file=str(_env_path) if _env_path.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Dự án & Môi trường
    project_name: str = Field(default="FPTUniQA", description="Tên dự án")
    version: str = Field(default="0.1.0", description="Phiên bản")
    environment: str = Field(default="development", description="Môi trường: development | staging | production")
    debug: bool = Field(default=False, description="Chế độ debug")

    # API Server
    api_host: str = Field(default="0.0.0.0", description="Host lắng nghe của FastAPI")
    api_port: int = Field(default=8000, description="Cổng lắng nghe của FastAPI")
    api_base_url: str = Field(default="http://localhost:8000", description="URL gốc của API")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"],
        description="Danh sách domain cho phép CORS",
    )
    rate_limit_rpm: int = Field(default=60, description="Số lượng request tối đa trong 1 phút cho mỗi IP")
    max_payload_bytes: int = Field(default=10485760, description="Kích thước payload tối đa (bytes, mặc định 10MB)")

    # LLM Provider
    llm_base_url: str = Field(default="http://localhost:20128/v1", description="Endpoint OpenAI-compatible LLM")
    llm_api_key: str = Field(default="", description="API Key cho LLM")
    anthropic_api_key: str = Field(default="", description="API Key cho Anthropic Claude")
    model_name: str = Field(default="gemini/gemini-3.5-flash-lite", description="Tên mô hình LLM")
    llm_timeout: float = Field(default=2.0, description="Timeout gọi LLM (giây)")

    # Retrieval & Reranking
    default_top_k: int = Field(default=5, description="Số lượng tài liệu truy xuất mặc định")
    score_threshold: float = Field(default=0.0, description="Ngưỡng điểm tối thiểu chấp nhận tài liệu")
    rerank_enabled: bool = Field(default=True, description="Kích hoạt Cross-Encoder Reranker")
    rerank_candidate_k: int = Field(default=20, description="Số ứng viên chuyển sang reranker")
    rerank_model_name: str = Field(default="BAAI/bge-reranker-base", description="Tên model Cross-Encoder")

    # Caching
    cache_enabled: bool = Field(default=True, description="Bật/tắt tầng bộ nhớ đệm truy xuất")
    cache_ttl_seconds: int = Field(default=3600, description="Thời gian sống (TTL) của cache")
    cache_max_entries: int = Field(default=1000, description="Dung lượng tối đa in-memory cache")
    cache_redis_url: Optional[str] = Field(default=None, description="URL kết nối Redis cache (tùy chọn)")

    # Thư mục dữ liệu & Logs
    log_dir: str = Field(default="logs", description="Thư mục ghi log")
    data_dir: str = Field(default="data", description="Thư mục chứa dữ liệu")

    @field_validator("api_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"Port không hợp lệ: {v}. Phải nằm trong khoảng [1, 65535].")
        return v

    @field_validator("api_base_url", "llm_base_url")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"URL không hợp lệ: {v}. Phải bắt đầu bằng http:// hoặc https://")
        return v

    @model_validator(mode="after")
    def validate_production_guards(self) -> "Settings":
        """Cảnh báo an toàn khi chạy trên môi trường production."""
        if self.environment.lower() == "production":
            if not self.llm_api_key and not self.anthropic_api_key:
                import warnings
                warnings.warn(
                    "CẢNH BÁO BẢO MẬT: Chạy ở chế độ production nhưng LLM_API_KEY và ANTHROPIC_API_KEY đều trống!",
                    UserWarning,
                )
        return self


# Nạp cấu hình singleton
settings = Settings()

"""Quản lý cấu hình tập trung cho toàn bộ ứng dụng bằng python-dotenv."""

import os
from dataclasses import dataclass
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent.parent
_env_path = _project_root / ".env"

try:
    from dotenv import load_dotenv
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
    else:
        load_dotenv()
except ImportError:
    # Đọc thủ công file .env nếu thư viện python-dotenv chưa được cài đặt
    if _env_path.exists():
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip("'\""))


@dataclass(frozen=True)
class AppConfig:
    """Đối tượng cấu hình duy nhất chứa tất cả các biến môi trường."""

    # Cấu hình API Server
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Cấu hình LLM Provider (OpenAI-compatible hoặc Anthropic)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:20128/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gemini/gemini-3.5-flash-lite")
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))

    # Cấu hình Retrieval & Pipeline
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    log_dir: str = os.getenv("LOG_DIR", "logs")


# Khởi tạo singleton Config dùng chung
config = AppConfig()

"""Quản lý cấu hình tập trung cho toàn bộ ứng dụng (Backward Compatibility layer)."""

from pathlib import Path
from typing import Any, Dict

from FPTUniQA.config import Settings, settings

_project_root = Path(__file__).resolve().parent.parent.parent.parent

# Tương thích ngược với các module sử dụng AppConfig và biến config
AppConfig = Settings
config = settings


def load_config(config_path: str = "configs/base.yaml") -> Dict[str, Any]:
    """Nạp cấu hình từ tệp YAML."""
    import yaml

    p = Path(config_path)
    if not p.is_absolute():
        p = _project_root / config_path
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


__all__ = ["Settings", "settings", "config", "AppConfig", "load_config"]

"""Đọc và hợp nhất các file cấu hình YAML."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def _deep_update(source: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Cập nhật đệ quy dict nguồn bằng các giá trị override."""
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            source[key] = _deep_update(source[key], value)
        else:
            source[key] = value
    return source


def load_config(
    config_path: Optional[str] = None,
    base_path: str = "configs/base.yaml",
) -> Dict[str, Any]:
    """Tải file cấu hình cơ sở và ghi đè bằng cấu hình môi trường tương ứng."""
    config: Dict[str, Any] = {}

    # Đọc base config
    if os.path.exists(base_path):
        with open(base_path, "r", encoding="utf-8") as f:
            base_config = yaml.safe_load(f) or {}
            config = base_config

    # Ghi đè bằng môi trường cụ thể nếu có
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            env_config = yaml.safe_load(f) or {}
            config = _deep_update(config, env_config)
    elif os.environ.get("ENVIRONMENT"):
        env_name = os.environ.get("ENVIRONMENT", "development")
        env_file = Path(f"configs/{env_name}.yaml")
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
                config = _deep_update(config, env_config)

    return config

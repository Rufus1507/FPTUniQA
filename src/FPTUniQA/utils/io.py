"""Tiện ích đọc và ghi file JSON, JSONL, TXT nhanh và an toàn."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Generator, List, Union


def read_json(path: Union[str, Path]) -> Any:
    """Đọc file JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: Any, path: Union[str, Path], indent: int = 2) -> None:
    """Ghi dữ liệu ra file JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def read_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Đọc toàn bộ file JSONL vào danh sách các dict."""
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def iter_jsonl(path: Union[str, Path]) -> Generator[Dict[str, Any], None, None]:
    """Duyệt qua từng dòng file JSONL dạng generator để tiết kiệm RAM."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(data: List[Dict[str, Any]], path: Union[str, Path], mode: str = "w") -> None:
    """Ghi danh sách dict ra file JSONL."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

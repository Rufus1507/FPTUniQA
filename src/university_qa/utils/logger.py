"""Hệ thống logging chuẩn ghi file JSONL phục vụ phân tích pipeline và kiểm thử."""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from university_qa.utils.config import config


class JSONLFormatter(logging.Formatter):
    """Formatter chuyển đổi bản ghi log sang định dạng dòng JSON (JSONL)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Nếu có đính kèm thông tin truy vấn RAG
        if hasattr(record, "query"):
            payload["query"] = getattr(record, "query")
        if hasattr(record, "latency_ms"):
            payload["latency_ms"] = getattr(record, "latency_ms")
        if hasattr(record, "status"):
            payload["status"] = getattr(record, "status")
        if hasattr(record, "extra_data"):
            payload["extra_data"] = getattr(record, "extra_data")

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str = "university_qa") -> logging.Logger:
    """Tạo hoặc lấy logger chuẩn đã được cấu hình StreamHandler và JSONL FileHandler."""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Đảm bảo console hỗ trợ bảng mã UTF-8 tiếng Việt trên Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler JSONL trong thư mục logs/
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = log_dir / "pipeline_events.jsonl"

    file_handler = logging.FileHandler(str(jsonl_path), encoding="utf-8")
    file_handler.setFormatter(JSONLFormatter())
    logger.addHandler(file_handler)

    return logger


def log_pipeline_event(
    query: str,
    latency_ms: float,
    status: str,
    message: str = "Pipeline query execution",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Ghi trực tiếp một sự kiện xử lý truy vấn RAG vào file log JSONL."""
    logger = get_logger("university_qa.pipeline_events")
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    setattr(record, "query", query)
    setattr(record, "latency_ms", round(latency_ms, 2))
    setattr(record, "status", status)
    logger.handle(record)


def log_query_event(
    original_query: str,
    rewritten_query: Optional[str] = None,
    parsed_query: Optional[Dict[str, Any]] = None,
    retrieved_docs: Optional[list] = None,
    reranked_docs: Optional[Any] = None,
    final_context: Optional[str] = None,
    citations: Optional[list] = None,
    answer: str = "",
    route_chosen: str = "unknown",
    answer_fallback: bool = False,
    possible_hallucination: bool = False,
    ungrounded_numbers: Optional[list] = None,
    fallback_triggered: Optional[bool] = None,
    session_id: Optional[str] = None,
    turn_index: Optional[int] = None,
    latency_ms: Optional[float] = None,
    timestamp: Optional[str] = None,
    # Tương thích ngược:
    retrieved_doc_ids: Optional[list] = None,
    scores: Optional[list] = None,
) -> Dict[str, Any]:
    """Ghi trực tiếp bản ghi Structured Log đầy đủ 7 trường cốt lõi vào logs/pipeline_events.jsonl.

    7 trường cốt lõi theo đúng kế hoạch gốc:
    1. original_query: Câu hỏi gốc người dùng nhập vào
    2. rewritten_query: Câu hỏi sau khi qua module Query Rewriting
    3. parsed_query: Kết quả cấu trúc từ Semantic Parser (Contract 3)
    4. retrieved_docs: Danh sách các tài liệu tìm kiếm được
    5. reranked_docs: Kết quả sau rerank (None / null vì chưa có TV2 bàn giao)
    6. final_context: Chuỗi ngữ cảnh tổng hợp đưa vào LLM
    7. citations: Danh sách trích dẫn nguồn
    """
    effective_fallback = answer_fallback if fallback_triggered is None else fallback_triggered
    payload = {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "turn_index": turn_index,
        # --- 7 TRƯỜNG CỐT LÕI (KẾ HOẠCH GỐC) ---
        "original_query": original_query,
        "rewritten_query": rewritten_query or original_query,
        "parsed_query": parsed_query or {},
        "retrieved_docs": retrieved_docs if retrieved_docs is not None else (retrieved_doc_ids or []),
        "reranked_docs": None,  # Ghi rõ: null vì chưa có TV2 bàn giao reranker
        "final_context": final_context or "",
        "citations": citations or [],
        # --- CÁC TRƯỜNG PHỤ TRỢ & GUARDRAIL TUẦN 6 ---
        "answer": answer,
        "route_chosen": route_chosen,
        "answer_fallback": effective_fallback,
        "possible_hallucination": possible_hallucination,
        "ungrounded_numbers": ungrounded_numbers or [],
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
    }
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = log_dir / "pipeline_events.jsonl"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def log_parsing_event(
    original_query: str,
    parsed_result: Dict[str, Any],
    route_chosen: str,
    latency_ms: float,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Ghi trực tiếp log sự kiện semantic parsing và routing vào logs/parsing_events.jsonl."""
    payload = {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "original_query": original_query,
        "parsed_result": parsed_result,
        "route_chosen": route_chosen,
        "latency_ms": round(latency_ms, 2),
    }
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = log_dir / "parsing_events.jsonl"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload

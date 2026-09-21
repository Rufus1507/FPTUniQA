"""Module Semantic Parsing chuyển đổi câu hỏi tự nhiên thành truy vấn có cấu trúc (Contract 3). Phụ trách: TV3.

Chiến lược:
1. LLM Structured Output (Chính): Gọi LLM sinh JSON có cấu trúc gồm intent, slots, confidence.
2. Regex / Rule-based (Fallback): Tự động kích hoạt khi lời gọi LLM gặp lỗi (mạng, JSON hỏng, thiếu field).
"""

import json
import re
from typing import Any, Dict, Optional
import requests

from contracts import ParsedQuery
from university_qa.query.intent import QueryIntent, SUPPORTED_INTENTS
from university_qa.query.normalizer import normalize_query
from university_qa.utils.config import config
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.query.semantic_parser")

# System Prompt chỉ thị LLM trích xuất intent và slots chuẩn xác
PARSER_SYSTEM_PROMPT = """Bạn là bộ phân tích ngữ nghĩa (Semantic Parser) cho hệ thống hỏi đáp quy chế học vụ Đại học FPT.
Nhiệm vụ của bạn là đọc câu hỏi của sinh viên và trích xuất thông tin cấu trúc dưới dạng duy nhất một đối tượng JSON hợp lệ theo lược đồ:

{
  "intent": "policy_lookup" | "tuition_lookup" | "graduation_lookup" | "OOD",
  "slots": {
    "program": "string hoặc null (ví dụ: AI, CNTT, KTPM)",
    "cohort": "string hoặc null (ví dụ: 2026, 2023, K18)",
    "topic": "string hoặc null (ví dụ: canh_bao_hoc_vu, tot_nghiep, hoc_phi, hoc_bong)",
    "target": "string hoặc null (ví dụ: dieu_kien, muc_phi, ty_le_vang)"
  },
  "confidence": float (từ 0.0 đến 1.0)
}

Quy tắc phân loại:
1. "tuition_lookup": Các câu hỏi về học phí, tiền học, chi phí theo ngành hoặc theo khóa.
2. "graduation_lookup": Các câu hỏi về điều kiện tốt nghiệp, chuẩn ngoại ngữ ra trường, đồ án Capstone.
3. "policy_lookup": Các câu hỏi về quy chế học vụ, cảnh cáo, điểm thi, môn tiên quyết, học bổng.
4. "OOD": Các câu hỏi ngoài phạm vi đào tạo ĐH FPT (thời tiết, trường đại học khác, đời sống, nấu ăn...).

CHÚ Ý QUAN TRỌNG: Chỉ trả về duy nhất chuỗi JSON thuần túy (không bọc trong markdown ```json, không thêm văn bản phụ trợ)."""


def _parse_with_llm(question: str) -> Optional[Dict[str, Any]]:
    """Gọi LLM qua OpenAI-compatible API để trích xuất intent và slots có cấu trúc."""
    base_url = config.llm_base_url
    api_key = config.llm_api_key
    model_name = config.model_name
    timeout = config.llm_timeout or 30

    if not base_url or not api_key:
        logger.warning("Chưa cấu hình LLM_BASE_URL hoặc LLM_API_KEY. Chuyển sang fallback.")
        return None

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Câu hỏi: {question}"},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
        "stream": False,
    }

    try:
        res = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        logger.info(f"LLM Status Code: {res.status_code}")

        if res.status_code != 200 or not res.text or not res.text.strip():
            logger.warning(f"LLM API trả về lỗi hoặc body rỗng (status {res.status_code}).")
            return None

        raw_text = res.text.strip()
        raw_content = ""

        # Trường hợp 1: Proxy trả về Server-Sent Events (SSE stream: data: {...})
        if "data:" in raw_text:
            for line in raw_text.splitlines():
                line = line.strip()
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data:"):
                    chunk_str = line[5:].strip()
                    try:
                        chunk = json.loads(chunk_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content_piece = delta.get("content") or ""
                        raw_content += content_piece
                    except Exception:
                        continue
        else:
            # Trường hợp 2: Proxy trả về đối tượng JSON hoàn chỉnh
            data = res.json()
            message = data["choices"][0]["message"]
            raw_content = message.get("content") or ""
            if not raw_content and "reasoning_content" in message:
                raw_content = message["reasoning_content"]

        raw_content = raw_content.strip()
        # Làm sạch nếu LLM lỡ bọc trong markdown code block
        raw_content = re.sub(r"^```json\s*", "", raw_content)
        raw_content = re.sub(r"\s*```$", "", raw_content).strip()

        if not raw_content:
            logger.warning("Không thể trích xuất nội dung văn bản từ phản hồi LLM.")
            return None

        parsed_json = json.loads(raw_content)

        # Kiểm tra tính hợp lệ của JSON
        if "intent" in parsed_json and parsed_json["intent"] in SUPPORTED_INTENTS:
            intent = parsed_json["intent"]
            slots = parsed_json.get("slots", {})
            # Sửa bug OOD slot-leak: nếu intent là OOD thì slots bắt buộc phải rỗng ({})
            if intent == QueryIntent.OOD.value:
                slots = {}

            return {
                "intent": intent,
                "slots": slots,
                "confidence": float(parsed_json.get("confidence", 0.95)),
                "model_used": model_name,
                "raw_content": raw_content,
            }
        else:
            logger.warning(f"LLM trả về intent không hợp lệ: {parsed_json.get('intent')}")
            return None
    except Exception as exc:
        logger.warning(f"Lỗi khi gọi LLM cho Semantic Parsing: {exc}. Kích hoạt fallback.")
        return None


def _parse_with_regex(question: str) -> Dict[str, Any]:
    """Phân tích dự phòng bằng Regex / Rule-based khi LLM gặp sự cố."""
    q_lower = question.lower()
    slots: Dict[str, Any] = {}

    # 1. Kiểm tra OOD (các chủ đề ngoài miền học vụ FPT)
    ood_keywords = ["thời tiết", "bách khoa", "kinh tế quốc dân", "quốc gia", "nấu ăn", "phở bò", "du lịch", "bóng đá"]
    if any(kw in q_lower for kw in ood_keywords):
        return {
            "intent": QueryIntent.OOD.value,
            "slots": {},
            "confidence": 0.90,
        }

    # 2. Kiểm tra tuition_lookup (Học phí / tín chỉ)
    if any(kw in q_lower for kw in ["học phí", "tiền học", "chi phí", "tín chỉ"]):
        # Trích xuất ngành học
        if "ai" in q_lower or "trí tuệ nhân tạo" in q_lower:
            slots["program"] = "AI"
        elif "cntt" in q_lower or "công nghệ thông tin" in q_lower:
            slots["program"] = "CNTT"
        elif "ktpm" in q_lower or "kỹ thuật phần mềm" in q_lower:
            slots["program"] = "KTPM"

        # Trích xuất khóa tuyển sinh
        cohort_match = re.search(r"\b(202[0-9]|203[0-9]|k1[0-9]|k2[0-9])\b", q_lower)
        if cohort_match:
            slots["cohort"] = cohort_match.group(1).upper()

        return {
            "intent": QueryIntent.TUITION_LOOKUP.value,
            "slots": slots,
            "confidence": 0.85,
        }

    # 3. Kiểm tra graduation_lookup (Điều kiện tốt nghiệp)
    if any(kw in q_lower for kw in ["tốt nghiệp", "ra trường", "chuẩn đầu ra", "đồ án", "khóa luận", "capstone", "sep490"]):
        if "đồ án" in q_lower or "capstone" in q_lower or "khóa luận" in q_lower:
            slots["topic"] = "do_an_capstone"
        else:
            slots["topic"] = "tot_nghiep"
        slots["target"] = "dieu_kien"

        return {
            "intent": QueryIntent.GRADUATION_LOOKUP.value,
            "slots": slots,
            "confidence": 0.85,
        }

    # 4. Kiểm tra policy_lookup (Quy chế học vụ)
    if any(kw in q_lower for kw in ["cảnh cáo", "cảnh báo", "học vụ", "tiên quyết", "thi lại", "học lại", "chuyên cần", "vắng", "điểm liệt", "học bổng"]):
        if "cảnh cáo" in q_lower or "cảnh báo" in q_lower:
            slots["topic"] = "canh_bao_hoc_vu"
            slots["target"] = "dieu_kien"
        elif "chuyên cần" in q_lower or "vắng" in q_lower:
            slots["topic"] = "chuyen_can"
            slots["target"] = "ty_le_vang"
        elif "học bổng" in q_lower:
            slots["topic"] = "hoc_bong"
            slots["target"] = "dieu_kien"
        else:
            slots["topic"] = "quy_che_chung"

        return {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "slots": slots,
            "confidence": 0.80,
        }

    # Mặc định rơi vào OOD nếu không khớp bất kỳ mẫu học vụ nào
    return {
        "intent": QueryIntent.OOD.value,
        "slots": {},
        "confidence": 0.40,
    }


def parse_query(question: str) -> ParsedQuery:
    """Chuyển đổi câu hỏi của sinh viên thành đối tượng ParsedQuery (Contract 3) và ghi log parsing_events.jsonl.

    Ưu tiên 1: LLM Structured Output.
    Ưu tiên 2: Regex Fallback nếu LLM thất bại.
    """
    import time
    from university_qa.query.router import route_query
    from university_qa.utils.logger import log_parsing_event

    start_time = time.time()
    clean_query = normalize_query(question)

    # 1. Thử phân tích bằng LLM Structured Output
    llm_result = _parse_with_llm(question)

    if llm_result:
        parsed = ParsedQuery(
            intent=llm_result["intent"],
            slots=llm_result.get("slots", {}),
            confidence=llm_result["confidence"],
            parser_method="llm_structured_output",
            fallback_used=False,
            original_query=question,
            normalized_query=clean_query,
        )
    else:
        # 2. Tự động rơi về Regex Fallback khi LLM thất bại
        logger.info(f"Kích hoạt Regex Fallback cho câu hỏi: '{question}'")
        regex_result = _parse_with_regex(clean_query)

        parsed = ParsedQuery(
            intent=regex_result["intent"],
            slots=regex_result.get("slots", {}),
            confidence=regex_result["confidence"],
            parser_method="regex_fallback",
            fallback_used=True,
            original_query=question,
            normalized_query=clean_query,
        )

    # Đo latency và điều phối router
    latency_ms = (time.time() - start_time) * 1000.0
    route_chosen, _ = route_query(parsed)

    # Ghi log sự kiện phân tích cú pháp vào logs/parsing_events.jsonl (phục vụ Tuần 7)
    log_parsing_event(
        original_query=question,
        parsed_result=parsed.model_dump(),
        route_chosen=route_chosen,
        latency_ms=latency_ms,
    )

    return parsed

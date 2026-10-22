"""Module viết lại câu hỏi theo ngữ cảnh hội thoại đa lượt (Query Rewriting). Phụ trách: TV3.

Nhiệm vụ cốt lõi:
- Đứng trước Semantic Parser trong dòng chảy Pipeline.
- Tiếp nhận câu hỏi hiện tại và lịch sử hội thoại (session context).
- Sử dụng LLM để giải quyết hiện tượng đồng tham chiếu (coreference) và tỉnh lược (ellipsis),
  viết lại câu hỏi thành dạng đầy đủ, độc lập ngữ cảnh trước khi phân tích cú pháp.
"""

import json
import re
from typing import Any, Dict, List, Optional
import requests

from FPTUniQA.utils.config import config
from FPTUniQA.utils.exceptions import CircuitBreaker, CircuitBreakerOpenError
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.query.rewriting")
_rewriter_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0, name="rewriter_llm")

REWRITER_SYSTEM_PROMPT = """Bạn là trợ lý chuyên viết lại câu hỏi (Query Rewriter) trong hệ thống hỏi đáp học vụ Đại học FPT.
Nhiệm vụ của bạn: Dựa vào lịch sử hội thoại, viết lại câu hỏi hiện tại của sinh viên thành một câu hỏi duy nhất, độc lập, rõ ràng và đầy đủ ngữ cảnh (tự chứa đầy đủ thông tin: ngành học, khóa tuyển sinh, chủ đề học vụ).

Quy tắc bắt buộc:
1. Nếu câu hỏi hiện tại thiếu thông tin hoặc dùng đại từ thay thế (ví dụ: "còn năm 2023 thì sao?", "thế ngành CNTT thì sao?", "nếu bị 3 lần thì sao?", "khóa 2024 nhé"), hãy bổ sung đầy đủ ngành học, khóa học hoặc chủ đề từ lịch sử hội thoại.
2. Nếu câu hỏi hiện tại đã đầy đủ thông tin độc lập, hãy giữ nguyên nội dung.
3. KHÔNG trả lời câu hỏi.
4. KHÔNG thêm lời giải thích, lời chào hoặc bất kỳ văn bản phụ trợ nào.
5. Chỉ trả về DUY NHẤT một câu hỏi đã viết lại trên một dòng."""


def _call_llm_rewriter(prompt: str) -> Optional[str]:
    """Gọi LLM qua endpoint cục bộ để viết lại câu hỏi."""
    base_url = config.llm_base_url
    api_key = config.llm_api_key
    model_name = config.model_name
    timeout = config.llm_timeout or 30

    if not base_url or not api_key:
        logger.warning("Chưa cấu hình LLM_BASE_URL hoặc LLM_API_KEY. Bỏ qua rewriting.")
        return None

    # Kiểm tra trạng thái Circuit Breaker
    try:
        _rewriter_breaker._check_state()
    except CircuitBreakerOpenError:
        return None

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": REWRITER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 512,
        "stream": False,
    }

    try:
        res = requests.post(endpoint, headers=headers, json=payload, timeout=min(timeout, 10))
        if res.status_code != 200 or not res.text or not res.text.strip():
            logger.warning(f"LLM Rewriter trả về lỗi hoặc rỗng (status {res.status_code}).")
            _rewriter_breaker._on_failure(Exception(f"HTTP {res.status_code}"))
            return None

        _rewriter_breaker._on_success()

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
        # Loại bỏ các tiền tố thường gặp nếu LLM lỡ sinh ra
        raw_content = re.sub(r"^(Câu hỏi viết lại|Câu hỏi sau khi viết lại|Rewritten Query):\s*", "", raw_content, flags=re.IGNORECASE)
        # Loại bỏ dấu ngoặc kép bọc ngoài nếu có
        if raw_content.startswith('"') and raw_content.endswith('"') and len(raw_content) > 1:
            raw_content = raw_content[1:-1].strip()

        return raw_content if raw_content else None
    except Exception as exc:
        _rewriter_breaker._on_failure(exc)
        logger.warning(f"Lỗi khi gọi LLM Rewriter: {exc}. Chuyển sang fallback theo luật.")
        return None


TOPIC_PATTERNS = {
    "tuition": [
        "học phí", "chi phí", "tiền học", "mức thu", "lệ phí", "nộp tiền",
        "kỳ định hướng", "học lại", "thi lại", "phí ký túc", "giá tín chỉ"
    ],
    "graduation": [
        "tốt nghiệp", "chuẩn đầu ra", "xét tốt nghiệp", "bằng tốt nghiệp",
        "tín chỉ tích lũy", "đồ án tốt nghiệp", "khóa luận", "chứng chỉ tiếng anh", "toeic", "ielts"
    ],
    "ojt_internship": [
        "ojt", "thực tập", "doanh nghiệp", "kỳ thực tập", "đi ojt"
    ],
    "discipline_warning": [
        "cảnh báo", "kỷ luật", "đình chỉ", "buộc thôi học", "học vụ",
        "điểm f", "nợ môn", "quá hạn", "vi phạm quy chế"
    ],
    "exam_appeal": [
        "phúc khảo", "khiếu nại", "chấm lại", "bài thi", "thời hạn phúc khảo", "lệ phí phúc khảo"
    ],
    "dormitory_campus": [
        "ký túc xá", "ktx", "phòng trọ", "nội trú", "xe buýt"
    ],
    "scholarship": [
        "học bổng", "tài trợ", "nguyễn văn đạo", "duy trì học bổng"
    ],
    "curriculum_credits": [
        "khung chương trình", "số tín chỉ", "tiến độ", "rút môn", "đăng ký môn", "chuyển ngành", "bảo lưu"
    ],
    "ood": [
        "thời tiết", "món ăn", "nấu ăn", "phở bò", "du lịch", "ca sĩ",
        "bóng đá", "thủ đô", "tổng thống", "quán cà phê", "chơi game", "phim ảnh"
    ],
}

CONTINUATION_PATTERNS = [
    r"^(thế\s+)?còn\b",
    r"^vậy\s+(nếu|thì|còn)\b",
    r"^nếu\s+(vậy|thế|bị|học)\b",
    r"^(ở|tại)\s+(đó|đấy|cơ sở|campus)\b",
    r"^(ngành|khóa|năm)\s+(đó|đấy|này)\b",
    r"\b(thì\s+sao|thế\s+nào|bao\s+nhiêu)\??$",
    r"^(bao\s+nhiêu|khi\s+nào|ở\s+đâu)\??$",
    r"\bở\s+(hà\s+nội|cần\s+thơ|đà\s+nẵng|hồ\s+chí\s+minh|quy\s+nhơn)\s+thì\s+sao\b",
    r"\bcòn\s+(hà\s+nội|cần\s+thơ|đà\s+nẵng|hồ\s+chí\s+minh|quy\s+nhơn|hcm|hn|ct|dn|qn)\b",
    r"\bcòn\s+(k\d{2}|khóa\s+\d{2})\b",
    r"\bcòn\s+ngành\s+[\w\s]+\s+thì\s+sao\b",
]


def detect_topic_from_text(text: str) -> str:
    """Xác định chủ đề chính của câu dựa trên từ khóa."""
    t_lower = text.lower()
    for topic, keywords in TOPIC_PATTERNS.items():
        if any(kw in t_lower for kw in keywords):
            return topic
    return "general_policy"


def is_continuation_query(query: str) -> bool:
    """Kiểm tra xem câu hỏi có dấu hiệu tỉnh lược/hỏi tiếp lượt trước hay không."""
    q_clean = query.strip().lower()
    for pattern in CONTINUATION_PATTERNS:
        if re.search(pattern, q_clean, flags=re.IGNORECASE):
            return True
    # Câu ngắn dưới 5 từ và không chứa chủ ngữ độc lập
    words = q_clean.split()
    if len(words) <= 4 and any(w in q_clean for w in ["còn", "sao", "thế", "vậy", "nào"]):
        return True
    return False


def detect_topic_switch(
    current_question: str,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Phát hiện xem lượt hiện tại có chuyển sang chủ đề khác (Topic Switch) hay không.
    
    Trả về dict:
        - is_topic_switch: bool
        - current_topic: str
        - previous_topic: Optional[str]
        - confidence: float
    """
    if not history:
        return {
            "is_topic_switch": False,
            "current_topic": detect_topic_from_text(current_question),
            "previous_topic": None,
            "confidence": 1.0,
        }

    # Nếu câu hỏi có dấu hiệu tỉnh lược/kế thừa rõ rệt -> KHÔNG phải topic switch
    if is_continuation_query(current_question):
        return {
            "is_topic_switch": False,
            "current_topic": detect_topic_from_text(current_question),
            "previous_topic": detect_topic_from_text(history[-1].get("query", "")),
            "confidence": 0.95,
        }

    curr_topic = detect_topic_from_text(current_question)

    # Lấy chủ đề các lượt trước
    prev_topics = []
    for turn in history:
        prev_q = turn.get("query") or turn.get("rewritten_query") or ""
        prev_topics.append(detect_topic_from_text(prev_q))

    last_topic = prev_topics[-1] if prev_topics else "general_policy"

    # Nếu câu hỏi hiện tại có chủ đề xác định và khác hoàn toàn chủ đề trước đó
    if curr_topic != "general_policy" and last_topic != "general_policy" and curr_topic != last_topic:
        return {
            "is_topic_switch": True,
            "current_topic": curr_topic,
            "previous_topic": last_topic,
            "confidence": 0.9,
        }

    # Nếu câu hỏi hiện tại là OOD
    if curr_topic == "ood":
        return {
            "is_topic_switch": True,
            "current_topic": "ood",
            "previous_topic": last_topic,
            "confidence": 0.99,
        }

    # Nếu câu hỏi độc lập dài (trên 7 từ), có đầy đủ chủ ngữ vị ngữ và không tham chiếu
    q_words = current_question.strip().split()
    if len(q_words) >= 8 and not is_continuation_query(current_question) and curr_topic != last_topic:
        return {
            "is_topic_switch": True,
            "current_topic": curr_topic,
            "previous_topic": last_topic,
            "confidence": 0.85,
        }

    return {
        "is_topic_switch": False,
        "current_topic": curr_topic,
        "previous_topic": last_topic,
        "confidence": 0.7,
    }


def _rule_based_rewrite(clean_q: str, history: List[Dict[str, Any]]) -> Optional[str]:
    """Fallback viết lại câu hỏi theo luật khi LLM không khả dụng (cho test và môi trường offline)."""
    if not history:
        return clean_q

    last_turn = history[-1]
    prev_q = last_turn.get("rewritten_query") or last_turn.get("query") or ""
    q_lower = clean_q.lower()

    # Trích xuất thực thể từ lượt trước
    cohort_match = re.search(r"\b(K1[7-9]|K2[0-2]|202[0-6])\b", prev_q, re.IGNORECASE)
    prev_cohort = cohort_match.group(0) if cohort_match else ""

    campus_match = re.search(r"\b(Hà Nội|TP\.?\s*Hồ Chí Minh|Đà Nẵng|Cần Thơ|Quy Nhơn|FUHL|HN|HCM|DN|CT|QN)\b", prev_q, re.IGNORECASE)
    prev_campus = campus_match.group(0) if campus_match else ""

    # Nhận diện ngành từ lượt trước
    majors = ["Công nghệ thông tin", "Kỹ thuật phần mềm", "Trí tuệ nhân tạo", "An toàn thông tin",
              "Khoa học dữ liệu", "Quản trị kinh doanh", "Marketing", "Kinh doanh quốc tế",
              "Truyền thông đa phương tiện", "Ngôn ngữ Anh", "Ngôn ngữ Nhật", "Ngôn ngữ Hàn",
              "CNTT", "KTPM", "AI", "ATTT", "KHDL", "QTKD"]
    prev_major = ""
    for m in majors:
        if m.lower() in prev_q.lower():
            prev_major = m
            break

    # Trường hợp 1: Đổi campus ("Còn ở Cần Thơ thì sao?", "Còn Đà Nẵng?", "Nếu học ở Quy Nhơn thì có rẻ hơn không?")
    new_campus_match = re.search(r"\b(ở\s+)?(Hà Nội|TP\.?\s*Hồ Chí Minh|Đà Nẵng|Cần Thơ|Quy Nhơn)\b", clean_q, re.IGNORECASE)
    if new_campus_match and ("còn" in q_lower or "thế" in q_lower or "thì sao" in q_lower or "nếu" in q_lower or "rẻ hơn" in q_lower or "đắt hơn" in q_lower):
        new_campus = new_campus_match.group(2)
        base_topic = "Học phí" if "học phí" in prev_q.lower() else "Quy chế"
        parts = [base_topic]
        if prev_cohort:
            parts.append(prev_cohort)
        if prev_major:
            parts.append(f"ngành {prev_major}")
        parts.append(f"tại {new_campus}")
        return " ".join(parts) + " là bao nhiêu?"

    # Trường hợp 2: Đổi khóa ("Còn K21 thì sao?", "Còn khóa 2024?")
    new_cohort_match = re.search(r"\b(K1[7-9]|K2[0-2]|202[0-6])\b", clean_q, re.IGNORECASE)
    if new_cohort_match and ("còn" in q_lower or "thế" in q_lower or "thì sao" in q_lower):
        new_cohort = new_cohort_match.group(1)
        base_topic = "Học phí" if "học phí" in prev_q.lower() else "Quy chế"
        parts = [base_topic, new_cohort]
        if prev_major:
            parts.append(f"ngành {prev_major}")
        if prev_campus:
            parts.append(f"tại {prev_campus}")
        return " ".join(parts) + " là bao nhiêu?"

    # Trường hợp 3: Đổi ngành ("Thế còn ngành Trí tuệ nhân tạo?")
    for m in majors:
        if m.lower() in clean_q.lower() and ("còn" in q_lower or "thế" in q_lower):
            base_topic = "Học phí" if "học phí" in prev_q.lower() else "Quy chế"
            parts = [base_topic]
            if prev_cohort:
                parts.append(prev_cohort)
            parts.append(f"ngành {m}")
            if prev_campus:
                parts.append(f"tại {prev_campus}")
            return " ".join(parts) + " là bao nhiêu?"

    # Trường hợp 4: Tham chiếu đại từ "ngành này"
    if "ngành này" in q_lower and prev_major:
        return clean_q.replace("ngành này", f"ngành {prev_major}")

    # Trường hợp 5: Tham chiếu môn học ("môn này", "môn đó", "học phần này")
    course_match = re.search(r"\b([A-Z]{3}\d{3}[a-z]?)\b", prev_q)
    if course_match:
        prev_course = course_match.group(1).upper()
        for p in ["môn này", "môn đó", "học phần này", "học phần đó", "môn ấy"]:
            if p in q_lower:
                return clean_q.replace(p, f"Môn {prev_course}")

    return None


def rewrite_query(current_question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Viết lại câu hỏi hiện tại dựa trên toàn bộ lịch sử hội thoại để tạo thành câu hỏi tự chứa đầy đủ ngữ cảnh.
    Tự động phát hiện Topic Switch để ngăn chặn nhiễm độc ngữ cảnh cũ (Context Bleeding).
    """
    clean_q = current_question.strip()
    if not clean_q:
        return ""

    if not history:
        logger.debug(f"Không có lịch sử hội thoại. Giữ nguyên câu hỏi: '{clean_q}'")
        return clean_q

    # Bước phát hiện chuyển đổi chủ đề (Topic Switch Detection)
    topic_switch_info = detect_topic_switch(clean_q, history)
    if topic_switch_info["is_topic_switch"]:
        logger.info(
            f"Phát hiện TOPIC SWITCH: '{topic_switch_info.get('previous_topic')}' -> "
            f"'{topic_switch_info.get('current_topic')}'. Giữ nguyên câu hỏi độc lập, không ghép ngữ cảnh cũ."
        )
        return clean_q

    # Xây dựng ngữ cảnh từ toàn bộ các lượt hội thoại trước (tối đa 5 lượt)
    recent_history = history[-5:]
    history_lines = []
    for idx, turn in enumerate(recent_history, start=1):
        q = turn.get("query") or turn.get("rewritten_query") or ""
        a = turn.get("answer") or ""
        short_a = a[:150] + "..." if len(a) > 150 else a
        history_lines.append(f"Lượt {idx}:")
        history_lines.append(f"- Sinh viên: {q}")
        if short_a:
            history_lines.append(f"- Trợ lý: {short_a}")

    history_text = "\n".join(history_lines)
    user_prompt = (
        f"Lịch sử hội thoại trước đó:\n{history_text}\n\n"
        f"Câu hỏi hiện tại của sinh viên: {clean_q}\n"
        f"Câu hỏi viết lại đầy đủ ngữ cảnh:"
    )

    logger.info(f"Bắt đầu viết lại câu hỏi: '{clean_q}' với lịch sử {len(recent_history)} lượt.")
    rewritten = _call_llm_rewriter(user_prompt)

    if rewritten:
        logger.info(f"Viết lại thành công qua LLM: '{clean_q}' -> '{rewritten}'")
        return rewritten

    # Fallback quy tắc nếu LLM offline / mock
    rule_rewritten = _rule_based_rewrite(clean_q, history)
    if rule_rewritten:
        logger.info(f"Viết lại thành công qua Rule Fallback: '{clean_q}' -> '{rule_rewritten}'")
        return rule_rewritten

    logger.info(f"Giữ nguyên câu hỏi gốc: '{clean_q}'")
    return clean_q

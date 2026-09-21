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

from university_qa.utils.config import config
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.query.rewriting")

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
        res = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        if res.status_code != 200 or not res.text or not res.text.strip():
            logger.warning(f"LLM Rewriter trả về lỗi hoặc rỗng (status {res.status_code}).")
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
        # Loại bỏ các tiền tố thường gặp nếu LLM lỡ sinh ra
        raw_content = re.sub(r"^(Câu hỏi viết lại|Câu hỏi sau khi viết lại|Rewritten Query):\s*", "", raw_content, flags=re.IGNORECASE)
        # Loại bỏ dấu ngoặc kép bọc ngoài nếu có
        if raw_content.startswith('"') and raw_content.endswith('"') and len(raw_content) > 1:
            raw_content = raw_content[1:-1].strip()

        return raw_content if raw_content else None
    except Exception as exc:
        logger.warning(f"Lỗi khi gọi LLM Rewriter: {exc}. Giữ nguyên câu hỏi gốc.")
        return None


def rewrite_query(current_question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Viết lại câu hỏi hiện tại dựa trên lịch sử hội thoại để tạo thành câu hỏi tự chứa đầy đủ ngữ cảnh.

    Tham số:
        current_question: Câu hỏi hiện tại của sinh viên.
        history: Danh sách các lượt hội thoại trước đó (gồm query, answer, parsed_query).

    Trả về:
        str: Câu hỏi đã được viết lại (hoặc giữ nguyên câu hỏi gốc nếu là lượt đầu hoặc LLM lỗi).
    """
    clean_q = current_question.strip()
    if not clean_q:
        return ""

    # Nếu không có lịch sử hội thoại (lượt 1), giữ nguyên câu hỏi gốc, không tốn tài nguyên gọi LLM
    if not history:
        logger.debug(f"Không có lịch sử hội thoại. Giữ nguyên câu hỏi: '{clean_q}'")
        return clean_q

    # Xây dựng ngữ cảnh từ các lượt hội thoại trước (tối đa 3 lượt gần nhất)
    recent_history = history[-3:]
    history_lines = []
    for idx, turn in enumerate(recent_history, start=1):
        q = turn.get("query") or turn.get("rewritten_query") or ""
        a = turn.get("answer") or ""
        # Rút gọn câu trả lời nếu quá dài để tiết kiệm context
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
        logger.info(f"Viết lại thành công: '{clean_q}' -> '{rewritten}'")
        return rewritten
    else:
        logger.info(f"Rewriting thất bại hoặc rỗng. Giữ nguyên: '{clean_q}'")
        return clean_q

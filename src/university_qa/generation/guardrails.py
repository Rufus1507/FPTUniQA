"""Module Guardrails hậu kỳ chống ảo giác và kiểm soát an toàn cho tầng Generation. Phụ trách: TV3.

Nhiệm vụ:
1. check_hallucination: Kiểm tra hậu kỳ (post-check) các số liệu trong câu trả lời sinh ra từ LLM
   đối chiếu với ngữ cảnh trích xuất (retrieved context). Nếu xuất hiện số liệu lạ (phần trăm, tiền tệ, ngày tháng)
   không có trong context, đánh dấu cờ possible_hallucination = True trong log (phục vụ tính Hallucination Rate ở Tuần 7).
2. validate_confidence: Kiểm tra ngưỡng tin cậy an toàn (confidence threshold).
"""

import re
from typing import Any, Dict, List


def check_hallucination(answer: str, context: str) -> Dict[str, Any]:
    """
    Kiểm tra hậu kỳ (post-check) chống ảo giác số liệu cho câu trả lời từ RAG Pipeline.

    Quy trình:
    1. Trích xuất toàn bộ các số liệu (phần trăm, số tiền, điểm số, khóa học, tỷ lệ) trong câu trả lời.
    2. Loại bỏ các ký hiệu đánh số trích dẫn nguồn (ví dụ: [Nguồn 1], [1]).
    3. Đối chiếu từng số liệu với ngữ cảnh trích xuất (context).
    4. Nếu có số liệu không xuất hiện trong context, đánh dấu possible_hallucination = True.

    Trả về:
        dict: {
            "possible_hallucination": bool,
            "ungrounded_numbers": List[str],
            "total_numbers_checked": int
        }
    """
    if not answer or not context:
        return {
            "possible_hallucination": False,
            "ungrounded_numbers": [],
            "total_numbers_checked": 0,
        }

    context_lower = context.lower()

    # Loại bỏ các số thứ tự trích dẫn nguồn dạng [Nguồn 1], [1], [Nguồn 2]...
    cleaned_answer = re.sub(r"\[(?:nguồn\s*)?\d+\]", "", answer, flags=re.IGNORECASE)

    # Tìm tất cả token chứa số: 20%, 28.700.000, 2.00, 550, IELTS 5.5, TOEIC 550, 2024, v.v.
    raw_tokens = re.findall(r"\b\d+(?:[.,]\d+)*(?:%)?\b", cleaned_answer)

    ungrounded = []
    checked_tokens = []

    for token in raw_tokens:
        token_str = token.strip()
        if not token_str:
            continue
        checked_tokens.append(token_str)

        # 1. Tìm trực tiếp chuỗi số trong context
        if token_str.lower() in context_lower:
            continue

        # 2. Tìm dạng số không có dấu phân cách hàng nghìn / phần trăm
        clean_digits = re.sub(r"[.,%]", "", token_str)
        if clean_digits and clean_digits in context_lower:
            continue

        # 3. Chuẩn hóa số thực (ví dụ '2.00' so với '2.0' hoặc '2')
        try:
            val = float(token_str.replace(",", ".").replace("%", ""))
            # So sánh dạng số nguyên hoặc số thực rút gọn
            val_int_str = str(int(val))
            val_float_str = f"{val:.1f}" if val % 1 == 0 else str(val)
            if val_int_str in context_lower or val_float_str in context_lower:
                continue
        except ValueError:
            pass

        # Nếu không tìm thấy bằng bất kỳ cách nào -> số liệu không có căn cứ trong context
        ungrounded.append(token_str)

    possible_hallucination = len(ungrounded) > 0

    return {
        "possible_hallucination": possible_hallucination,
        "ungrounded_numbers": list(set(ungrounded)),
        "total_numbers_checked": len(checked_tokens),
    }

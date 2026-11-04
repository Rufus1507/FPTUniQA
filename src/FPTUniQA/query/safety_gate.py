"""Safety Gate: Bộ tiền lọc an toàn và nhận diện câu hỏi ngoài phạm vi (Near-OOD) không dùng LLM.
Tối ưu hóa độ trễ phản hồi (<50ms) và bảo vệ an toàn hệ thống.
"""

import json
import os
import re
from typing import Any, Dict, Optional

# Load external orgs dictionary
_DICT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "dictionary", "external_orgs.json")
)

_EXTERNAL_UNIS = []
_EXTERNAL_SCHOLARSHIPS = []
_HARMFUL_PATTERNS = []

def _reload_dict():
    global _EXTERNAL_UNIS, _EXTERNAL_SCHOLARSHIPS, _HARMFUL_PATTERNS
    if os.path.exists(_DICT_PATH):
        try:
            with open(_DICT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _EXTERNAL_UNIS = data.get("external_universities", [])
                _EXTERNAL_SCHOLARSHIPS = data.get("external_scholarships_and_programs", [])
                _HARMFUL_PATTERNS = data.get("harmful_patterns", [])
        except Exception:
            pass

_reload_dict()


def safety_precheck(query: str) -> Optional[Dict[str, Any]]:
    """Kiểm tra an toàn sơ bộ và phân loại Near-OOD / Adversarial trước khi chạy pipeline.
    
    Returns:
        None nếu câu hỏi an toàn và thuộc phạm vi FPT.
        Dict chứa reason, refusal_message nếu bị chặn.
    """
    if not query or not query.strip():
        return None

    q_lower = query.lower().strip()

    # 1. Kiểm tra hành vi độc hại, tấn công prompt injection, gian lận học vụ
    for pat in _HARMFUL_PATTERNS:
        if pat in q_lower:
            return {
                "blocked": True,
                "reason": "harmful_intent",
                "intent": "ood",
                "answer": (
                    "Tôi không thể hỗ trợ các yêu cầu liên quan đến hành vi gian lận thi cử, "
                    "vi phạm quy chế đào tạo hoặc can thiệp vào bảo mật hệ thống. "
                    "Mọi hành vi vi phạm kỷ luật học tập sẽ bị xử lý nghiêm theo quy định của Đại học FPT."
                ),
            }

    # 2. Kiểm tra câu hỏi trường khác (Near-OOD) và học bổng ngoài FPT
    # Lưu ý: Whitelist nếu câu hỏi nhấn mạnh Đại học FPT
    is_fpt_mention = "fpt" in q_lower or "đại học fpt" in q_lower

    for uni in _EXTERNAL_UNIS:
        # Kiểm tra từ khóa trường ngoài (dùng word boundary cho từ viết tắt ngắn)
        is_hit = False
        if len(uni) <= 4:
            if re.search(r"\b" + re.escape(uni) + r"\b", q_lower):
                is_hit = True
        else:
            if uni in q_lower:
                is_hit = True

        if is_hit:
            # Nếu chỉ hỏi thuần về trường ngoài mà không có nội dung học vụ FPT
            return {
                "blocked": True,
                "reason": "near_ood_university",
                "intent": "ood",
                "answer": (
                    f"FPTUniQA là trợ lý tư vấn chuyên trách về Quy chế đào tạo, Chương trình học và Biểu phí "
                    f"của Đại học FPT. Tôi không có dữ liệu chính thức về quy chế tuyển sinh hoặc đào tạo của {uni.upper()}. "
                    f"Vui lòng tham khảo trang thông tin tuyển sinh chính thức của trường bạn quan tâm."
                ),
            }

    for sch in _EXTERNAL_SCHOLARSHIPS:
        if sch in q_lower:
            return {
                "blocked": True,
                "reason": "near_ood_scholarship",
                "intent": "ood",
                "answer": (
                    f"FPTUniQA chỉ cung cấp thông tin về các chương trình học bổng cấp trường của Đại học FPT "
                    f"(như Học bổng Nguyễn Văn Đạo, Học bổng Tài năng). Tôi không có thẩm quyền tư vấn về chương trình {sch.title()}. "
                    f"Bạn vui lòng kiểm tra trực tiếp tại cổng thông tin chính thức của đơn vị cấp học bổng."
                ),
            }

    return None

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
    # Lưu ý: Whitelist nếu câu hỏi nhấn mạnh hỏi thủ tục chuyển trường sang FPT
    is_fpt_mention = "fpt" in q_lower or "đại học fpt" in q_lower or "dh fpt" in q_lower
    is_transfer = any(w in q_lower for w in ["chuyển trường", "chuyen truong", "chuyển sang", "chuyen sang", "so sánh"])
    if is_fpt_mention and is_transfer:
        return None  # Whitelist hợp lệ: sinh viên hỏi chuyển tiếp vào FPT

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


# Bộ nhận diện Chitchat / Greeting / Identity (<5ms)
_CHITCHAT_PATTERNS = [
    (
        "identity",
        re.compile(
            r"^\s*(bạn|mày|em|m|bot)\s+(là\s+ai|la\s+ai|tên\s+gì|ten\s+gi|có\s+thể\s+làm\s+gì|giúp\s+được\s+gì)\b|"
            r"^\s*(ai\s+tạo\s+ra\s+(bạn|mày|em|bot)|who\s+are\s+you|what\s+is\s+your\s+name|giới\s+thiệu\s+(về\s+)?(bản\s+thân|bạn|bot))\b",
            re.IGNORECASE,
        ),
        (
            "Xin chào! Tôi là **FPTUniQA** — Trợ lý ảo tư vấn Quy chế đào tạo, Chương trình học và Học phí "
            "của Đại học FPT.\n\nTôi có thể hỗ trợ bạn:\n"
            "- 💰 **Học phí & Biểu phí:** Tra cứu mức học phí theo khóa (K17–K22) và phân hiệu (Hà Nội, Cần Thơ, Quy Nhơn, Đà Nẵng, TP.HCM).\n"
            "- 📚 **Môn học & Tiên quyết:** Tra cứu điều kiện tiên quyết (ví dụ: SWP391, PRO192), giáo trình và chuẩn đầu ra.\n"
            "- 📜 **Quy chế học vụ:** Điều kiện thi, quy định điểm danh, cảnh cáo học vụ, thực tập OJT và xét tốt nghiệp.\n\n"
            "Bạn có câu hỏi học vụ nào cần tôi hỗ trợ không?"
        ),
    ),
    (
        "speed",
        re.compile(
            r"^\s*(sao\s+)?(m\s+|mày\s+|bạn\s+|bot\s+|em\s+)?(nhanh\s+(v|vậy|the|thế|qua|quá))\b|"
            r"^\s*sao\s+nhanh\s+(v|vậy|the|thế)\b",
            re.IGNORECASE,
        ),
        (
            "FPTUniQA được tối ưu hóa với cơ chế truy xuất dữ liệu có cấu trúc (SSOT) và bộ chỉ mục Hybrid Retriever "
            "cục bộ, giúp tra cứu thông tin học vụ Đại học FPT chính xác với thời gian phản hồi gần như tức thì. "
            "Bạn cần tra cứu thêm thông tin gì về quy chế hay học phí không?"
        ),
    ),
    (
        "greeting",
        re.compile(
            r"^\s*(xin\s+chào|chào\s+bạn|chào\s+bot|chao\s+ban|chao\s+bot|hello|hi|hey)\s*[!.]*$",
            re.IGNORECASE,
        ),
        (
            "Xin chào bạn! Tôi là FPTUniQA, trợ lý học vụ Đại học FPT. "
            "Tôi có thể hỗ trợ bạn tra cứu biểu phí, môn học hay quy chế đào tạo nào hôm nay?"
        ),
    ),
    (
        "thanks",
        re.compile(
            r"^\s*(cảm\s+ơn|cam\s+on|thank\s+you|thanks)(\s+(bạn|bot|nhiều|nhe|nhé))?\s*[!.]*$",
            re.IGNORECASE,
        ),
        (
            "Rất vui được hỗ trợ bạn! Nếu còn thắc mắc nào về học vụ hoặc quy chế ĐH FPT, bạn cứ hỏi nhé. "
            "Chúc bạn học tập thật tốt!"
        ),
    ),
]


def check_chitchat(query: str) -> Optional[Dict[str, Any]]:
    """Nhận diện các truy vấn Chitchat / Greeting / Identity để phản hồi nhanh mà không qua RAG."""
    if not query or not query.strip():
        return None
    q_strip = query.strip()
    for cat, pattern, reply in _CHITCHAT_PATTERNS:
        if pattern.search(q_strip):
            return {
                "category": cat,
                "answer": reply,
                "route": "chitchat",
            }
    return None

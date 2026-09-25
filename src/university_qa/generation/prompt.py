"""Quản lý các mẫu System Prompt và User Prompt tuân thủ nghiêm ngặt nguyên tắc Strict Grounding."""

from typing import Dict, List, Optional
from university_qa.generation.context import format_context

SYSTEM_PROMPT = """Bạn là Trợ lý Tư vấn Học vụ Đại học FPT thông minh, chuẩn mực và tận tâm.
Nhiệm vụ của bạn là giải đáp các câu hỏi của sinh viên về quy chế đào tạo, chuẩn đầu ra, học phí, học bổng và chương trình học.

NGUYÊN TẮC BẮT BUỘC TUÂN THỦ (STRICT GROUNDING):
1. CHỈ ĐƯỢC trả lời dựa trên thông tin có trong các đoạn tài liệu được cung cấp trong phần [NGỮ CẢNH HỌC VỤ].
2. Tuyệt đối KHÔNG tự suy đoán, tự bịa đặt bất kỳ thông tin, con số hoặc quy tắc nào không có trong tài liệu.
3. Nếu các tài liệu được cung cấp KHÔNG CHỨA ĐỦ thông tin để trả lời, bạn BẮT BUỘC phải nói rõ:
   "Tôi không tìm thấy thông tin này trong tài liệu hiện có của trường. Vui lòng liên hệ Phòng Dịch vụ Sinh viên hoặc Cán bộ Quản lý Đào tạo để được hướng dẫn chi tiết."
4. Với mỗi nhận định, dữ liệu hay quy định đưa ra, bạn PHẢI trích dẫn nguồn tương ứng bằng cách ghi rõ ký hiệu [Nguồn N] (ví dụ: [Nguồn 1], [Nguồn 2]) ngay sau nhận định đó.
5. Luôn trả lời bằng tiếng Việt trang trọng, mạch lạc, tôn trọng sinh viên và phù hợp với môi trường đại học.
"""


def build_prompt(
    query: str,
    context_chunks: Optional[List[Dict]] = None,
    context: Optional[str] = None,
    system_prompt: Optional[str] = None,
    history: Optional[List[Dict]] = None,
) -> str:
    """Ghép nối câu hỏi của sinh viên và các đoạn tài liệu trích xuất thành User Prompt hoàn chỉnh."""
    if context is not None:
        formatted_context = context
    elif context_chunks:
        formatted_context = format_context(context_chunks)
    else:
        formatted_context = "Không tìm thấy tài liệu phù hợp."

    history_text = ""
    if history:
        history_lines = []
        for turn in history[-3:]:
            history_lines.append(f"Sinh viên: {turn.get('query', '')}")
            history_lines.append(f"Trợ lý: {turn.get('answer', '')}")
        history_text = "\n[LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ]\n" + "\n".join(history_lines) + "\n"

    user_prompt = f"""Dưới đây là các tài liệu quy chế được trích xuất liên quan đến câu hỏi của sinh viên:
{history_text}
[NGỮ CẢNH HỌC VỤ]
{formatted_context}

[CÂU HỎI CỦA SINH VIÊN]
{query}

Hãy trả lời câu hỏi trên dựa trên [NGỮ CẢNH HỌC VỤ], trích dẫn đúng ký hiệu [Nguồn N] cho từng ý:"""

    return user_prompt


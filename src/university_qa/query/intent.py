"""Định nghĩa và quản lý các ý định truy vấn (Query Intents) cho hệ thống University QA. Phụ trách: TV3.

DANH SÁCH TẬP INTENT CHUẨN (HỌC VỤ FPTU):
1. policy_lookup:
   - Ý nghĩa: Tra cứu quy chế, quy định học vụ dạng văn bản / factoid.
   - Ví dụ: Cảnh cáo học vụ, môn tiên quyết, quy chế thi lại, điểm chuyên cần, học bổng.
2. tuition_lookup:
   - Ý nghĩa: Tra cứu học phí, biểu phí, số tín chỉ theo ngành học và khóa tuyển sinh (dữ liệu có cấu trúc).
   - Ví dụ: Học phí ngành AI khóa 2026, mức đóng học phí kỳ chuyên ngành, hạn nộp học phí.
3. graduation_lookup:
   - Ý nghĩa: Tra cứu điều kiện xét công nhận tốt nghiệp đại học, chuẩn đầu ra ngoại ngữ, đồ án tốt nghiệp Capstone.
   - Ví dụ: Điều kiện tốt nghiệp, chuẩn tiếng Anh ra trường, điều kiện làm khóa luận SEP490.
4. OOD (Out-Of-Domain):
   - Ý nghĩa: Các câu hỏi ngoài phạm vi học vụ, đào tạo và quy chế ĐH FPT.
   - Ví dụ: Hỏi thời tiết, thông tin các trường đại học khác, nấu ăn, thể thao, trò chuyện phiếm.
"""

from enum import Enum
from typing import List


class QueryIntent(str, Enum):
    """Tập intent chuẩn hóa cho module Semantic Parsing."""

    POLICY_LOOKUP = "policy_lookup"
    TUITION_LOOKUP = "tuition_lookup"
    GRADUATION_LOOKUP = "graduation_lookup"
    OOD = "OOD"


SUPPORTED_INTENTS: List[str] = [intent.value for intent in QueryIntent]

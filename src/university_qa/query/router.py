"""Router điều phối truy vấn: Structured Lookup vs RAG Pipeline vs Clarification vs OOD. Phụ trách: TV3.

Chiến lược điều phối:
1. intent == "tuition_lookup":
   - Đủ slot (program + cohort): Chuyển sang "structured_lookup" tra thẳng vào bảng học phí mock (Zero Hallucination).
   - Thiếu slot (ví dụ thiếu cohort hoặc program): Chuyển sang "clarification" để hỏi làm rõ (mầm mống cho Multi-turn Tuần 5).
2. intent in ["policy_lookup", "graduation_lookup"]: Chuyển sang "rag_pipeline" tra cứu tài liệu quy chế.
3. intent == "OOD": Chuyển sang "ood" trả về thông báo từ chối lịch sự.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple

from contracts import ParsedQuery
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.query.router")

RouteType = Literal["structured_lookup", "rag_pipeline", "clarification", "ood", "uncertain"]

MOCK_TUITION_PATH = Path(__file__).parent / "mock_tuition_table.json"


class RouteResult(str):
    """Chuỗi kết quả định tuyến có thể so sánh trực tiếp như str (ví dụ route == 'structured_lookup')
    đồng thời hỗ trợ unpack tuple (route, clarification_msg) và truy cập thuộc tính .clarification.
    """

    def __new__(cls, route: str, clarification: Optional[str] = None):
        instance = super().__new__(cls, route)
        instance.route = route
        instance.clarification = clarification
        return instance

    def __iter__(self):
        return iter((str(self), self.clarification))


def load_mock_tuition_table() -> list:
    """Đọc dữ liệu bảng học phí giả lập trong namespace TV3."""
    if not MOCK_TUITION_PATH.exists():
        logger.warning(f"Không tìm thấy file bảng học phí tại {MOCK_TUITION_PATH}")
        return []
    with open(MOCK_TUITION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def route_query(parsed: ParsedQuery) -> RouteResult:
    """
    Phân loại tuyến đường thực thi dựa trên đối tượng ParsedQuery (Contract 3).

    Trả về RouteResult:
        - "uncertain": Khi confidence < 0.5 (Guardrail an toàn Tuần 6)
        - "structured_lookup": Tra cứu trực tiếp bảng học phí
        - "rag_pipeline": Tra cứu quy chế qua mock_retriever
        - "clarification": Hỏi làm rõ khi thiếu slot cần thiết
        - "ood": Ngoài phạm vi đào tạo
    """
    # 0. Kiểm tra ngưỡng tin cậy an toàn (Tuần 6 Guardrail)
    # Nếu confidence < 0.5 (dù intent không phải OOD) -> tự động coi như không đủ tin cậy
    if parsed.confidence is not None and parsed.confidence < 0.5:
        return RouteResult(
            "uncertain",
            "Hệ thống chưa chắc chắn về câu hỏi này (độ tin cậy phân tích thấp). Vui lòng diễn đạt rõ hơn hoặc cung cấp thêm thông tin học vụ cụ thể.",
        )

    # 1. Nhánh ngoài phạm vi (OOD)
    if parsed.intent == "OOD":
        return RouteResult("ood", None)

    # 2. Nhánh tra cứu học phí / số liệu (tuition_lookup)
    if parsed.intent == "tuition_lookup":
        slots = parsed.slots or {}
        has_program = bool(slots.get("program"))
        has_cohort = bool(slots.get("cohort"))

        # Đủ cả ngành và khóa -> Tra cứu trực tiếp bảng số liệu (Zero Hallucination)
        if has_program and has_cohort:
            return RouteResult("structured_lookup", None)

        # Thiếu slot -> Hỏi làm rõ thông tin thay vì đoán bừa (chống ảo giác, mầm cho Tuần 5)
        if has_program and not has_cohort:
            program = slots.get("program")
            return RouteResult(
                "clarification",
                f"Bạn đang hỏi về học phí ngành {program}. Vui lòng cho biết bạn muốn tra cứu cho khóa tuyển sinh nào (ví dụ: khóa 2026 hay 2023)?",
            )
        elif has_cohort and not has_program:
            cohort = slots.get("cohort")
            return RouteResult(
                "clarification",
                f"Bạn đang hỏi về học phí khóa {cohort}. Vui lòng cho biết bạn muốn tra cứu cho ngành học nào (ví dụ: AI, CNTT, KTPM)?",
            )
        else:
            return RouteResult(
                "clarification",
                "Vui lòng cung cấp thêm ngành học và khóa tuyển sinh (ví dụ: ngành AI khóa 2026) để tôi tra cứu học phí chính xác cho bạn.",
            )

    # 3. Nhánh quy chế và tốt nghiệp -> Chuyển vào RAG Pipeline
    if parsed.intent in ["policy_lookup", "graduation_lookup"]:
        return RouteResult("rag_pipeline", None)

    return RouteResult("rag_pipeline", None)


def execute_structured_lookup(slots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tra cứu trực tiếp vào bảng số liệu học phí mock (Zero Hallucination).
    Đảm bảo tính chính xác số học tuyệt đối, không thông qua LLM sinh tự do.
    """
    table = load_mock_tuition_table()
    raw_program = str(slots.get("program") or "").strip().upper()
    raw_cohort = str(slots.get("cohort") or "").strip().upper()

    # Chuẩn hóa tên ngành viết tắt / đầy đủ
    program_map = {
        "AI": "AI",
        "TRÍ TUỆ NHÂN TẠO": "AI",
        "TRI TUE NHAN TAO": "AI",
        "CNTT": "CNTT",
        "CÔNG NGHỆ THÔNG TIN": "CNTT",
        "CONG NGHE THONG TIN": "CNTT",
        "KTPM": "KTPM",
        "KỸ THUẬT PHẦN MỀM": "KTPM",
        "KY THUAT PHAN MEM": "KTPM",
    }
    target_program = program_map.get(raw_program, raw_program)

    # Chuẩn hóa khóa (ví dụ K2026 -> 2026)
    cohort_match = re.search(r"\d{4}", raw_cohort)
    target_cohort = cohort_match.group(0) if cohort_match else raw_cohort

    for row in table:
        row_program = str(row.get("program", "")).strip().upper()
        row_cohort = str(row.get("cohort", "")).strip().upper()

        if row_program == target_program and (row_cohort == target_cohort or target_cohort.endswith(row_cohort)):
            amount_formatted = f"{row['tuition_per_term_vnd']:,} {row['currency']}"
            answer = (
                f"Theo biểu phí chính thức của Đại học FPT, học phí chuyên ngành {row['program_name']} ({row['program']}) "
                f"cho sinh viên Khóa {row['cohort']} là {amount_formatted}/học kỳ. "
                f"Thời gian đào tạo chuẩn gồm {row['total_terms']} học kỳ chuyên ngành. ({row['note']})"
            )
            return {
                "found": True,
                "answer": answer,
                "data": row,
                "source": f"Biểu phí tuyển sinh ĐH FPT - Khóa {row['cohort']} ({row['program']})",
            }

    return {
        "found": False,
        "answer": f"Hiện tại chưa có dữ liệu học phí chính xác cho ngành {target_program} khóa {target_cohort} trong hệ thống biểu phí.",
        "data": None,
        "source": "Biểu phí tuyển sinh ĐH FPT",
    }

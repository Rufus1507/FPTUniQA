"""Kiểm thử hồi quy (Regression Test) cho các kịch bản lỗi trong session_npy2ykn.

Bao gồm:
1. Chống nhiễm độc ngữ cảnh (Context Contamination): Các câu hỏi độc lập về môn học (CSD201, PRO192)
   hoặc lệ phí chung không bị ghi đè thành câu hỏi học phí cũ.
2. Self-Containedness Gate: Bảo toàn nguyên vẹn câu hỏi tự chứa.
3. Kế thừa đúng (Continuation): Các câu rút gọn (còn k20 thì sao, thế ở quy nhơn...) kế thừa đúng ngữ cảnh.
4. Chuẩn hóa từ đồng nghĩa và biến thể viết tắt / không dấu.
"""

import pytest
from contracts import ParsedQuery
from FPTUniQA.normalization.engine import get_entity_normalizer
from FPTUniQA.query.rewriting import is_continuation_query, is_self_contained_query, rewrite_query
from FPTUniQA.query.router import execute_structured_lookup, route_query
from FPTUniQA.query.semantic_parser import parse_query


@pytest.fixture
def sample_history():
    return [
        {
            "query": "Học phí ngành Vi mạch bán dẫn khóa 2026 tại Quy Nhơn là bao nhiêu?",
            "rewritten_query": "Học phí K22 ngành Vi mạch bán dẫn tại Quy Nhơn là bao nhiêu?",
            "answer": "Theo biểu phí chính thức tuyển sinh Đại học FPT...",
            "route_chosen": "structured_lookup",
            "parsed_query": {
                "intent": "tuition_lookup",
                "slots": {"cohort": "K22", "program": "Vi mạch bán dẫn", "campus": "Quy Nhơn"}
            }
        },
        {
            "query": "Môn PRF192 có bao nhiêu tín chỉ?",
            "rewritten_query": "Môn PRF192 có bao nhiêu tín chỉ?",
            "answer": "Môn PRF192 có khối lượng đào tạo là 3 tín chỉ...",
            "route_chosen": "structured_lookup",
            "parsed_query": {
                "intent": "course_lookup",
                "slots": {"course_code": "PRF192", "course_aspect": "credits"}
            }
        }
    ]


def test_self_contained_course_queries_not_contaminated(sample_history):
    """Lượt 6 & 7: Hỏi môn mới (CSD201, PRO192) không được ghi đè thành học phí Vi mạch Quy Nhơn."""
    q6 = "Môn CSD201 cần học môn tiên quyết nào?"
    assert is_self_contained_query(q6) is True
    assert rewrite_query(q6, sample_history) == q6

    p6 = parse_query(q6)
    r6 = route_query(p6)
    assert r6 == "structured_lookup"
    ans6 = execute_structured_lookup(p6)
    assert "PRO192" in ans6["answer"]

    q7 = "Giáo trình môn PRO192 là sách nào?"
    assert is_self_contained_query(q7) is True
    assert rewrite_query(q7, sample_history) == q7

    p7 = parse_query(q7)
    r7 = route_query(p7)
    assert r7 == "structured_lookup"
    ans7 = execute_structured_lookup(p7)
    assert "Core Java" in ans7["answer"]


def test_self_contained_common_fees_not_prepended_with_course(sample_history):
    """Lượt 9 & 10: Hỏi lệ phí học lại / ký túc xá không được ghép môn PRF192 từ lượt 5."""
    q9 = "Lệ phí học lại tính theo một tín chỉ là bao nhiêu tiền?"
    assert is_self_contained_query(q9) is True
    assert rewrite_query(q9, sample_history) == q9

    p9 = parse_query(q9)
    r9 = route_query(p9)
    assert r9 == "structured_lookup"
    ans9 = execute_structured_lookup(p9)
    assert "650,000" in ans9["answer"]

    q10 = "Phí ký túc xá phân hiệu Hà Nội là bao nhiêu một học kỳ?"
    assert is_self_contained_query(q10) is True
    assert rewrite_query(q10, sample_history) == q10

    p10 = parse_query(q10)
    r10 = route_query(p10)
    assert r10 == "structured_lookup"
    ans10 = execute_structured_lookup(p10)
    assert "4,000,000" in ans10["answer"]


def test_unaccented_and_abbreviated_variants():
    """Lượt 14, 15, 21, 22: Chuẩn hóa câu không dấu và chữ viết tắt."""
    # Lượt 14
    q14 = "mon csd201 hoc o ky may"
    p14 = parse_query(q14)
    assert p14.slots.get("course_code") == "CSD201"
    assert route_query(p14) == "structured_lookup"

    # Lượt 15
    q15 = "le phi thi lai la bao nhieu tien"
    p15 = parse_query(q15)
    r15 = route_query(p15)
    assert r15 == "structured_lookup"
    assert r15.clarification is None

    # Lượt 21: công nghệ tt
    q21 = "Học phí ngành công nghệ tt khóa 2026 tại Hà Nội là bao nhiêu?"
    norm21 = get_entity_normalizer().normalize(q21)
    assert norm21.slots_hint.get("program") in ["CNTT", "Công nghệ thông tin"]

    # Lượt 22: kỹ thuật pm
    q22 = "Học phí ngành kỹ thuật pm khóa K22 tại TP.HCM là bao nhiêu?"
    norm22 = get_entity_normalizer().normalize(q22)
    assert norm22.slots_hint.get("program") in ["KTPM", "Kỹ thuật phần mềm"]


def test_true_continuation_queries():
    """Lượt 31, 32, 33: Câu hỏi tỉnh lược kế thừa đúng slot từ lượt trước."""
    history_tuition = [
        {
            "query": "hoc phi nganh cntt k22 can tho",
            "rewritten_query": "Học phí K22 ngành CNTT tại Cần Thơ là bao nhiêu?",
            "answer": "Theo biểu phí tuyển sinh...",
            "route_chosen": "structured_lookup",
            "parsed_query": {
                "intent": "tuition_lookup",
                "slots": {"cohort": "K22", "program": "CNTT", "campus": "Cần Thơ"}
            }
        }
    ]

    # Lượt 31: con k20 thi sao?
    q31 = "con k20 thi sao?"
    assert is_continuation_query(q31) is True
    rw31 = rewrite_query(q31, history_tuition)
    assert "K20" in rw31
    assert "CNTT" in rw31 or "Công nghệ thông tin" in rw31

    # Lượt 32: the o quy nhon thi bao nhieu?
    q32 = "the o quy nhon thi bao nhieu?"
    assert is_continuation_query(q32) is True
    rw32 = rewrite_query(q32, history_tuition)
    assert "Quy Nhơn" in rw32


def test_standalone_policy_and_ood():
    """Lượt 11, 12, 35, 41, 42: Các câu hỏi quy chế và OOD không bị rewriting can thiệp."""
    history = [
        {"query": "Học phí K22 CNTT Hà Nội", "rewritten_query": "Học phí K22 CNTT Hà Nội", "answer": "31,600,000"}
    ]

    q11 = "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?"
    assert is_self_contained_query(q11) is True
    assert rewrite_query(q11, history) == q11

    q12 = "Điều kiện xét tốt nghiệp đại học như thế nào?"
    assert is_self_contained_query(q12) is True
    assert rewrite_query(q12, history) == q12

    q35 = "Thế điều kiện làm đồ án tốt nghiệp Capstone là gì?"
    assert is_self_contained_query(q35) is True
    assert rewrite_query(q35, history) == q35

    q41 = "Sinh viên đang bị nợ học phí có được làm đơn đăng ký môn học không?"
    assert is_self_contained_query(q41) is True
    assert rewrite_query(q41, history) == q41

    q42 = "Hướng dẫn cách nấu món bún bò Huế ngon chuẩn vị?"
    assert is_self_contained_query(q42) is True
    p42 = parse_query(q42)
    assert route_query(p42) == "ood"

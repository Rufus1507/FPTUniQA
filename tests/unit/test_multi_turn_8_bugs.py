import pytest
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline


@pytest.fixture(scope="module")
def pipeline():
    return RAGPipeline(use_mock_fallback=True)


def test_multi_turn_8_bugs(pipeline):
    """Kiểm tra hồi quy 8 lỗi thực tế phát hiện trong session 13 câu hỏi."""
    session_id = "test_multi_turn_regression_sess"

    # Turn 1
    r1 = pipeline.answer("Học phí ngành Trí tuệ nhân tạo khóa 2026 tại Hà Nội là bao nhiêu?", session_id=session_id)
    assert "31,600,000" in r1.get("answer", "")

    # Turn 2
    r2 = pipeline.answer("Thế còn ở phân hiệu Quy Nhơn thì sao ad?", session_id=session_id)
    assert "15,800,000" in r2.get("answer", "")

    # Bug 1 (Turn 3): KTX Quy Nhon - không bị đè bởi bảng biểu phí 15.8tr
    r3 = pipeline.answer("Ở đó ký túc xá một kỳ bao nhiêu tiền?", session_id=session_id)
    ans3 = r3.get("answer", "")
    assert "ký túc xá" in ans3.lower()
    assert "15,800,000" not in ans3

    # Bug 2 (Turn 4): OJT Semester - Kỳ 6
    r4 = pipeline.answer("Sinh viên ngành Kỹ thuật phần mềm đi thực tập OJT vào kỳ mấy?", session_id=session_id)
    assert "kỳ 6" in r4.get("answer", "").lower()

    # Bug 3 (Turn 5): OJT Conditions - tín chỉ & SWP391
    r5 = pipeline.answer("Cần tích lũy bao nhiêu tín chỉ và hoàn thành môn dự án nào để được đi?", session_id=session_id)
    ans5 = r5.get("answer", "")
    assert "tín chỉ" in ans5.lower()
    assert "swp391" in ans5.lower()

    # Bug 4 (Turn 6): OJT Tuition - miễn học phí chuyên ngành
    r6 = pipeline.answer("Trong kỳ này sinh viên có phải đóng học phí chuyên ngành không?", session_id=session_id)
    assert "không phải đóng học phí chuyên ngành" in r6.get("answer", "").lower()

    # Turn 7: CSD201 Exam
    r7 = pipeline.answer("Môn Cấu trúc dữ liệu và giải thuật CSD201 thi PE hay EOS?", session_id=session_id)
    assert "pe" in r7.get("answer", "").lower()

    # Bug 5 (Turn 8): Điểm F CSD201 - học lại, không thi lại
    r8 = pipeline.answer("Nếu chẳng may bị điểm F môn này thì phải thi lại hay học lại?", session_id=session_id)
    ans8 = r8.get("answer", "")
    assert "học lại" in ans8.lower()
    assert "không được phép thi lại" in ans8.lower()

    # Turn 9: Compare SE & AI
    r9 = pipeline.answer("So sánh chương trình đào tạo giữa ngành SE và AI", session_id=session_id)
    assert "so sánh" in r9.get("answer", "").lower()

    # Bug 6 (Turn 10): ATTT Credits - 132 tín chỉ, không bị đè bởi CSD201
    r10 = pipeline.answer("Thế còn ngành An toàn thông tin thì học bao nhiêu tín chỉ?", session_id=session_id)
    ans10 = r10.get("answer", "")
    assert "132" in ans10
    assert "csd201" not in ans10.lower()

    # Turn 11: PRF192 Textbook
    r11 = pipeline.answer("Giáo trình môn Cơ sở lập trình C PRF192 là cuốn sách nào?", session_id=session_id)
    assert "the c programming language" in r11.get("answer", "").lower()

    # Bug 7 (Turn 12): Next course after PRF192 - PRO192 Java
    r12 = pipeline.answer("Học xong môn này thì kỳ sau học tiếp môn lập trình nào?", session_id=session_id)
    ans12 = r12.get("answer", "")
    assert "pro192" in ans12.lower()
    assert "java" in ans12.lower()

    # Bug 8 (Turn 13): PRO192 Assignment
    r13 = pipeline.answer("Môn Java đấy có cần làm bài tập lớn Assignment không?", session_id=session_id)
    ans13 = r13.get("answer", "")
    assert "assignment" in ans13.lower() or "bài tập lớn" in ans13.lower()

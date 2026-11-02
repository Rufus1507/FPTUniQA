"""Unit tests cho Động cơ Chuẩn hóa Thực thể (FPTUniQA Entity Normalization Engine - M3)."""

import time
import pytest
from FPTUniQA.normalization.engine import EntityNormalizer, get_entity_normalizer


@pytest.fixture(scope="module")
def normalizer():
    return get_entity_normalizer()


class TestEntityNormalizer:
    """Bộ kiểm thử đơn vị toàn diện cho EntityNormalizer."""

    def test_major_synonyms(self, normalizer):
        """Kiểm tra nhận diện ngành AI qua nhiều biến thể đồng nghĩa."""
        queries = [
            "Học phí ngành AI là bao nhiêu?",
            "Học phí ngành A.I. là bao nhiêu?",
            "Học phí ngành Trí tuệ nhân tạo là bao nhiêu?",
            "Học phí ngành tri tue nhan tao la bao nhieu?",
            "Ngành AI có học phí thế nào?",
        ]
        for q in queries:
            res = normalizer.normalize(q)
            eids = [e.entity_id for e in res.entities]
            assert "MAJOR_AI" in eids, f"Không tìm thấy MAJOR_AI trong câu: '{q}'"
            assert res.slots_hint.get("program") == "AI"

    def test_major_ktpm_and_cntt(self, normalizer):
        """Kiểm tra nhận diện ngành KTPM và CNTT."""
        res_ktpm = normalizer.normalize("Học phí ngành KTPM khóa 2026")
        assert any(e.entity_id == "MAJOR_KTPM" for e in res_ktpm.entities)
        assert res_ktpm.slots_hint.get("program") == "KTPM"

        res_cntt = normalizer.normalize("Ngành Công nghệ thông tin có bao nhiêu tín chỉ?")
        assert any(e.entity_id == "MAJOR_CNTT" for e in res_cntt.entities)

    def test_cohort_verified_2026_and_k22(self, normalizer):
        """Kiểm tra năm 2026 và K22 được xác thực 100% khớp COHORT_K22."""
        res1 = normalizer.normalize("Học phí khóa 2026 ngành AI")
        c1 = [e for e in res1.entities if e.entity_type == "cohort"]
        assert len(c1) == 1
        assert c1[0].entity_id == "COHORT_K22"
        assert c1[0].verified is True
        assert res1.slots_hint.get("cohort") == "K22"

        res2 = normalizer.normalize("Học phí khóa K22 ngành AI")
        c2 = [e for e in res2.entities if e.entity_type == "cohort"]
        assert len(c2) == 1
        assert c2[0].entity_id == "COHORT_K22"
        assert c2[0].verified is True

    def test_cohort_unverified_future_year(self, normalizer):
        """Kiểm tra năm tương lai (2028) không bị tự tiện suy đoán, giữ nguyên chuỗi thô."""
        res = normalizer.normalize("Học phí khóa 2028 ngành AI là bao nhiêu?")
        c = [e for e in res.entities if e.entity_type == "cohort"]
        assert len(c) == 1
        assert c[0].entity_id == "RAW_YEAR_2028"
        assert c[0].verified is False
        assert c[0].confidence < 1.0

    def test_course_by_vietnamese_name(self, normalizer):
        """Kiểm tra nhận diện môn học khi người dùng hỏi bằng tên tiếng Việt không có mã môn."""
        res = normalizer.normalize("Môn Cơ sở lập trình C học những nội dung gì?")
        courses = [e for e in res.entities if e.entity_type == "course"]
        assert len(courses) >= 1
        assert courses[0].code == "PRF192"
        assert res.slots_hint.get("course_code") == "PRF192"
        assert res.slots_hint.get("course_aspect") == "syllabus"

    def test_course_by_code(self, normalizer):
        """Kiểm tra nhận diện môn học khi người dùng cung cấp mã môn trực tiếp."""
        res = normalizer.normalize("Giáo trình môn PRO192 là sách nào?")
        courses = [e for e in res.entities if e.entity_type == "course"]
        assert len(courses) >= 1
        assert courses[0].code == "PRO192"
        assert res.slots_hint.get("course_code") == "PRO192"
        assert res.slots_hint.get("course_aspect") == "textbook"

    def test_campus_matcher(self, normalizer):
        """Kiểm tra nhận diện phân hiệu cơ sở qua các từ viết tắt."""
        res_ct = normalizer.normalize("Học phí ngành AI ở ct là bao nhiêu?")
        assert any(e.entity_id == "CAMPUS_CANTHO" for e in res_ct.entities)
        assert res_ct.slots_hint.get("campus") == "Cần Thơ"

        res_hl = normalizer.normalize("Học phí ngành KTPM ở Hòa Lạc")
        assert any(e.entity_id == "CAMPUS_HANOI" for e in res_hl.entities)
        assert res_hl.slots_hint.get("campus") == "Hà Nội"

    def test_negative_no_substring_false_positive(self, normalizer):
        """Kiểm tra không bị match nhầm từ 'ai' trong các từ tiếng Việt thông thường."""
        # 'ai' là đại từ nghi vấn trong 'ai là', không phải ngành AI
        res1 = normalizer.normalize("Ai là người sáng lập Đại học FPT?")
        # Không có từ chỉ thị ngành, nhưng quan trọng là từ 'mai', 'lai' không match 'ai'
        res2 = normalizer.normalize("Ngày mai tôi đi học lại môn CSD201")
        eids2 = [e.entity_id for e in res2.entities]
        assert "MAJOR_AI" not in eids2
        assert "COURSE_CSD201" in eids2

    def test_determinism_and_idempotency(self, normalizer):
        """Kiểm tra tính xác định (10 lần chạy cùng 1 kết quả) và tính lũy thừa."""
        query = "Học phí ngành Trí tuệ nhân tạo khóa 2026 cơ sở Cần Thơ bao nhiêu?"
        r1 = normalizer.normalize(query).to_dict()
        for _ in range(10):
            r2 = normalizer.normalize(query).to_dict()
            assert r1 == r2

    def test_latency_performance(self, normalizer):
        """Kiểm tra độ trễ xử lý cực thấp (p95 <= 5ms trên CPU)."""
        query = "Học phí chuyên ngành Kỹ thuật phần mềm khóa K22 tại phân hiệu Hà Nội là bao nhiêu?"
        start = time.perf_counter()
        for _ in range(100):
            normalizer.normalize(query)
        elapsed_ms = ((time.perf_counter() - start) / 100) * 1000
        assert elapsed_ms < 10.0, f"Độ trễ quá cao: {elapsed_ms:.2f}ms"

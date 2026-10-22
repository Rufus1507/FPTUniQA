"""Integration test kiểm tra RAGPipeline với các truy vấn sâu về nội dung học và giáo trình."""

import pytest
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline


@pytest.fixture(scope="module")
def pipeline():
    return RAGPipeline(use_mock_fallback=False)


def test_pipeline_course_syllabus_prf192(pipeline):
    res = pipeline.answer("Môn PRF192 học những gì?")
    assert res["intent"] in ["factoid", "course_lookup"]
    ans = res["answer"]
    assert "PRF192" in ans
    assert any(kw in ans.lower() for kw in ["biến", "con trỏ", "pointer", "hàm"])


def test_pipeline_course_textbook_pro192(pipeline):
    res = pipeline.answer("Giáo trình môn PRO192 là sách nào?")
    assert res["intent"] in ["factoid", "course_lookup"]
    ans = res["answer"]
    assert "PRO192" in ans
    assert any(kw in ans for kw in ["Core Java", "Horstmann", "Prentice Hall"])


def test_pipeline_course_syllabus_dbi202(pipeline):
    res = pipeline.answer("Môn DBI202 học những gì?")
    assert res["intent"] in ["factoid", "course_lookup"]
    ans = res["answer"]
    assert "DBI202" in ans
    assert any(kw in ans for kw in ["SQL", "quan hệ", "Database", "chuẩn hóa"])


def test_pipeline_course_textbook_author_mkt101(pipeline):
    res = pipeline.answer("Giáo trình môn MKT101 của ai viết?")
    assert res["intent"] in ["factoid", "course_lookup"]
    ans = res["answer"]
    assert "MKT101" in ans
    assert any(kw in ans for kw in ["Philip Kotler", "Gary Armstrong", "Principles of Marketing"])


def test_pipeline_course_syllabus_csd201(pipeline):
    res = pipeline.answer("Môn CSD201 học về những nội dung gì?")
    assert res["intent"] in ["factoid", "course_lookup"]
    ans = res["answer"]
    assert "CSD201" in ans
    assert any(kw in ans.lower() for kw in ["thuật toán", "cây", "danh sách liên kết", "đồ thị"])


def test_pipeline_course_syllabus_vov114(pipeline):
    res = pipeline.answer("Môn VOV114 học những gì?")
    assert res["intent"] in ["factoid", "course_lookup"]
    ans = res["answer"]
    assert "VOV114" in ans
    assert any(kw in ans.lower() for kw in ["vovinam", "đòn chém", "thế chiến lược", "võ đạo"])

"""Unit tests kiểm tra hàm format_course_answer với các aspect mới (syllabus, textbook)."""

import pytest
from FPTUniQA.data.structured import StructuredDataParser


@pytest.fixture
def parser():
    return StructuredDataParser()


def test_format_syllabus_prf192(parser):
    ans = parser.format_course_answer("PRF192", aspect="syllabus")
    assert "PRF192" in ans
    assert "Nội dung đào tạo trọng tâm" in ans
    assert "con trỏ" in ans.lower() or "pointer" in ans.lower() or "biến" in ans.lower()


def test_format_textbook_prf192(parser):
    ans = parser.format_course_answer("PRF192", aspect="textbook")
    assert "PRF192" in ans
    assert "The C Programming Language" in ans
    assert "Kernighan" in ans


def test_format_syllabus_pro192(parser):
    ans = parser.format_course_answer("PRO192", aspect="syllabus")
    assert "PRO192" in ans
    assert "Java" in ans
    assert "đối tượng" in ans.lower() or "oop" in ans.lower()


def test_format_textbook_pro192(parser):
    ans = parser.format_course_answer("PRO192", aspect="textbook")
    assert "PRO192" in ans
    assert "Core Java" in ans or "Horstmann" in ans


def test_format_syllabus_csd201(parser):
    ans = parser.format_course_answer("CSD201", aspect="syllabus")
    assert "CSD201" in ans
    assert "thuật toán" in ans.lower() or "cây" in ans.lower() or "danh sách" in ans.lower()


def test_format_syllabus_dbi202(parser):
    ans = parser.format_course_answer("DBI202", aspect="syllabus")
    assert "DBI202" in ans
    assert "SQL" in ans or "quan hệ" in ans.lower()


def test_format_textbook_mkt101(parser):
    ans = parser.format_course_answer("MKT101", aspect="textbook")
    assert "MKT101" in ans
    assert "Philip Kotler" in ans or "Marketing" in ans


def test_format_syllabus_vov114(parser):
    ans = parser.format_course_answer("VOV114", aspect="syllabus")
    assert "VOV114" in ans
    assert "Vovinam" in ans or "võ đạo" in ans.lower() or "đòn chém" in ans.lower()


def test_format_prerequisite_prf192(parser):
    ans = parser.format_course_answer("PRF192", aspect="prerequisite")
    assert "không yêu cầu" in ans.lower()


def test_format_prerequisite_pro192(parser):
    ans = parser.format_course_answer("PRO192", aspect="prerequisite")
    assert "PRF192" in ans


def test_format_unknown_course(parser):
    ans = parser.format_course_answer("UNKNOWN999", aspect="syllabus")
    assert "chưa có dữ liệu" in ans.lower()


def test_format_empty_aspect_defaults(parser):
    ans = parser.format_course_answer("PRF192")
    assert "Thông tin môn học PRF192" in ans
    assert "tín chỉ" in ans.lower()

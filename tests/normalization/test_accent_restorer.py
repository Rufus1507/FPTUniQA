"""Kiểm thử unit test cho AccentRestorer (Phục hồi dấu tiếng Việt học vụ)."""

import pytest
from FPTUniQA.normalization.accent import get_accent_restorer, has_vietnamese_accents, remove_accents


def test_has_vietnamese_accents():
    assert has_vietnamese_accents("Điều kiện xét tốt nghiệp") is True
    assert has_vietnamese_accents("dieu kien xet tot nghiep") is False
    assert has_vietnamese_accents("học phí") is True
    assert has_vietnamese_accents("hoc phi") is False


def test_accent_restoration_graduation():
    restorer = get_accent_restorer()
    res = restorer.restore("dieu kien de sinh vien duoc xet tot nghiep la gi")
    assert "điều kiện" in res.restored_text
    assert "sinh viên" in res.restored_text
    assert "xét tốt nghiệp" in res.restored_text or "tốt nghiệp" in res.restored_text


def test_accent_restoration_tuition():
    restorer = get_accent_restorer()
    res = restorer.restore("hoc phi nganh an toan thong tin la bao nhieu")
    assert "học phí" in res.restored_text
    assert "an toàn thông tin" in res.restored_text


def test_accented_preservation():
    restorer = get_accent_restorer()
    raw = "Điều kiện để sinh viên được xét tốt nghiệp là gì?"
    res = restorer.restore(raw)
    assert res.restored_text == raw

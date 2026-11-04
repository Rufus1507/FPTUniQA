"""Kiểm thử mở rộng EntityNormalizer analyze_with_spans."""

import pytest
from FPTUniQA.normalization.engine import EntityNormalizer, EntityAnalysisResult


def test_analyze_with_spans_graduation_query():
    norm = EntityNormalizer()
    res = norm.analyze_with_spans("dieu kien de sinh vien duoc xet tot nghiep la gi")
    assert isinstance(res, EntityAnalysisResult)
    assert res.slots_hint.get("topic") == "tot_nghiep"
    assert any(e.entity_id == "TERM_TOT_NGHIEP" for e in res.entities)
    assert any(e.entity_id == "TERM_SINH_VIEN" for e in res.entities)
    assert "Điều kiện tốt nghiệp" in res.canonical_text or "Sinh viên" in res.canonical_text


def test_existing_normalize_backward_compatibility():
    norm = EntityNormalizer()
    res = norm.normalize("k21 nganh cong nghe thong tin tai hoa lac")
    assert res.slots_hint.get("cohort") == "K21"
    assert any(e.entity_id == "MAJOR_CNTT" for e in res.entities)
    assert any(e.entity_id == "CAMPUS_HANOI" for e in res.entities)

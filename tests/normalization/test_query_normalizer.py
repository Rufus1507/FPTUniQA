"""Regression tests cho bộ chuẩn hóa truy vấn tiếng Việt có dấu và không dấu."""

import pytest
from FPTUniQA.query.normalizer import normalize_query, normalize_for_retrieval, NormalizedQuery


def test_normalize_query_basic():
    """Kiểm tra chuẩn hóa Unicode NFC và khoảng trắng cơ bản."""
    raw = "  dieu  kien   de sinh vien duoc   xet tot nghiep la gi  "
    expected = "dieu kien de sinh vien duoc xet tot nghiep la gi"
    assert normalize_query(raw) == expected


def test_normalize_query_accented_preservation():
    """Kiểm tra câu hỏi có dấu không bị biến đổi mất dấu hay xáo trộn thứ tự."""
    raw = "Điều kiện để sinh viên được xét tốt nghiệp là gì?"
    res = normalize_query(raw)
    assert res == raw


def test_normalize_for_retrieval_unaccented():
    """Kiểm tra normalize_for_retrieval trên câu không dấu phục hồi dấu và thêm canonical expansion."""
    q_unacc = "dieu kien de sinh vien duoc xet tot nghiep la gi"
    norm_q = normalize_for_retrieval(q_unacc)
    assert isinstance(norm_q, NormalizedQuery)
    assert norm_q.is_unaccented is True
    assert "điều kiện" in norm_q.retrieval_query
    assert "sinh viên" in norm_q.retrieval_query
    assert "Điều kiện tốt nghiệp" in norm_q.retrieval_query or "tốt nghiệp" in norm_q.retrieval_query


def test_normalize_for_retrieval_accented():
    """Kiểm tra normalize_for_retrieval trên câu có dấu bảo toàn hoàn toàn không thêm token thừa."""
    q_acc = "Điều kiện để sinh viên được xét tốt nghiệp là gì?"
    norm_q = normalize_for_retrieval(q_acc)
    assert norm_q.is_unaccented is False
    assert norm_q.retrieval_query == q_acc

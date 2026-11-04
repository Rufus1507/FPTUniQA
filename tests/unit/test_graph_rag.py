"""Bộ kiểm thử đơn vị cho module Academic Knowledge Graph (Graph RAG)."""

import pytest
from FPTUniQA.graph.knowledge_graph import AcademicKnowledgeGraph, get_knowledge_graph


@pytest.fixture(scope="module")
def kg():
    """Fixture nạp singleton Knowledge Graph."""
    return get_knowledge_graph()


def test_graph_initialization(kg):
    """Kiểm tra khởi tạo đồ thị có đủ số lượng Nodes và Edges cốt lõi."""
    assert kg.graph.number_of_nodes() >= 70
    assert kg.graph.number_of_edges() >= 100
    assert kg.prereq_graph.number_of_nodes() >= 60
    assert kg.prereq_graph.number_of_edges() >= 40


def test_prerequisite_chain_swp391(kg):
    """Kiểm tra chuỗi tiên quyết đa bước của môn dự án SWP391."""
    res = kg.get_prerequisite_chain("SWP391")
    assert res["found"] is True
    assert res["has_prerequisites"] is True
    # Các môn tiên quyết trực tiếp của SWP391
    assert "SWE201C" in res["direct_prerequisites"] or "SWE201c" in res["direct_prerequisites"]
    assert "PRJ301" in res["direct_prerequisites"]
    # Các môn tiên quyết gián tiếp sâu
    assert "PRO192" in res["full_prerequisite_chain"]
    assert "PRF192" in res["full_prerequisite_chain"]
    assert res["total_prerequisite_credits"] >= 12


def test_prerequisite_chain_sep490_capstone(kg):
    """Kiểm tra chuỗi tiên quyết sâu nhất: Khóa luận tốt nghiệp KTPM (SEP490)."""
    res = kg.get_prerequisite_chain("SEP490")
    assert res["found"] is True
    assert "SWP391" in res["direct_prerequisites"]
    assert "SWD392" in res["direct_prerequisites"]
    assert "PRF192" in res["full_prerequisite_chain"]
    assert len(res["full_prerequisite_chain"]) >= 6


def test_prerequisite_chain_root_course(kg):
    """Kiểm tra môn gốc không có tiên quyết (PRF192)."""
    res = kg.get_prerequisite_chain("PRF192")
    assert res["found"] is True
    assert res["has_prerequisites"] is False
    assert len(res["direct_prerequisites"]) == 0
    assert len(res["full_prerequisite_chain"]) == 0


def test_failure_impact_prf192(kg):
    """Kiểm tra phân tích hậu quả khi trượt môn nền tảng PRF192."""
    res = kg.get_failure_impact("PRF192")
    assert res["found"] is True
    assert res["has_downstream"] is True
    assert "PRO192" in res["direct_blocked"]
    assert "CSD201" in res["all_blocked_courses"]
    assert "SWP391" in res["all_blocked_courses"]
    assert "SEP490" in res["all_blocked_courses"]
    assert res["affects_ojt"] is True
    assert res["affects_capstone"] is True


def test_compare_programs_se_and_ai(kg):
    """Kiểm tra so sánh chương trình đào tạo KTPM và AI."""
    res = kg.compare_programs("KTPM", "AI")
    assert res["shared_count"] >= 15
    # Môn chung: PRF192, PRO192, CSD201
    assert any("PRF192" in c for c in res["shared_courses"])
    assert any("PRO192" in c for c in res["shared_courses"])
    # Môn riêng AI
    assert any("AIL302M" in c or "AIL302m" in c for c in res["unique_courses_b"])
    # Môn riêng SE
    assert any("SWD392" in c for c in res["unique_courses_a"])


def test_query_graph_dispatcher(kg):
    """Kiểm tra tự động phân loại intent và trả lời qua query_graph."""
    # 1. Chuỗi tiên quyết
    res1 = kg.query_graph("Muốn học môn SWP391 thì cần học qua những môn nào trước?", {})
    assert res1 is not None
    assert res1["found"] is True
    assert "SWP391" in res1["answer"]

    # 2. Hậu quả rớt môn
    res2 = kg.query_graph("Nếu bị rớt môn PRF192 thì có bị ảnh hưởng gì đến các kỳ sau không?", {})
    assert res2 is not None
    assert res2["found"] is True
    assert "Cảnh báo học vụ" in res2["answer"]

    # 3. So sánh ngành
    res3 = kg.query_graph("So sánh chương trình đào tạo giữa ngành SE và AI", {})
    assert res3 is not None
    assert res3["found"] is True
    assert "So sánh chương trình đào tạo" in res3["answer"]

    # 4. Điều kiện OJT
    res4 = kg.query_graph("Điều kiện để sinh viên được đi thực tập OJT là gì?", {})
    assert res4 is not None
    assert res4["found"] is True
    assert "OJT" in res4["answer"]

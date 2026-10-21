"""Kiểm thử đơn vị cho tính năng Slot Extraction và Metadata Pre-filtering."""

import pytest
from university_qa.query.normalizer import QueryNormalizer
from university_qa.retrieval.bm25 import BM25Retriever
from university_qa.retrieval.dense import DenseRetriever
from university_qa.retrieval.retriever import HybridRetriever


SAMPLE_DOCS = [
    {
        "id": "doc_k17_01",
        "title": "Học phí K17",
        "text": "Học phí chuyên ngành K17 là 25300000 VNĐ.",
        "applies_to_cohort": ["K17"],
        "campus": "ALL",
    },
    {
        "id": "doc_k19_01",
        "title": "Học phí K19",
        "text": "Học phí chuyên ngành K19 là 28700000 VNĐ.",
        "applies_to_cohort": ["K19"],
        "campus": "HN",
    },
    {
        "id": "doc_k20_01",
        "title": "Học phí K20",
        "text": "Học phí chuyên ngành K20 là 31500000 VNĐ.",
        "applies_to_cohort": ["K20"],
        "campus": "FUHL",
    },
    {
        "id": "doc_k21_hcm",
        "title": "Ký túc xá K21 HCM",
        "text": "Chi phí ký túc xá cơ sở Hồ Chí Minh.",
        "applies_to_cohort": ["K21"],
        "campus": "HCM",
    },
    {
        "id": "doc_general_01",
        "title": "Quy chế chung",
        "text": "Quy định chung về kỷ luật và rèn luyện sinh viên.",
        "applies_to_cohort": ["ALL"],
        "campus": "ALL",
    },
]


def test_slot_extraction():
    """Kiểm tra trích xuất khóa và cơ sở từ câu truy vấn."""
    normalizer = QueryNormalizer()

    # Nhận diện K19 và cơ sở Hòa Lạc -> FUHL
    cohort, campus = normalizer.extract_cohort_and_campus("học phí k19 hòa lạc bao nhiêu")
    assert cohort == "K19"
    assert campus == "FUHL"

    # Nhận diện Khóa 21 và cơ sở HCM
    cohort, campus = normalizer.extract_cohort_and_campus("sổ tay khóa 21 tphcm")
    assert cohort == "K21"
    assert campus == "HCM"

    # Nhận diện K22
    cohort, campus = normalizer.extract_cohort_and_campus("biểu phí tiếng anh k22")
    assert cohort == "K22"
    assert campus is None

    # Câu hỏi chung không có slot
    cohort, campus = normalizer.extract_cohort_and_campus("sinh viên được thi lại mấy lần")
    assert cohort is None
    assert campus is None


def test_bm25_metadata_prefiltering():
    """Kiểm tra BM25 pre-filtering loại bỏ hoàn toàn tài liệu sai khóa."""
    bm25 = BM25Retriever()
    bm25.index(SAMPLE_DOCS)

    # Truy vấn hỏi về K19 nhưng có từ khóa học phí
    results = bm25.retrieve("học phí chuyên ngành", top_k=5, filter_cohort="K19")
    returned_ids = [doc["id"] for doc, _ in results]

    # Phải có doc_k19_01 hoặc doc_general_01, TUYỆT ĐỐI không có doc_k17_01 hoặc doc_k20_01
    assert "doc_k19_01" in returned_ids
    assert "doc_k17_01" not in returned_ids
    assert "doc_k20_01" not in returned_ids


def test_campus_filtering():
    """Kiểm tra lọc theo cơ sở đào tạo."""
    bm25 = BM25Retriever()
    bm25.index(SAMPLE_DOCS)

    # Lọc cơ sở HCM
    results = bm25.retrieve("ký túc xá", top_k=5, filter_campus="HCM")
    returned_ids = [doc["id"] for doc, _ in results]
    assert "doc_k21_hcm" in returned_ids
    assert "doc_k19_01" not in returned_ids

    # Lọc cơ sở HN / FUHL tương đương
    results_hn = bm25.retrieve("học phí", top_k=5, filter_campus="HN")
    returned_ids_hn = [doc["id"] for doc, _ in results_hn]
    # doc_k19_01 (HN) và doc_k20_01 (FUHL) đều thuộc cụm Hà Nội
    assert "doc_k19_01" in returned_ids_hn
    assert "doc_k20_01" in returned_ids_hn
    assert "doc_k21_hcm" not in returned_ids_hn


def test_hybrid_retriever_prefiltering():
    """Kiểm tra HybridRetriever truyền tham số lọc xuống cả BM25 và Dense."""
    hybrid = HybridRetriever()
    hybrid.index(SAMPLE_DOCS)

    results = hybrid.retrieve("học phí", top_k=3, filter_cohort="K20")
    for doc, score in results:
        cohorts = doc.get("applies_to_cohort", [])
        assert "K20" in cohorts or "ALL" in cohorts
        assert "K17" not in cohorts

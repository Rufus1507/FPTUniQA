"""Unit tests cho module lọc siêu dữ liệu (Metadata Pre-filtering & Soft Classification)."""

import pytest
from FPTUniQA.retrieval.filter import (
    extract_cohort_set,
    classify_cohort_match,
    classify_metadata_match,
    matches_metadata_filter,
)


def test_extract_cohort_set():
    assert extract_cohort_set("K18") == {"K18"}
    assert extract_cohort_set("k18") == {"K18"}
    assert extract_cohort_set("Khóa 19") == {"K19"}
    assert extract_cohort_set("K17-K20") == {"K17", "K18", "K19", "K20"}
    assert extract_cohort_set("K17–K20") == {"K17", "K18", "K19", "K20"}
    assert extract_cohort_set("K17..K20") == {"K17", "K18", "K19", "K20"}
    assert extract_cohort_set(["K17", "K18"]) == {"K17", "K18"}
    assert extract_cohort_set(None) is None
    assert extract_cohort_set("All") is None
    assert extract_cohort_set("chung") is None


def test_classify_cohort_match():
    # Exact match
    assert classify_cohort_match("K18", "K18") == "match"
    # Range match
    assert classify_cohort_match("K17-K20", "K18") == "match"
    assert classify_cohort_match("K18", None, "K17-K20") == "match"
    # Shared / missing
    assert classify_cohort_match(None, "K18") == "neutral"
    assert classify_cohort_match("All", "K18") == "neutral"
    assert classify_cohort_match("K18", None, None) == "neutral"
    # Mismatch
    assert classify_cohort_match("K21", "K18") == "mismatch"
    assert classify_cohort_match(["K21", "K22"], "K18") == "mismatch"


def test_classify_metadata_match():
    doc_shared = {"metadata": {}}
    doc_k18 = {"metadata": {"cohort": "K18", "campus": "Hà Nội"}}
    doc_range = {"metadata": {"cohort": "K17-K20", "campus": "Hà Nội"}}
    doc_k21_hcm = {"metadata": {"cohort": "K21", "campus": "TP. Hồ Chí Minh"}}

    # Truy vấn K18 Hà Nội
    filter_k18_hn = {"cohort": "K18", "campus": "FUHL"}
    assert classify_metadata_match(doc_k18, filter_k18_hn) == "match"
    assert classify_metadata_match(doc_range, filter_k18_hn) == "match"
    assert classify_metadata_match(doc_shared, filter_k18_hn) == "neutral"
    assert classify_metadata_match(doc_k21_hcm, filter_k18_hn) == "mismatch"

    # Backward compatibility cho matches_metadata_filter: neutral không bị coi là False
    assert matches_metadata_filter(doc_shared, filter_k18_hn) is True
    assert matches_metadata_filter(doc_k18, filter_k18_hn) is True
    assert matches_metadata_filter(doc_range, filter_k18_hn) is True
    assert matches_metadata_filter(doc_k21_hcm, filter_k18_hn) is False

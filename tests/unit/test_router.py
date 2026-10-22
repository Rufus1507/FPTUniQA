"""Unit test cho Router điều phối truy vấn (Contract 3 & Routing)."""

import pytest
from contracts import ParsedQuery
from FPTUniQA.query.router import (
    RouteResult,
    execute_structured_lookup,
    route_query,
)


def test_route_low_confidence():
    parsed = ParsedQuery(
        intent="policy_lookup",
        slots={},
        confidence=0.3,
        parser_method="rule_based",
        fallback_used=True,
    )
    result = route_query(parsed)
    assert result == "uncertain"
    assert result.clarification is not None


def test_route_ood():
    parsed = ParsedQuery(
        intent="OOD",
        slots={},
        confidence=0.95,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "ood"


def test_route_policy_lookup():
    parsed = ParsedQuery(
        intent="policy_lookup",
        slots={"topic": "canh_bao_hoc_vu"},
        confidence=0.9,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "rag_pipeline"


def test_route_graduation_lookup():
    parsed = ParsedQuery(
        intent="graduation_lookup",
        slots={"topic": "tot_nghiep"},
        confidence=0.88,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "rag_pipeline"


def test_route_tuition_full_slots():
    parsed = ParsedQuery(
        intent="tuition_lookup",
        slots={"program": "CNTT", "cohort": "2026", "campus": "Hà Nội"},
        confidence=0.92,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "structured_lookup"


def test_route_tuition_missing_cohort():
    parsed = ParsedQuery(
        intent="tuition_lookup",
        slots={"program": "CNTT"},
        confidence=0.85,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "clarification"
    assert "khóa tuyển sinh" in result.clarification


def test_route_tuition_missing_program():
    parsed = ParsedQuery(
        intent="tuition_lookup",
        slots={"cohort": "2026"},
        confidence=0.85,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "clarification"
    assert "ngành học" in result.clarification


def test_route_tuition_missing_all():
    parsed = ParsedQuery(
        intent="tuition_lookup",
        slots={},
        confidence=0.8,
        parser_method="rule_based",
        fallback_used=False,
    )
    result = route_query(parsed)
    assert result == "clarification"


def test_execute_structured_lookup_specific_campus():
    parsed = ParsedQuery(
        intent="tuition_lookup",
        slots={"program": "KTPM", "cohort": "2026", "campus": "Cần Thơ"},
        confidence=0.9,
        parser_method="rule_based",
        fallback_used=False,
    )
    res = execute_structured_lookup(parsed)
    assert res.get("found") is True
    assert "Cần Thơ" in res.get("answer", "")
    assert res.get("data") is not None


def test_execute_structured_lookup_all_campuses():
    parsed = ParsedQuery(
        intent="tuition_lookup",
        slots={"program": "KTPM", "cohort": "2026"},
        confidence=0.9,
        parser_method="rule_based",
        fallback_used=False,
    )
    res = execute_structured_lookup(parsed)
    assert res.get("found") is True
    assert "Hà Nội" in res.get("answer", "")

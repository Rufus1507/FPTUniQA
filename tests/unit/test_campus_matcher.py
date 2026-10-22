"""Unit test cho module nhận diện và chuẩn hóa campus."""

import pytest
from FPTUniQA.query.campus_matcher import (
    CampusCode,
    match_campus,
    match_campus_code,
)


@pytest.mark.parametrize(
    "query,expected_code,expected_name",
    [
        ("Học phí ngành KTPM tại Hà Nội khóa 2026", CampusCode.HANOI.value, "Hà Nội"),
        ("Tôi muốn đăng ký học ở Hòa Lạc", CampusCode.HANOI.value, "Hà Nội"),
        ("Học phí CNTT ở HN là bao nhiêu?", CampusCode.HANOI.value, "Hà Nội"),
        ("Điểm chuẩn cơ sở TP. Hồ Chí Minh", CampusCode.HCM.value, "TP. Hồ Chí Minh"),
        ("Học phí campus Sài Gòn", CampusCode.HCM.value, "TP. Hồ Chí Minh"),
        ("hoc phi hcm", CampusCode.HCM.value, "TP. Hồ Chí Minh"),
        ("Học bổng ở Đà Nẵng", CampusCode.DANANG.value, "Đà Nẵng"),
        ("hoc o da nang bao nhieu tien", CampusCode.DANANG.value, "Đà Nẵng"),
        ("phân hiệu Cần Thơ có ngành AI không", CampusCode.CANTHO.value, "Cần Thơ"),
        ("hoc phi can tho", CampusCode.CANTHO.value, "Cần Thơ"),
        ("Chi phí sinh hoạt tại Quy Nhơn", CampusCode.QUYNHON.value, "Quy Nhơn"),
        ("hoc o quy nhon", CampusCode.QUYNHON.value, "Quy Nhơn"),
    ],
)
def test_match_campus_valid(query, expected_code, expected_name):
    assert match_campus_code(query) == expected_code
    assert match_campus(query, return_code=True) == expected_code
    assert match_campus(query, return_code=False) == expected_name


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        None,
        "Điều kiện tốt nghiệp ngành AI là gì?",
        "Thời tiết hôm nay thế nào?",
    ],
)
def test_match_campus_none(query):
    assert match_campus_code(query) is None
    assert match_campus(query) is None

"""Module lọc siêu dữ liệu (Metadata Pre-filtering & Soft Classification). Phụ trách: TV2."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from FPTUniQA.query.campus_matcher import CAMPUS_DISPLAY_NAMES, CampusCode

# Map nhóm campus tương đương (HN <=> FUHL <=> Hòa Lạc) đồng bộ từ SSOT campus_matcher
_CAMPUS_EQUIVALENCE_SETS = [
    {"hn", "fuhl", "hà nội", "ha noi", "hòa lạc", "hoa lac", CampusCode.HANOI.value.lower(), CAMPUS_DISPLAY_NAMES[CampusCode.HANOI.value].lower()},
    {"hcm", "hồ chí minh", "ho chi minh", "tp. hồ chí minh", "tp hồ chí minh", "sài gòn", "sai gon", CampusCode.HCM.value.lower(), CAMPUS_DISPLAY_NAMES[CampusCode.HCM.value].lower()},
    {"dn", "đà nẵng", "da nang", CampusCode.DANANG.value.lower(), CAMPUS_DISPLAY_NAMES[CampusCode.DANANG.value].lower()},
    {"ct", "cần thơ", "can tho", CampusCode.CANTHO.value.lower(), CAMPUS_DISPLAY_NAMES[CampusCode.CANTHO.value].lower()},
    {"qn", "quy nhơn", "quy nhon", CampusCode.QUYNHON.value.lower(), CAMPUS_DISPLAY_NAMES[CampusCode.QUYNHON.value].lower()},
]


def _is_campus_match(val_str: str, target_str: str) -> bool:
    """Kiểm tra hai chuỗi cơ sở/phân hiệu có tương đương nhau không."""
    val_norm = str(val_str).strip().lower()
    tgt_norm = str(target_str).strip().lower()
    if not val_norm or not tgt_norm:
        return True
    if val_norm == tgt_norm or val_norm in ("all", "tất cả", "tat ca", "tất cả các cơ sở") or tgt_norm in ("all", "tất cả", "tat ca", "tất cả các cơ sở"):
        return True
    for eq_set in _CAMPUS_EQUIVALENCE_SETS:
        if val_norm in eq_set and tgt_norm in eq_set:
            return True
    return False


def extract_cohort_set(val: Any) -> Optional[Set[str]]:
    """Trích xuất tập hợp các mã khóa (ví dụ: {'K17', 'K18', 'K19', 'K20'}) từ giá trị bất kỳ.

    Hỗ trợ:
    - Chuỗi đơn: 'K18', 'k18', 'Khóa 18' -> {'K18'}
    - Chuỗi khoảng/range: 'K17-K20', 'K17–K20', 'K17..K20', 'K17 - K20' -> {'K17', 'K18', 'K19', 'K20'}
    - Danh sách/tập hợp: ['K17', 'K18'] hoặc ['K17-K18', 'K20']
    - Wildcard hoặc rỗng: None, '', 'all', 'All', 'chung' -> None (biểu thị tài liệu chung toàn diện)
    """
    if val is None:
        return None

    if isinstance(val, (list, tuple, set)):
        merged: Set[str] = set()
        has_any = False
        for item in val:
            s = extract_cohort_set(item)
            if s is not None:
                merged.update(s)
                has_any = True
        return merged if has_any else None

    val_str = str(val).strip()
    if not val_str:
        return None

    val_lower = val_str.lower()
    if val_lower in ("all", "tat ca", "tất cả", "chung", "toan quoc", "toàn quốc", "none", "unknown"):
        return None

    cohorts: Set[str] = set()

    # Nhận diện dạng range: K17-K20, K17–K20, K17..K20, K17 đến K20
    range_match = re.search(r"k?(\d{1,2})\s*(?:-|–|\.\.|đến|den)\s*k?(\d{1,2})", val_lower)
    if range_match:
        try:
            start_num = int(range_match.group(1))
            end_num = int(range_match.group(2))
            if start_num <= end_num and (end_num - start_num) <= 15:
                for n in range(start_num, end_num + 1):
                    cohorts.add(f"K{n}")
        except Exception:
            pass

    # Nhận diện các khóa đơn lẻ: K15, K16, ..., K25
    singles = re.findall(r"\bk?(\d{1,2})\b", val_lower)
    for num_str in singles:
        try:
            n = int(num_str)
            if 10 <= n <= 30:
                cohorts.add(f"K{n}")
        except Exception:
            pass

    # Tìm cụ thể chữ K theo sau là số: k18, K19
    k_matches = re.findall(r"k(\d{1,2})", val_lower)
    for num_str in k_matches:
        try:
            n = int(num_str)
            if 10 <= n <= 30:
                cohorts.add(f"K{n}")
        except Exception:
            pass

    return cohorts if cohorts else None


def classify_cohort_match(
    doc_cohort_val: Any,
    target_cohort: Optional[str] = None,
    target_cohort_range: Optional[Any] = None,
) -> str:
    """Phân loại mức độ khớp khóa (cohort) giữa tài liệu và yêu cầu truy vấn.

    Trả về:
    - 'match': doc có khóa khớp trực tiếp hoặc nằm trong khoảng target.
    - 'mismatch': doc có khóa xác định rõ nhưng KHÔNG giao với target.
    - 'neutral': doc là quy chế chung, doc không ghi rõ khóa, hoặc target không yêu cầu khóa.
    """
    # Nếu truy vấn không yêu cầu khóa nào -> neutral
    target_set: Set[str] = set()
    if target_cohort:
        ts = extract_cohort_set(target_cohort)
        if ts:
            target_set.update(ts)
    if target_cohort_range:
        trs = extract_cohort_set(target_cohort_range)
        if trs:
            target_set.update(trs)

    if not target_set:
        return "neutral"

    doc_set = extract_cohort_set(doc_cohort_val)
    # Doc không khai báo khóa hoặc áp dụng chung (scope: shared/unknown) -> neutral (không phạt)
    if doc_set is None:
        return "neutral"

    # Nếu có giao nhau -> match
    if doc_set & target_set:
        return "match"

    # Nếu doc có khóa rõ ràng nhưng không khớp bất kỳ khóa mục tiêu nào -> mismatch
    return "mismatch"


def classify_metadata_match(
    doc: Dict[str, Any],
    metadata_filter: Optional[Dict[str, Any]],
) -> str:
    """Phân loại trạng thái khớp siêu dữ liệu: 'match' | 'mismatch' | 'neutral'.

    - 'match': khớp ít nhất một metadata trường (cohort hoặc campus) và không có trường nào bị mismatch.
    - 'mismatch': có ít nhất một trường xung đột rõ rệt (sai cohort hoặc sai cơ sở).
    - 'neutral': tài liệu chung, thiếu metadata, hoặc filter không tự tin/không khai báo.
    """
    if not metadata_filter:
        return "neutral"

    # Kiểm tra độ tin cậy nếu có khai báo confidence
    confidence = metadata_filter.get("confidence")
    if confidence is not None:
        try:
            if float(confidence) < 0.6:
                return "neutral"
        except (ValueError, TypeError):
            pass

    doc_meta = doc.get("metadata", {})
    if not isinstance(doc_meta, dict):
        doc_meta = {}

    has_match = False

    # 1. Kiểm tra Campus
    target_campus = metadata_filter.get("campus")
    if target_campus and str(target_campus).strip().lower() not in ("all", "tất cả", "tất cả các cơ sở", ""):
        doc_campus = doc_meta.get("campus", doc.get("campus"))
        if doc_campus is not None and str(doc_campus).strip():
            if isinstance(doc_campus, (list, tuple, set)):
                doc_campuses = [str(c).strip().lower() for c in doc_campus if c]
                if doc_campuses and not any(_is_campus_match(c, target_campus) for c in doc_campuses):
                    return "mismatch"
                elif any(_is_campus_match(c, target_campus) for c in doc_campuses):
                    has_match = True
            else:
                if not _is_campus_match(str(doc_campus), target_campus):
                    return "mismatch"
                else:
                    has_match = True

    # 2. Kiểm tra Cohort
    target_cohort = metadata_filter.get("cohort") or metadata_filter.get("applies_to_cohort")
    target_range = metadata_filter.get("cohort_range")
    if target_cohort or target_range:
        doc_cohort_val = doc_meta.get("cohort", doc.get("cohort", doc_meta.get("applies_to_cohort", doc.get("applies_to_cohort"))))
        cohort_status = classify_cohort_match(
            doc_cohort_val=doc_cohort_val,
            target_cohort=target_cohort,
            target_cohort_range=target_range,
        )
        if cohort_status == "mismatch":
            return "mismatch"
        elif cohort_status == "match":
            has_match = True

    return "match" if has_match else "neutral"


def matches_metadata_filter(
    doc: Dict[str, Any],
    metadata_filter: Optional[Dict[str, Any]],
) -> bool:
    """Kiểm tra tài liệu có khớp với bộ lọc metadata hay không.

    Tương thích ngược: chỉ trả False khi có 'mismatch' rõ ràng.
    Tài liệu chung hoặc thiếu metadata ('neutral') luôn trả True để bảo toàn Recall.
    """
    if not metadata_filter:
        return True
    return classify_metadata_match(doc, metadata_filter) != "mismatch"

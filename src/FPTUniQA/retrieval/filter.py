"""Module lọc siêu dữ liệu (Metadata Pre-filtering). Phụ trách: TV2."""

from typing import Any, Dict, Optional


# Map nhóm campus tương đương (HN <=> FUHL <=> Hòa Lạc)
_CAMPUS_EQUIVALENCE_SETS = [
    {"hn", "fuhl", "hà nội", "ha noi", "hòa lạc", "hoa lac"},
    {"hcm", "hồ chí minh", "ho chi minh", "tp. hồ chí minh", "tp hồ chí minh"},
    {"dn", "đà nẵng", "da nang"},
    {"ct", "cần thơ", "can tho"},
    {"qn", "quy nhơn", "quy nhon"},
]


def _is_campus_match(val_str: str, target_str: str) -> bool:
    """Kiểm tra hai chuỗi cơ sở/phân hiệu có tương đương nhau không."""
    if val_str == target_str or val_str == "all" or target_str == "all":
        return True
    for eq_set in _CAMPUS_EQUIVALENCE_SETS:
        if val_str in eq_set and target_str in eq_set:
            return True
    return False


def matches_metadata_filter(
    doc: Dict[str, Any],
    metadata_filter: Optional[Dict[str, Any]],
) -> bool:
    """Kiểm tra tài liệu có khớp với bộ lọc metadata hay không.

    Hỗ trợ:
    - Tra cứu cả ở metadata lồng (doc['metadata']) và cấp gốc (doc).
    - Các trường đồng nghĩa/alias:
        * 'cohort' <-> 'applies_to_cohort'
        * 'category' <-> 'doc_type'
    - Giá trị wildcard 'All' / 'all' (áp dụng cho cả dạng chuỗi và danh sách).
    - Tương đương campus: HN <=> FUHL.
    - So sánh không phân biệt hoa thường và loại bỏ khoảng trắng thừa.
    """
    if not metadata_filter:
        return True

    doc_meta = doc.get("metadata", {})
    if not isinstance(doc_meta, dict):
        doc_meta = {}

    for k, v in metadata_filter.items():
        if v is None:
            continue

        # Tìm giá trị trường trong doc_meta hoặc doc gốc
        val = doc_meta.get(k, doc.get(k))

        # Kiểm tra alias
        if val is None:
            if k in ("cohort", "applies_to_cohort"):
                val = doc_meta.get("applies_to_cohort", doc.get("applies_to_cohort", doc_meta.get("cohort", doc.get("cohort"))))
            elif k in ("category", "doc_type"):
                val = doc_meta.get("doc_type", doc.get("doc_type", doc_meta.get("category", doc.get("category"))))

        if val is None:
            return False

        target_str = str(v).strip().lower()

        if k in ("campus",):
            if isinstance(val, (list, tuple, set)):
                val_strs = [str(item).strip().lower() for item in val]
                if not any(_is_campus_match(item_str, target_str) for item_str in val_strs):
                    return False
            else:
                val_str = str(val).strip().lower()
                if not _is_campus_match(val_str, target_str):
                    return False
        else:
            if isinstance(val, (list, tuple, set)):
                val_strs = [str(item).strip().lower() for item in val]
                if target_str not in val_strs and "all" not in val_strs:
                    return False
            else:
                val_str = str(val).strip().lower()
                if val_str != target_str and val_str != "all":
                    return False

    return True

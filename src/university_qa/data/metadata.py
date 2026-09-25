"""Bổ sung thông tin siêu dữ liệu (cohort, ngày ban hành, danh mục, campus). Phụ trách: TV1."""

import re
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------- #
# Quy tắc phân loại chủ đề (doc_type)
# ---------------------------------------------------------------------------- #
_DOC_TYPE_RULES: List[Dict[str, Any]] = [
    {
        "type": "tuition",
        "keywords": ["học phí", "hoc-phi", "mức phí", "chi phí học", "học phí kỳ", "tuition"],
    },
    {
        "type": "scholarship",
        "keywords": [
            "học bổng", "hoc-bong", "tìm kiếm nhân tài", "ielts mentor",
            "tín dụng sinh viên", "tài trợ học phí", "miễn học phí",
        ],
    },
    {
        "type": "admission",
        "keywords": [
            "tuyển sinh", "tuyen-sinh", "xét tuyển", "phương thức tuyển",
            "điểm chuẩn", "thông báo tuyển sinh", "chỉ tiêu tuyển sinh",
        ],
    },
    {
        "type": "enrollment",
        "keywords": [
            "nhập học", "nhap-hoc", "thủ tục nhập học", "hồ sơ nhập học",
            "ngày nhập học", "đăng ký nhập học",
        ],
    },
    {
        "type": "curriculum",
        "keywords": [
            "chuyên ngành", "chuyen-nganh", "chương trình đào tạo",
            "ngành học", "khoa học máy tính", "kỹ thuật phần mềm",
            "trí tuệ nhân tạo", "an toàn thông tin", "vi mạch bán dẫn",
            "công nghệ thông tin", "thiết kế đồ họa", "ô tô số",
            "quản trị kinh doanh", "ngôn ngữ anh", "tiếng hàn",
            "truyền thông", "marketing",
        ],
    },
]

# ---------------------------------------------------------------------------- #
# Quy tắc xác định campus
# ---------------------------------------------------------------------------- #
_CAMPUS_RULES: List[Dict[str, Any]] = [
    {"campus": "ha_noi", "keywords": ["hà nội", "ha-noi", "campus hà nội", "/hn/", "hoa lạc"]},
    {
        "campus": "ho_chi_minh",
        "keywords": [
            "tp. hồ chí minh", "ho-chi-minh", "tp hồ chí minh",
            "campus tp.", "/hcm/", "bình dương", "hcmtuyensinh",
        ],
    },
    {"campus": "da_nang", "keywords": ["đà nẵng", "da-nang", "/dn/", "campus đà nẵng"]},
    {"campus": "can_tho", "keywords": ["cần thơ", "can-tho", "campus cần thơ"]},
    {"campus": "quy_nhon", "keywords": ["quy nhơn", "quy-nhon", "campus quy nhơn"]},
]

# ---------------------------------------------------------------------------- #
# Quy tắc trích xuất cohort/năm học
# ---------------------------------------------------------------------------- #
_COHORT_PATTERNS = [
    r"\bK\d{2}\b",            # K22, K21, ...
    r"\bkhóa\s+\d{4}\b",     # khóa 2026
    r"\bnhập học năm\s+\d{4}\b",
    r"\bnăm học\s+\d{4}[–-]\d{2,4}\b",
]

_EFFECTIVE_DATE_PATTERNS = [
    r"\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b",  # ISO format
    r"\bnăm\s+(20\d{2})\b",
    r"\b(20\d{2})\b",
]


def classify_doc_type(text: str, url: str = "") -> str:
    """Phân loại loại tài liệu dựa trên nội dung và URL."""
    combined = (text + " " + url).lower()
    for rule in _DOC_TYPE_RULES:
        if any(kw in combined for kw in rule["keywords"]):
            return rule["type"]
    return "general"


def classify_campus(text: str, url: str = "") -> str:
    """Xác định campus từ nội dung và URL."""
    combined = (text + " " + url).lower()
    for rule in _CAMPUS_RULES:
        if any(kw in combined for kw in rule["keywords"]):
            return rule["campus"]
    return "all"


def extract_cohorts(text: str) -> List[str]:
    """Trích xuất danh sách cohort/khóa học từ văn bản."""
    cohorts = set()
    for pattern in _COHORT_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            cohorts.add(m.group(0).strip())
    return list(cohorts) if cohorts else ["All"]


def extract_effective_date(text: str, url: str = "") -> str:
    """Trích xuất ngày hiệu lực từ văn bản. Trả về chuỗi ISO date hoặc năm."""
    combined = text + " " + url
    m = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", combined)
    if m:
        return m.group(0)
    m = re.search(r"\b(202[4-9]|203\d)\b", combined)
    if m:
        return f"{m.group(1)}-01-01"
    return "2026-01-01"


class MetadataEnricher:
    """Gán và chuẩn hóa siêu dữ liệu cho các văn bản chunk."""

    def __init__(self, default_metadata: Optional[Dict[str, Any]] = None):
        self.default_metadata = default_metadata or {
            "cohort": "All",
            "effective_date": "2026-01-01",
            "category": "general",
        }

    def enrich_chunk(
        self,
        chunk_id: str,
        title: str,
        text: str,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Tạo đối tượng corpus chunk hoàn chỉnh với đầy đủ metadata."""
        meta = self.default_metadata.copy()
        if custom_metadata:
            meta.update(custom_metadata)

        return {
            "id": chunk_id,
            "title": title,
            "text": text,
            "metadata": meta,
        }

    def enrich_from_document(
        self,
        chunk_id: str,
        title: str,
        text: str,
        doc: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Tạo chunk corpus đầy đủ theo cả Contract 1 lẫn schema legacy.
        """
        url = doc.get("url", "")
        content_for_classification = text + " " + title + " " + url

        doc_type = classify_doc_type(content_for_classification, url)
        campus = classify_campus(content_for_classification, url)
        cohorts = extract_cohorts(content_for_classification)
        effective_date = extract_effective_date(content_for_classification, url)

        source = url or doc.get("source", "")

        metadata = {
            "doc_id": chunk_id,
            "source_file": doc.get("source", ""),
            "url": url,
            "effective_date": effective_date,
            "applies_to_cohort": cohorts,
            "source_doc_version": "v1.0",
            "doc_type": doc_type,
            "campus": campus,
            "crawled_at": doc.get("crawled_at", ""),
            "depth": doc.get("depth"),
        }

        return {
            "id": chunk_id,
            "title": title,
            "text": text,
            "metadata": metadata,
            "doc_id": chunk_id,
            "source": source,
            "effective_date": effective_date,
            "applies_to_cohort": cohorts,
            "source_doc_version": "v1.0",
            "doc_type": doc_type,
            "campus": campus,
        }

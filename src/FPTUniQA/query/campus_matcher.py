"""Module nhận diện và chuẩn hóa phân hiệu (Campus) dùng chung cho hệ thống. Phụ trách: TV3."""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Optional


class CampusCode(str, Enum):
    HANOI = "HANOI"
    HCM = "HCM"
    DANANG = "DANANG"
    CANTHO = "CANTHO"
    QUYNHON = "QUYNHON"


# Tên hiển thị chuẩn tiếng Việt (khớp với khóa trong structured_data.json)
CAMPUS_DISPLAY_NAMES: Dict[str, str] = {
    CampusCode.HANOI.value: "Hà Nội",
    CampusCode.HCM.value: "TP. Hồ Chí Minh",
    CampusCode.DANANG.value: "Đà Nẵng",
    CampusCode.CANTHO.value: "Cần Thơ",
    CampusCode.QUYNHON.value: "Quy Nhơn",
}

# Ánh xạ từ tên hiển thị sang mã chuẩn
DISPLAY_NAME_TO_CODE: Dict[str, str] = {
    v: k for k, v in CAMPUS_DISPLAY_NAMES.items()
}

# Các từ khóa và regex đại diện cho từng phân hiệu
CAMPUS_PATTERNS = [
    (
        CampusCode.CANTHO.value,
        ["cần thơ", "can tho", "cantho", "cầntho", "ct"],
        r"c[aần\?]?n\s*th[oơ\?]",
    ),
    (
        CampusCode.QUYNHON.value,
        ["quy nhơn", "quy nhon", "quynhon", "bình định", "binh dinh", "qn"],
        r"quy\s*nh[oơ\?]",
    ),
    (
        CampusCode.DANANG.value,
        ["đà nẵng", "da nang", "danang", "đn", "dn"],
        r"d[aà\?]\s*n[aẵ\?]ng",
    ),
    (
        CampusCode.HCM.value,
        [
            "tp. hcm",
            "tp hcm",
            "hồ chí minh",
            "ho chi minh",
            "hcm",
            "tphcm",
            "tp.hcm",
            "sài gòn",
            "sai gon",
        ],
        r"h[oồ\?]\s*ch[ií\?]\s*m[ií\?]nh",
    ),
    (
        CampusCode.HANOI.value,
        [
            "hà nội",
            "ha noi",
            "hanoi",
            "hòa lạc",
            "hoa lac",
            "hn",
            "hl",
        ],
        r"h[aà\?]\s*n[oộ\?]i",
    ),
]


def match_campus_code(text: Optional[str]) -> Optional[str]:
    """Nhận diện văn bản đầu vào và trả về mã phân hiệu chuẩn (VD: 'HANOI', 'HCM').

    Nếu không nhận diện được, trả về None.
    """
    if not text or not str(text).strip():
        return None

    raw_text = str(text).strip().lower()

    # Kiểm tra trực tiếp nếu text đã là mã hoặc tên hiển thị
    text_upper = raw_text.upper()
    if text_upper in CAMPUS_DISPLAY_NAMES:
        return text_upper

    for code, display_name in CAMPUS_DISPLAY_NAMES.items():
        if raw_text == display_name.lower():
            return code

    # Kiểm tra danh sách từ khóa và regex
    for code, keywords, regex in CAMPUS_PATTERNS:
        # Khớp theo từ khóa đầy đủ / cụm từ
        for kw in keywords:
            # Nếu từ khóa ngắn (<= 2 ký tự như hn, ct, dn, qn) thì cần match theo word boundary
            if len(kw) <= 2:
                if re.search(rf"\b{re.escape(kw)}\b", raw_text):
                    return code
            else:
                if kw in raw_text:
                    return code

        # Khớp theo regex chịu lỗi encoding
        if regex and re.search(regex, raw_text):
            return code

    return None


def match_campus(text: Optional[str], return_code: bool = False) -> Optional[str]:
    """Chuẩn hóa phân hiệu từ văn bản đầu vào.

    Args:
        text: Chuỗi câu hỏi hoặc tên campus thô.
        return_code: Nếu True trả về mã ('HANOI', 'HCM'...), nếu False trả về tên tiếng Việt ('Hà Nội'...).

    Returns:
        Mã hoặc tên tiếng Việt phân hiệu, hoặc None nếu không nhận diện được.
    """
    code = match_campus_code(text)
    if not code:
        return None
    if return_code:
        return code
    return CAMPUS_DISPLAY_NAMES.get(code, code)

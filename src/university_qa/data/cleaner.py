"""Làm sạch, xóa ký tự đặc biệt, chuẩn hóa khoảng trắng văn bản tiếng Việt. Phụ trách: TV1."""

import re
import unicodedata


def clean_vietnamese_text(text: str) -> str:
    """Chuẩn hóa Unicode tiếng Việt (NFC), loại bỏ khoảng trắng thừa và ký tự điều khiển rác."""
    if not text:
        return ""

    # Chuẩn hóa bảng mã Unicode sang chuẩn NFC
    text = unicodedata.normalize("NFC", text)

    # Loại bỏ ký tự điều khiển ASCII vô hình (ngoại trừ xuống dòng \n và tab \t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Chuẩn hóa khoảng trắng ngang liên tiếp
    text = re.sub(r"[ \t]+", " ", text)

    # Chuẩn hóa số dòng trống liên tiếp (tối đa 2 dòng trống)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_headers_footers(text: str, patterns: list = None) -> str:
    """Loại bỏ số trang, tiêu đề đầu/cuối trang từ file trích xuất PDF."""
    if patterns is None:
        patterns = [
            r"Trang\s+\d+\s*/\s*\d+",
            r"Page\s+\d+\s+of\s+\d+",
            r"^\d+\s*$",
        ]
    cleaned = text
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.MULTILINE)
    return clean_vietnamese_text(cleaned)

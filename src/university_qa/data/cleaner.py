"""Làm sạch, xóa ký tự đặc biệt, chuẩn hóa khoảng trắng văn bản tiếng Việt. Phụ trách: TV1."""

import re
import unicodedata


def clean_handbook_noise(text: str) -> str:
    """Loại bỏ watermark Studocu, running header/footer Sổ tay sinh viên FPT."""
    if not text:
        return ""

    patterns = [
        # Watermark Studocu
        r"Studocu is not sponsored or endorsed by any college or university",
        r"Downloaded by [^\n]+",
        r"Scan to open on Studeersnel",
        r"lms\.fpt\.edu\.vn",
        # Running header / footer của Sổ tay sinh viên FPT
        r"SỔ TAY (TÂN )?SINH VIÊN\s*[\|\-–]\s*\d+",
        r"SỔ TAY SINH VIÊN K\d+\s*\(Trích phần [^\)]+\)",
        r"^\s*Trường Đại học FPT\s*$",
        r"^\s*\d{1,3}\s*$",  # Số trang đơn lẻ trên dòng
    ]

    cleaned = text
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    # Chuẩn hóa các ký tự bullet đặc thù từ PDF sang gạch đầu dòng chuẩn
    cleaned = re.sub(r"[•·]\s*", "- ", cleaned)

    # Nối các từ bị ngắt dòng do dấu gạch nối cuối dòng trong PDF (ví dụ: "chương-\ntrình" -> "chương trình")
    cleaned = re.sub(r"(\b[a-zA-ZÀ-ỹ]+)-\n([a-zA-ZÀ-ỹ]+\b)", r"\1\2", cleaned)

    return cleaned


def clean_vietnamese_text(text: str) -> str:
    """Chuẩn hóa Unicode tiếng Việt (NFC), loại bỏ khoảng trắng thừa và ký tự điều khiển rác."""
    if not text:
        return ""

    # Loại bỏ tạp âm Sổ tay sinh viên & Studocu trước
    text = clean_handbook_noise(text)

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

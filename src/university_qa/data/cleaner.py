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


def normalize_vnd_amounts(text: str) -> str:
    """
    Chuẩn hóa định dạng số tiền VND trong văn bản.

    Ví dụ: "31.600.000" -> "31,600,000 VND"
    Chú ý: Trong tiếng Việt, dấu chấm thường dùng làm phân cách hàng nghìn.
    Hàm này chuẩn hóa về định dạng không mơ hồ và gắn đơn vị VND rõ ràng.
    """
    def _reformat_vnd(m: re.Match) -> str:
        raw = m.group(0)
        numeric = raw.replace(".", "")
        if len(numeric) >= 4:
            formatted = f"{int(numeric):,}"
            return f"{formatted} VND"
        return raw

    text = re.sub(r"\b\d{1,3}(?:\.\d{3}){1,}\b", _reformat_vnd, text)
    return text


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


def deduplicate_whitespace_lines(text: str) -> str:
    """Xóa các dòng chỉ chứa khoảng trắng và thu gọn dòng trống thừa."""
    lines = text.splitlines()
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False
    return "\n".join(cleaned_lines).strip()


def clean_document_text(text: str, normalize_numbers: bool = True) -> str:
    """
    Pipeline làm sạch đầy đủ cho văn bản tài liệu tuyển sinh FPT.

    Args:
        text: Văn bản thô cần làm sạch.
        normalize_numbers: Nếu True, chuẩn hóa số tiền VND.
    """
    text = clean_vietnamese_text(text)
    if normalize_numbers:
        text = normalize_vnd_amounts(text)
    text = deduplicate_whitespace_lines(text)
    return text

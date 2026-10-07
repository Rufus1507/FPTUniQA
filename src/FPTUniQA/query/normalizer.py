"""Chuẩn hóa câu truy vấn của sinh viên trước khi đưa vào pipeline. Phụ trách: TV3."""

import re
import unicodedata


def normalize_query(text: str) -> str:
    """Chuẩn hóa chuỗi truy vấn:

    1. Chuẩn hóa bảng mã Unicode tiếng Việt sang chuẩn dựng sẵn (NFC).
    2. Loại bỏ khoảng trắng thừa ở đầu/cuối và khoảng trắng liên tiếp ở giữa.
    3. Chuyển thành chữ thường các từ khóa thông thường (lowercase).
    """
    if not text:
        return ""

    # Chuẩn hóa Unicode sang dạng dựng sẵn NFC
    normalized = unicodedata.normalize("NFC", text)

    # Thay thế các ký tự khoảng trắng liên tiếp (tab, newlines, nhiều dấu cách) thành 1 dấu cách
    normalized = re.sub(r"\s+", " ", normalized)

    # Chuyển về chữ thường
    normalized = normalized.strip().lower()

    return normalized

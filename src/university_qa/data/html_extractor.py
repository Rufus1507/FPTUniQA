"""
Module bóc tách nội dung sạch từ HTML thô của website tuyển sinh FPT.
Phụ trách: TV1.

Chiến lược trích xuất:
1. Dùng trafilatura làm extractor chính (main article body, tables).
2. Fallback sang BeautifulSoup cho các trang có cấu trúc đặc biệt.
3. Bảo tồn bảng biểu học phí dưới dạng Markdown table.
4. Phân tích metadata trang (title, H1, canonical URL).
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

try:
    import trafilatura
    _TRAFILATURA_AVAILABLE = True
except ImportError:
    _TRAFILATURA_AVAILABLE = False


def _extract_tables_as_markdown(soup: BeautifulSoup) -> List[str]:
    """Trích xuất tất cả bảng HTML thành định dạng Markdown table."""
    tables_md = []
    for table in soup.find_all("table"):
        rows_md = []
        all_rows = table.find_all("tr")
        for i, row in enumerate(all_rows):
            cells = row.find_all(["th", "td"])
            if not cells:
                continue
            cell_texts = [c.get_text(" ", strip=True).replace("\n", " ") for c in cells]
            rows_md.append("| " + " | ".join(cell_texts) + " |")
            if i == 0:
                rows_md.append("|" + "|".join(["---"] * len(cells)) + "|")
        if rows_md:
            tables_md.append("\n".join(rows_md))
    return tables_md


def extract_from_html(html: str, fallback_title: str = "") -> Dict[str, str]:
    """
    Trích xuất nội dung sạch từ chuỗi HTML.

    Returns:
        dict với các key:
            - title: tiêu đề trang
            - h1: nội dung thẻ H1 đầu tiên
            - text: nội dung văn bản chính đã làm sạch
            - tables_md: các bảng biểu dạng Markdown (nếu có)
            - combined_text: text + tables_md gộp lại (dùng để chunking)
    """
    soup = BeautifulSoup(html, "html.parser")

    # --- Title ---
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        # Bỏ phần suffix " - Trường Đại học FPT" hoặc " – Campus ..."
        title = re.sub(r"\s*[\-–|]\s*Trường Đại học FPT.*$", "", title).strip()
        title = re.sub(r"\s*–\s*Campus.*$", "", title).strip()

    if not title:
        title = fallback_title

    # --- H1 ---
    h1 = ""
    h1_tag = soup.find("h1")
    if h1_tag:
        h1 = h1_tag.get_text(" ", strip=True)

    # --- Bảng biểu ---
    tables_md = _extract_tables_as_markdown(soup)

    # --- Văn bản chính: ưu tiên trafilatura ---
    main_text = ""
    if _TRAFILATURA_AVAILABLE:
        extracted = trafilatura.extract(
            html,
            include_tables=False,  # Ta tự xử lý bảng bằng BS4
            include_comments=False,
            include_images=False,
            no_fallback=False,
        )
        if extracted and len(extracted.split()) >= 30:
            main_text = extracted

    # Fallback: BeautifulSoup lấy article/main/entry-content
    if not main_text:
        content_tags = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="entry-content")
            or soup.find("div", class_="content")
            or soup.find("div", class_="post-content")
        )
        if content_tags:
            # Xóa nav, script, style, form
            for tag in content_tags.find_all(["script", "style", "nav", "form", "footer"]):
                tag.decompose()
            main_text = content_tags.get_text(" ", strip=True)
        else:
            # Fallback cuối: toàn bộ body
            body = soup.find("body")
            if body:
                for tag in body.find_all(["script", "style", "nav", "form", "footer", "header"]):
                    tag.decompose()
                main_text = body.get_text(" ", strip=True)

    # Chuẩn hóa khoảng trắng
    main_text = re.sub(r"[ \t]+", " ", main_text or "")
    main_text = re.sub(r"\n{3,}", "\n\n", main_text).strip()

    # combined = text + bảng biểu (nếu có bảng chưa xuất hiện trong main_text)
    combined_parts = [main_text] if main_text else []
    if tables_md:
        combined_parts.append("\n\n".join(tables_md))
    combined_text = "\n\n".join(combined_parts).strip()

    return {
        "title": title,
        "h1": h1,
        "text": main_text,
        "tables_md": tables_md,
        "combined_text": combined_text,
    }


def load_html_file(file_path: str | Path) -> Optional[Dict[str, str]]:
    """
    Đọc và trích xuất nội dung từ một tệp HTML.

    Returns:
        dict kết quả trích xuất, hoặc None nếu file không đọc được.
    """
    path = Path(file_path)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        result = extract_from_html(html, fallback_title=path.stem)
        result["source_file"] = path.name
        return result
    except Exception:
        return None

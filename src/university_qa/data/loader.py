"""Trích xuất nội dung văn bản từ các tệp thô (TXT, MD, PDF, DOCX, XLSX). Phụ trách: TV1.
Kiến trúc Hybrid Document Ingestion Gateway:
- PyMuPDF: Động cơ chính tốc độ cao cho PDF (bảo toàn phân tách số trang --- [Trang X] ---).
- Microsoft MarkItDown: Động cơ chuyển đổi hợp nhất cho Office (DOCX, XLSX, PPTX, CSV, HTML, MD).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Bộ nạp tài liệu thông minh (Hybrid Gateway) từ thư mục dữ liệu thô."""

    def __init__(self, supported_extensions: Optional[List[str]] = None):
        self.supported_extensions = supported_extensions or [
            ".txt",
            ".md",
            ".json",
            ".pdf",
            ".docx",
            ".xlsx",
            ".csv",
            ".html",
        ]
        self._markitdown_converter = None

    def _get_markitdown(self):
        """Khởi tạo lười (lazy load) đối tượng MarkItDown."""
        if self._markitdown_converter is None:
            try:
                from markitdown import MarkItDown
                self._markitdown_converter = MarkItDown()
            except ImportError:
                raise ImportError(
                    "Thư viện markitdown chưa được cài đặt. Vui lòng chạy: pip install markitdown"
                )
        return self._markitdown_converter

    def load_with_markitdown(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Trích xuất và chuyển đổi tệp bất kỳ thành Markdown chuẩn bằng Microsoft MarkItDown."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

        md = self._get_markitdown()
        result = md.convert(str(path))
        text_content = result.text_content if hasattr(result, "text_content") else str(result)

        return {
            "source": str(path.name),
            "file_path": str(path),
            "content": text_content,
            "engine": "markitdown",
        }

    def load_pdf(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Trích xuất nội dung văn bản từ tệp PDF sử dụng PyMuPDF bảo toàn chỉ số trang."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tệp PDF không tồn tại: {file_path}")

        try:
            import pymupdf
        except ImportError:
            raise ImportError("Vui lòng cài đặt pymupdf: pip install pymupdf")

        doc = pymupdf.open(str(path))
        pages_content = []
        full_text_parts = []

        for page_idx, page in enumerate(doc, start=1):
            text = page.get_text()
            stripped_text = text.strip()
            # Bỏ qua các trang rỗng hoặc trang bìa chỉ chứa ảnh không có chữ
            if len(stripped_text) < 15:
                continue

            page_header = f"--- [Trang {page_idx}] ---"
            pages_content.append({"page": page_idx, "text": stripped_text})
            full_text_parts.append(f"{page_header}\n{stripped_text}")

        full_content = "\n\n".join(full_text_parts)
        num_pages = len(doc)
        doc.close()

        return {
            "source": str(path.name),
            "file_path": str(path),
            "content": full_content,
            "num_pages": num_pages,
            "extracted_pages": len(pages_content),
            "engine": "pymupdf",
        }

    def load_file(self, file_path: Union[str, Path], engine: str = "auto") -> Dict[str, Any]:
        """Đọc và trích xuất nội dung từ tệp theo cơ chế định tuyến thông minh (Smart Router)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

        suffix = path.suffix.lower()

        # Nếu người dùng chỉ định dùng MarkItDown tường minh
        if engine == "markitdown":
            return self.load_with_markitdown(path)

        # Định tuyến theo loại tệp
        if suffix == ".pdf":
            # PDF ưu tiên PyMuPDF để bảo đảm tốc độ và phân đoạn theo số trang
            try:
                return self.load_pdf(path)
            except Exception as e:
                logger.warning(f"PyMuPDF load thất bại với {path.name}: {e}. Chuyển sang fallback MarkItDown.")
                return self.load_with_markitdown(path)

        elif suffix in [".docx", ".xlsx", ".pptx", ".csv", ".html"]:
            # Office và cấu trúc bảng ưu tiên MarkItDown
            return self.load_with_markitdown(path)

        elif suffix in [".txt", ".md"]:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "source": str(path.name),
                "file_path": str(path),
                "content": content,
                "engine": "native_text",
            }

        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {
                "source": str(path.name),
                "file_path": str(path),
                "content": content,
                "engine": "fallback_text",
            }

    def load_directory(self, dir_path: Union[str, Path], engine: str = "auto") -> List[Dict[str, Any]]:
        """Duyệt và nạp tất cả các file được hỗ trợ trong thư mục."""
        path = Path(dir_path)
        documents = []
        for file in sorted(path.glob("**/*")):
            if file.is_file() and file.suffix.lower() in self.supported_extensions:
                documents.append(self.load_file(file, engine=engine))
        return documents

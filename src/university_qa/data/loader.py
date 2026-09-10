"""Trích xuất nội dung văn bản từ các tệp thô (TXT, MD, PDF, DOCX). Phụ trách: TV1."""

from pathlib import Path
from typing import Dict, List, Union


class DocumentLoader:
    """Bộ nạp tài liệu từ thư mục dữ liệu thô."""

    def __init__(self, supported_extensions: List[str] = None):
        self.supported_extensions = supported_extensions or [".txt", ".md", ".json"]

    def load_file(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """Đọc nội dung một file văn bản."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

        suffix = path.suffix.lower()
        if suffix in [".txt", ".md"]:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # Dự phòng cho PDF/DOCX (có thể tích hợp PyPDF2/python-docx)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        return {
            "source": str(path.name),
            "file_path": str(path),
            "content": content,
        }

    def load_directory(self, dir_path: Union[str, Path]) -> List[Dict[str, str]]:
        """Duyệt và đọc tất cả các file trong thư mục."""
        path = Path(dir_path)
        documents = []
        for file in path.glob("**/*"):
            if file.is_file() and file.suffix.lower() in self.supported_extensions:
                documents.append(self.load_file(file))
        return documents

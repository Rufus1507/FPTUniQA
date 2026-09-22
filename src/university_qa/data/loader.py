"""Trích xuất nội dung văn bản từ các tệp thô (TXT, MD, PDF, HTML). Phụ trách: TV1."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from university_qa.data.html_extractor import load_html_file


class DocumentLoader:
    """Bộ nạp tài liệu từ thư mục dữ liệu thô, hỗ trợ HTML kèm crawl_manifest."""

    def __init__(self, supported_extensions: Optional[List[str]] = None):
        self.supported_extensions = supported_extensions or [".txt", ".md", ".json", ".html"]

    def load_file(self, file_path: Union[str, Path]) -> Optional[Dict[str, str]]:
        """Đọc nội dung một file văn bản hoặc HTML."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

        suffix = path.suffix.lower()

        if suffix == ".html":
            result = load_html_file(path)
            if result is None:
                return None
            return {
                "source": path.name,
                "file_path": str(path),
                "content": result["combined_text"],
                "title": result["title"],
                "h1": result["h1"],
                "tables_md": result["tables_md"],
                "raw_text": result["text"],
            }

        elif suffix in [".txt", ".md"]:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        return {
            "source": str(path.name),
            "file_path": str(path),
            "content": content,
            "title": path.stem,
            "h1": "",
            "tables_md": [],
            "raw_text": content,
        }

    def load_directory(
        self,
        dir_path: Union[str, Path],
        manifest_path: Optional[Union[str, Path]] = None,
    ) -> List[Dict[str, str]]:
        """
        Duyệt và đọc tất cả các file trong thư mục.

        Args:
            dir_path: Thư mục chứa tệp dữ liệu thô.
            manifest_path: Đường dẫn tới crawl_manifest.jsonl (tùy chọn).
                Nếu cung cấp, mỗi document sẽ được bổ sung thêm
                url, status_code, depth, crawled_at, content_hash từ manifest.
        """
        path = Path(dir_path)

        # Nạp manifest nếu có
        manifest_by_filename: Dict[str, Dict] = {}
        if manifest_path:
            mp = Path(manifest_path)
            if mp.exists():
                with open(mp, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        raw_file = record.get("raw_file", "")
                        if raw_file:
                            fname = Path(raw_file).name
                            # Nếu trùng, ưu tiên bản ghi có status_code == 200
                            if fname not in manifest_by_filename or record.get("status_code") == 200:
                                manifest_by_filename[fname] = record

        documents = []
        for file in sorted(path.glob("**/*")):
            if not file.is_file():
                continue
            if file.suffix.lower() not in self.supported_extensions:
                continue

            doc = self.load_file(file)
            if doc is None:
                continue

            # Gắn thông tin manifest nếu có
            manifest_rec = manifest_by_filename.get(file.name, {})
            doc["url"] = manifest_rec.get("final_url") or manifest_rec.get("url", "")
            doc["status_code"] = manifest_rec.get("status_code")
            doc["depth"] = manifest_rec.get("depth")
            doc["crawled_at"] = manifest_rec.get("crawled_at", "")
            doc["content_hash"] = manifest_rec.get("content_hash", "")
            doc["source_domain"] = "fpt_admission"

            documents.append(doc)

        return documents

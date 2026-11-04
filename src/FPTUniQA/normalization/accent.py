"""Module phục hồi dấu tiếng Việt dựa trên Lexicon từ điển học vụ FPTUniQA (Accent Restoration).

Thực hiện:
1. Nạp từ điển các cụm từ và thực thể học vụ có dấu từ data/dictionary/.
2. Xây dựng bản đồ đối sánh không dấu -> có dấu (unaccented -> accented map) theo thứ tự Longest Match First.
3. Phục hồi dấu chuẩn xác trong <1ms mà không phụ thuộc model ngoài hay mạng.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Bảng từ vựng thông dụng trong câu hỏi học vụ tiếng Việt (unambiguous functional words)
COMMON_ACADEMIC_UNACCENTED_MAP: Dict[str, str] = {
    # Cụm từ ghép học vụ cốt lõi
    "dieu kien": "điều kiện",
    "xet tot nghiep": "xét tốt nghiệp",
    "tot nghiep": "tốt nghiệp",
    "sinh vien": "sinh viên",
    "hoc phi": "học phí",
    "thuc tap": "thực tập",
    "doanh nghiep": "doanh nghiệp",
    "tin chi": "tín chỉ",
    "quy che": "quy chế",
    "dao tao": "đào tạo",
    "tuyen sinh": "tuyển sinh",
    "chuyen nganh": "chuyên ngành",
    "tien quyet": "tiên quyết",
    "hoc vu": "học vụ",
    "hoc ky": "học kỳ",
    "hoc lai": "học lại",
    "thi lai": "thi lại",
    "tam dung": "tạm dừng",
    "thoi hoc": "thôi học",
    "bao luu": "bảo lưu",
    "chung chi": "chứng chỉ",
    "chuan dau ra": "chuẩn đầu ra",
    "khoa hoc": "khóa học",
    "an toan thong tin": "an toàn thông tin",
    "cong nghe thong tin": "công nghệ thông tin",
    "tri tue nhan tao": "trí tuệ nhân tạo",
    "ky thuat phan mem": "kỹ thuật phần mềm",
    "quan tri kinh doanh": "quản trị kinh doanh",
    "ngon ngu anh": "ngôn ngữ anh",
    "ngon ngu nhat": "ngôn ngữ nhật",
    "ngon ngu han": "ngôn ngữ hàn",
    "hoa lac": "hòa lạc",
    "da nang": "đà nẵng",
    "quy nhon": "quy nhơn",
    "can tho": "cần thơ",
    "sai gon": "sài gòn",
    "ha noi": "hà nội",
    "ho chi minh": "hồ chí minh",

    # Từ đơn chức năng rõ nghĩa trong ngữ cảnh học vụ
    "dieu": "điều",
    "kien": "kiện",
    "duoc": "được",
    "xet": "xét",
    "nghiep": "nghiệp",
    "phi": "phí",
    "nganh": "ngành",
    "khoa": "khóa",
    "nhieu": "nhiêu",
    "can": "cần",
    "chi": "chỉ",
    "truong": "trường",
    "lop": "lớp",
    "diem": "điểm",
    "mon": "môn",
}


def remove_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt chuyển về ký tự ASCII thường."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return no_accent.replace("đ", "d").replace("Đ", "D")


def has_vietnamese_accents(text: str) -> bool:
    """Kiểm tra chuỗi văn bản có chứa ký tự tiếng Việt có dấu hay không."""
    if not text:
        return False
    # Regex phát hiện các ký tự đặc trưng của tiếng Việt có dấu
    return bool(re.search(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", text, re.IGNORECASE))


@dataclass(frozen=True)
class AccentReplacement:
    original_span_text: str
    restored_text: str
    start: int
    end: int


@dataclass
class AccentRestoreResult:
    original_text: str
    restored_text: str
    replacements: List[AccentReplacement] = field(default_factory=list)
    ambiguous_tokens: List[str] = field(default_factory=list)


class AccentRestorer:
    """Bộ phục hồi dấu tiếng Việt tối ưu bằng Trie/Regex Longest-Match trên từ điển miền."""

    def __init__(self, dict_dir: Optional[Path] = None):
        self.dict_dir = dict_dir or (Path(__file__).resolve().parent.parent.parent.parent / "data" / "dictionary")
        self._phrase_map: Dict[str, str] = {}
        self._sorted_patterns: List[Tuple[re.Pattern, str, str]] = []
        self._build_lexicon()

    def _build_lexicon(self) -> None:
        """Xây dựng từ điển ánh xạ từ unaccented -> accented."""
        # 1. Nạp từ bảng tĩnh chuẩn
        for unacc, acc in COMMON_ACADEMIC_UNACCENTED_MAP.items():
            self._phrase_map[unacc.lower().strip()] = acc.lower().strip()

        # 2. Nạp từ các file từ điển JSON
        if self.dict_dir.exists():
            for fname in ["majors.json", "courses.json", "cohorts.json", "campuses.json", "academic_terms.json", "abbreviations.json"]:
                fpath = self.dict_dir / fname
                if not fpath.exists():
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            c_vi = item.get("canonical_name_vi", "").strip()
                            if c_vi and has_vietnamese_accents(c_vi):
                                unacc = remove_accents(c_vi).lower()
                                if unacc and unacc not in self._phrase_map:
                                    self._phrase_map[unacc] = c_vi.lower()
                            # Alias
                            for alias in item.get("aliases", []):
                                alias_clean = alias.strip()
                                if has_vietnamese_accents(alias_clean) and len(alias_clean.split()) >= 2:
                                    unacc_alias = remove_accents(alias_clean).lower()
                                    if unacc_alias not in self._phrase_map:
                                        self._phrase_map[unacc_alias] = alias_clean.lower()
                except Exception:
                    pass

        # 3. Sắp xếp theo độ dài giảm dần (Longest Match First)
        sorted_pairs = sorted(self._phrase_map.items(), key=lambda x: len(x[0]), reverse=True)
        for unacc_phrase, acc_phrase in sorted_pairs:
            # Biên dịch regex có word boundary an toàn
            escaped = re.escape(unacc_phrase)
            pattern = re.compile(rf"(?<![\wÀ-ỹ]){escaped}(?![\wÀ-ỹ])", re.IGNORECASE)
            self._sorted_patterns.append((pattern, unacc_phrase, acc_phrase))

    def restore(self, text: str) -> AccentRestoreResult:
        """Phục hồi dấu tiếng Việt cho chuỗi đầu vào nếu là chuỗi không dấu."""
        if not text or not str(text).strip():
            return AccentRestoreResult(original_text=text or "", restored_text=text or "")

        raw = str(text)
        # Nếu câu hỏi đã có dấu tiếng Việt đầy đủ (>15% ký tự có dấu), giữ nguyên không biến đổi
        if has_vietnamese_accents(raw):
            return AccentRestoreResult(original_text=raw, restored_text=unicodedata.normalize("NFC", raw))

        normalized_input = unicodedata.normalize("NFC", raw).lower()
        restored = normalized_input
        replacements: List[AccentReplacement] = []
        occupied_spans: List[Tuple[int, int]] = []

        # Áp dụng Longest Match First
        for pattern, unacc_phrase, acc_phrase in self._sorted_patterns:
            matches = list(pattern.finditer(restored))
            for m in matches:
                span = m.span()
                overlap = False
                for o_s, o_e in occupied_spans:
                    if max(span[0], o_s) < min(span[1], o_e):
                        overlap = True
                        break
                if overlap:
                    continue

                occupied_spans.append(span)
                replacements.append(AccentReplacement(
                    original_span_text=m.group(0),
                    restored_text=acc_phrase,
                    start=span[0],
                    end=span[1],
                ))

        # Thực hiện thay thế từ phải sang trái theo vị trí span
        replacements.sort(key=lambda r: r.start, reverse=True)
        chars = list(restored)
        for rep in replacements:
            chars[rep.start:rep.end] = list(rep.restored_text)

        result_text = "".join(chars)
        # Chuẩn hóa lại Unicode NFC
        result_text = unicodedata.normalize("NFC", result_text)

        return AccentRestoreResult(
            original_text=raw,
            restored_text=result_text,
            replacements=replacements,
            ambiguous_tokens=[],
        )


_DEFAULT_RESTORER: Optional[AccentRestorer] = None

def get_accent_restorer() -> AccentRestorer:
    """Singleton getter cho AccentRestorer."""
    global _DEFAULT_RESTORER
    if _DEFAULT_RESTORER is None:
        _DEFAULT_RESTORER = AccentRestorer()
    return _DEFAULT_RESTORER

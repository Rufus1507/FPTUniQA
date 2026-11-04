"""Động cơ Chuẩn hóa Thực thể Học vụ (FPTUniQA Entity Normalization Engine).

Thực hiện:
1. Nạp toàn bộ kho từ điển miền (data/dictionary/) vào bộ nhớ.
2. Đối sánh từ khóa & cụm từ theo quy tắc Longest Match First và ranh giới từ (word boundaries).
3. Hỗ trợ đối sánh không dấu (diacritic-insensitive matching).
4. Phân giải đa nghĩa ngữ cảnh (Contextual Disambiguation).
5. Trích xuất slots_hint tương thích với Contract 3 (ParsedQuery).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.normalization.engine")

# Đường dẫn mặc định tới thư mục từ điển
_DEFAULT_DICT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "dictionary"


def normalize_n1(s: str) -> str:
    """N1 (strict) = NFKC(s) -> lowercase -> trim -> collapse whitespace."""
    if not s:
        return ""
    norm = unicodedata.normalize("NFKC", s).lower()
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def remove_accents(text: str) -> str:
    """Chuyển chuỗi tiếng Việt có dấu thành không dấu."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return no_accent.replace("đ", "d").replace("Đ", "D")


@dataclass
class NormalizedEntity:
    """Mô hình dữ liệu thực thể đã được nhận diện và chuẩn hóa."""
    entity_id: str
    entity_type: str
    canonical_name: str
    canonical_name_vi: str
    code: Optional[str] = None
    matched_alias: str = ""
    span: Tuple[int, int] = (0, 0)
    confidence: float = 1.0
    verified: bool = True
    source_reference: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "code": self.code,
            "canonical_name": self.canonical_name,
            "canonical_name_vi": self.canonical_name_vi,
            "matched_alias": self.matched_alias,
            "span": list(self.span),
            "confidence": self.confidence,
            "verified": self.verified,
            "source_reference": self.source_reference,
            "notes": self.notes,
        }


@dataclass
class EntityReplacement:
    original_text: str
    canonical_text: str
    start: int
    end: int
    entity_id: str


@dataclass
class EntityAnalysisResult:
    canonical_text: str
    entities: List[NormalizedEntity] = field(default_factory=list)
    replacements: List[EntityReplacement] = field(default_factory=list)
    slots_hint: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizationResult:
    """Đầu ra có cấu trúc từ quá trình chuẩn hóa câu hỏi."""
    original_query: str
    normalized_query: str
    entities: List[NormalizedEntity] = field(default_factory=list)
    slots_hint: Dict[str, Any] = field(default_factory=dict)
    unresolved_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "entities": [e.to_dict() for e in self.entities],
            "slots_hint": self.slots_hint,
            "unresolved_terms": self.unresolved_terms,
        }


class EntityNormalizer:
    """Bộ chuẩn hóa thực thể học vụ dựa trên Từ điển miền (Domain Dictionary)."""

    def __init__(self, dict_dir: Optional[Path] = None):
        self.dict_dir = Path(dict_dir) if dict_dir else _DEFAULT_DICT_DIR
        self._entities_by_id: Dict[str, Dict[str, Any]] = {}
        self._sorted_alias_patterns: List[Tuple[re.Pattern, str, str, Dict[str, Any]]] = []
        self._sorted_unaccented_patterns: List[Tuple[re.Pattern, str, str, Dict[str, Any]]] = []
        self._load_dictionary()

    def _load_dictionary(self) -> None:
        """Nạp toàn bộ các file từ điển và xây dựng cấu trúc index tối ưu."""
        if not self.dict_dir.exists():
            logger.warning(f"Thư mục từ điển không tồn tại: {self.dict_dir}")
            return

        files = [
            "majors.json",
            "courses.json",
            "cohorts.json",
            "campuses.json",
            "academic_terms.json",
            "abbreviations.json",
        ]

        raw_aliases: List[Tuple[str, str, Dict[str, Any]]] = []

        for fname in files:
            fpath = self.dict_dir / fname
            if not fpath.exists():
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    entries = json.load(f)
                    for entry in entries:
                        eid = entry.get("entity_id")
                        if not eid:
                            continue
                        self._entities_by_id[eid] = entry
                        aliases = entry.get("aliases", [])
                        for a in aliases:
                            n1_alias = normalize_n1(a)
                            if n1_alias:
                                raw_aliases.append((n1_alias, eid, entry))
            except Exception as e:
                logger.error(f"Lỗi khi nạp từ điển {fname}: {e}")

        # Sắp xếp alias theo độ dài giảm dần (Longest Match First)
        # Ưu tiên cụm từ dài trước để tránh partial-word collision
        raw_aliases.sort(key=lambda x: len(x[0]), reverse=True)

        # Biên dịch regex pattern cho từng alias với ranh giới từ (\b hoặc non-word)
        seen_patterns = set()
        for alias, eid, entry in raw_aliases:
            key = (alias, eid)
            if key in seen_patterns:
                continue
            seen_patterns.add(key)

            escaped = re.escape(alias)
            # Dùng regex lookaround an toàn cho cả ký tự tiếng Việt có dấu
            # Ranh giới: không liền kề ký tự chữ hoặc số
            pattern = re.compile(rf"(?<![\wÀ-ỹ]){escaped}(?![\wÀ-ỹ])", re.IGNORECASE)
            self._sorted_alias_patterns.append((pattern, alias, eid, entry))

        # Xây dựng danh sách pattern không dấu (Diacritic-Folding Fallback Pass)
        # Giúp nhận diện hoàn hảo các câu hỏi gõ lỗi dấu nửa chừng (ví dụ "công nghe thông tin")
        raw_unacc: List[Tuple[str, str, Dict[str, Any]]] = []
        seen_unacc = set()
        for alias, eid, entry in raw_aliases:
            unacc = remove_accents(alias)
            if not unacc:
                continue
            # Chỉ nạp các cụm từ nhiều từ hoặc dài >= 4 ký tự để tránh va chạm từ viết tắt ngắn
            if " " in unacc or len(unacc) >= 4 or unacc != alias:
                key = (unacc, eid)
                if key not in seen_unacc:
                    seen_unacc.add(key)
                    raw_unacc.append((unacc, eid, entry))

        raw_unacc.sort(key=lambda x: len(x[0]), reverse=True)
        for unacc, eid, entry in raw_unacc:
            p = re.compile(rf"(?<![\wÀ-ỹ]){re.escape(unacc)}(?![\wÀ-ỹ])", re.IGNORECASE)
            self._sorted_unaccented_patterns.append((p, unacc, eid, entry))

        logger.info(
            f"Đã nạp {len(self._entities_by_id)} entities, "
            f"{len(self._sorted_alias_patterns)} alias patterns và "
            f"{len(self._sorted_unaccented_patterns)} unaccented fallback patterns từ {self.dict_dir}"
        )

    def normalize(self, query: str) -> NormalizationResult:
        """Thực hiện chuẩn hóa câu hỏi và trích xuất thực thể."""
        if not query or not str(query).strip():
            return NormalizationResult(original_query=query, normalized_query="")



        raw_query = str(query)
        clean_query = normalize_n1(raw_query)

        detected_entities: List[NormalizedEntity] = []
        occupied_spans: List[Tuple[int, int]] = []
        detected_entity_ids: Set[str] = set()

        # Đối sánh Longest Match First trên clean_query
        for pattern, alias, eid, entry in self._sorted_alias_patterns:
            # Nếu entity này đã được phát hiện ở cùng span hoặc ưu tiên cao hơn, có thể tiếp tục
            for match in pattern.finditer(clean_query):
                span = match.span()

                # Kiểm tra span có bị overlap với thực thể dài hơn đã match trước không
                overlap = False
                for o_start, o_end in occupied_spans:
                    if max(span[0], o_start) < min(span[1], o_end):
                        overlap = True
                        break

                if overlap:
                    continue

                # Phân giải đa nghĩa ngữ cảnh (Disambiguation)
                matched_text = match.group(0)
                if not self._check_disambiguation(clean_query, span, entry, eid):
                    continue

                # Nếu là abbreviation có resolves_to trỏ sang entity khác
                target_entry = entry
                target_eid = eid
                resolves_to = entry.get("resolves_to")
                if resolves_to and resolves_to in self._entities_by_id:
                    target_eid = resolves_to
                    target_entry = self._entities_by_id[resolves_to]

                occupied_spans.append(span)
                detected_entity_ids.add(target_eid)

                norm_entity = NormalizedEntity(
                    entity_id=target_eid,
                    entity_type=target_entry.get("entity_type", "unknown"),
                    code=target_entry.get("code"),
                    canonical_name=target_entry.get("canonical_name", ""),
                    canonical_name_vi=target_entry.get("canonical_name_vi", ""),
                    matched_alias=matched_text,
                    span=span,
                    confidence=float(target_entry.get("confidence", 1.0)),
                    verified=bool(target_entry.get("verified", True)),
                    source_reference=target_entry.get("source_reference", {}),
                    notes=target_entry.get("notes"),
                )
                detected_entities.append(norm_entity)

        # Pass 2: Diacritic-Folding Fallback Pass (đối sánh không dấu trên các span còn trống)
        # Tự động khắc phục lỗi người dùng gõ thiếu/sai dấu tiếng Việt nửa chừng
        unacc_query = remove_accents(clean_query)
        for pattern, unacc_alias, eid, entry in self._sorted_unaccented_patterns:
            for match in pattern.finditer(unacc_query):
                span = match.span()

                # Kiểm tra span có bị overlap với thực thể đã khớp ở Pass 1 không
                overlap = False
                for o_start, o_end in occupied_spans:
                    if max(span[0], o_start) < min(span[1], o_end):
                        overlap = True
                        break

                if overlap:
                    continue

                if not self._check_disambiguation(clean_query, span, entry, eid):
                    continue

                target_entry = entry
                target_eid = eid
                resolves_to = entry.get("resolves_to")
                if resolves_to and resolves_to in self._entities_by_id:
                    target_eid = resolves_to
                    target_entry = self._entities_by_id[resolves_to]

                occupied_spans.append(span)
                detected_entity_ids.add(target_eid)

                matched_text = clean_query[span[0]:span[1]]
                norm_entity = NormalizedEntity(
                    entity_id=target_eid,
                    entity_type=target_entry.get("entity_type", "unknown"),
                    code=target_entry.get("code"),
                    canonical_name=target_entry.get("canonical_name", ""),
                    canonical_name_vi=target_entry.get("canonical_name_vi", ""),
                    matched_alias=matched_text,
                    span=span,
                    confidence=float(target_entry.get("confidence", 1.0)) * 0.95,
                    verified=bool(target_entry.get("verified", True)),
                    source_reference=target_entry.get("source_reference", {}),
                    notes=f"{target_entry.get('notes', '')} [Diacritic-folded match '{unacc_alias}']".strip(),
                )
                detected_entities.append(norm_entity)

        # Xử lý các năm học chưa verified (ví dụ "khóa 2027", "năm 2028")
        unresolved_years = self._extract_unresolved_years(clean_query, occupied_spans)
        for span, year_str in unresolved_years:
            norm_entity = NormalizedEntity(
                entity_id=f"RAW_YEAR_{year_str}",
                entity_type="cohort",
                code=year_str,
                canonical_name=f"Admission Year {year_str}",
                canonical_name_vi=f"Năm nhập học {year_str}",
                matched_alias=year_str,
                span=span,
                confidence=0.5,
                verified=False,
                source_reference={"file": "unverified_query"},
                notes=f"Năm {year_str} chưa có trong dữ liệu văn bản chính thức của repository.",
            )
            detected_entities.append(norm_entity)
            occupied_spans.append(span)

        # Sắp xếp thực thể theo thứ tự xuất hiện trong câu
        detected_entities.sort(key=lambda e: e.span[0])

        # Đóng gói slots_hint cho Contract 3
        slots_hint = self._build_slots_hint(clean_query, detected_entities)

        # Sinh normalized_query (thay thế các từ viết tắt học vụ phổ biến an toàn)
        normalized_text = self._build_normalized_query(clean_query, detected_entities)

        return NormalizationResult(
            original_query=raw_query,
            normalized_query=normalized_text,
            entities=detected_entities,
            slots_hint=slots_hint,
            unresolved_terms=[],
        )

    def analyze_with_spans(self, text: str) -> EntityAnalysisResult:
        norm_res = self.normalize(text)
        entities = norm_res.entities

        replacements: List[EntityReplacement] = []
        clean_text = normalize_n1(text)
        chars = list(clean_text)

        sorted_entities = sorted(entities, key=lambda e: e.span[0], reverse=True)
        for e in sorted_entities:
            s, end = e.span
            canon = e.canonical_name_vi or e.canonical_name
            if canon:
                replacements.append(EntityReplacement(
                    original_text=clean_text[s:end],
                    canonical_text=canon,
                    start=s,
                    end=end,
                    entity_id=e.entity_id,
                ))
                chars[s:end] = list(canon)

        canonical_text = "".join(chars)
        return EntityAnalysisResult(
            canonical_text=canonical_text,
            entities=entities,
            replacements=replacements,
            slots_hint=norm_res.slots_hint,
        )

    def _check_disambiguation(
        self,
        query: str,
        span: Tuple[int, int],
        entry: Dict[str, Any],
        eid: str,
    ) -> bool:
        """Kiểm tra các quy tắc phân giải ngữ cảnh khi từ khóa có nhiều nghĩa."""
        rules = entry.get("disambiguation_rules") or {}

        start, end = span
        matched_str = query[start:end].strip().lower()
        before_text = query[max(0, start - 30):start].strip().lower()
        after_text = query[end:min(len(query), end + 30)].strip().lower()

        # Quy tắc cho CAMPUS_ALL (Tránh match nhầm 'chứng chỉ' / 'minh chứng' thành cơ sở 'chung')
        if eid == "CAMPUS_ALL":
            raw_span = query[start:end].lower()
            if "chứng" in raw_span or "chưng" in raw_span:
                return False
            if any(before_text.endswith(w) for w in ["chứng", "chung", "minh", "bằng", "làm"]):
                return False
            if any(after_text.startswith(w) for w in ["chỉ", "chi", "nhận", "nhan", "từ", "tu"]):
                return False

        # Quy tắc cho MAJOR_NNA (Ngôn ngữ Anh vs Chứng chỉ/Ngoại ngữ tiếng Anh)
        if eid == "MAJOR_NNA":
            cert_signals = (
                "chứng chỉ", "chung chi", "chuẩn", "chuan", "chuẩn đầu ra", "chuan dau ra",
                "trình độ", "trinh do", "tiêu chuẩn", "tieu chuan", "bằng", "bang",
                "ngoại ngữ", "ngoai ngu", "môn", "mon", "học phần", "hoc phan"
            )
            if any(before_text.endswith(p) or f"{p} " in before_text for p in cert_signals):
                return False
            q_full = query.lower()
            if "chứng chỉ tiếng anh" in q_full or "chuẩn tiếng anh" in q_full or "ngoại ngữ tiếng anh" in q_full:
                return False

        # Quy tắc cho Môn học NWC203C (Mạng máy tính)
        if eid == "COURSE_NWC203C":
            q_full = query.lower()
            if any(w in q_full for w in ["casio", "bỏ túi", "bo tui", "cầm tay", "cam tay", "fx-", "fx "]):
                return False
            if "mang" in matched_str and "mạng" not in matched_str:
                return False

        # Quy tắc cho AI (ngành học vs môn học vs đại từ nghi vấn tiếng Việt)
        if eid == "MAJOR_AI":
            prefer_courses = rules.get("prefer_course_if_preceded_by", [])
            if any(before_text.endswith(w) for w in prefer_courses):
                # Nếu từ đứng trước chỉ môn học (môn ai, học phần ai), bỏ qua MAJOR_AI
                return False

            # Nếu alias khớp là "ai" hoặc "a.i."
            if matched_str in ("ai", "a.i."):
                # 1. Các tiền tố khẳng định là ngành học/học vụ:
                major_prefixes = (
                    "ngành", "nganh", "chuyên ngành", "chuyen nganh", "khoa",
                    "học phí", "hoc phi", "chương trình", "chuong trinh", "tuyển sinh", "tuyen sinh",
                    "điểm chuẩn", "diem chuan", "lớp", "lop", "khóa", "khoa", "kỳ", "ky"
                )
                if any(before_text.endswith(p) or f"{p} " in before_text for p in major_prefixes):
                    return True

                # 2. Các giới từ hỏi người (hỏi ai, gặp ai, liên hệ ai, nhờ ai, cho ai, với ai...):
                pronoun_before = (
                    "hỏi", "hoi", "gặp", "gap", "liên hệ", "lien he", "nhờ", "nho",
                    "cho", "với", "voi", "tìm", "tim", "bảo", "bao", "do"
                )
                if any(before_text.endswith(b) for b in pronoun_before):
                    return False

                # 3. Đại từ nghi vấn đi kèm vị ngữ nhân xưng:
                pronoun_after_patterns = [
                    r"^là\s+(người|thầy|cô|giảng\s+viên|hiệu\s+trưởng|trưởng\s+khoa|ai|cán\s+bộ|chủ\s+nhiệm|sinh\s+viên\s+nào)",
                    r"^la\s+(nguoi|thay|co|giang\s+vien|hieu\s+truong|truong\s+khoa|ai|can\s+bo|chu\s+nhiem|sinh\s+vien\s+nao)",
                    r"^(dạy|day|sáng\s+lập|sang\s+lap|viết|viet|phụ\s+trách|phu\s+trach|quản\s+lý|quan\s+ly|chịu\s+trách\s+nhiệm|chiu\s+trach\s+nhiem)(|\s|$)",
                    r"^(có\s+thể\s+(giải\s+đáp|hỗ\s+trợ|giúp|cho\s+biết)|co\s+the\s+(giai\s+dap|ho\s+tro|giup|cho\s+biet))(|\s|$)",
                    r"^(hướng\s+dẫn|huong\s+dan|ra\s+đề|ra\s+de|chấm\s+thi|cham\s+thi)(|\s|$)",
                ]
                for pat in pronoun_after_patterns:
                    if re.search(pat, after_text, re.IGNORECASE):
                        return False

                # 4. Nếu "ai" đứng ở đầu câu và theo sau là "là":
                # "AI là gì?", "AI là ngành gì?" -> True
                # "Ai là người...", "Ai là..." không có từ hỏi định nghĩa -> False
                if re.match(r"^(là|la)", after_text):
                    if re.search(r"(gì|gi|như\s+thế\s+nào|nhu\s+the\s+nao|ra\s+sao|viết\s+tắt|viet\s+tat)", after_text):
                        return True
                    if start == 0 or any(before_text.endswith(w) for w in ("cho em hỏi", "cho hỏi", "xin hỏi", "em hỏi")):
                        return False

        return True

    def _extract_unresolved_years(
        self,
        query: str,
        occupied_spans: List[Tuple[int, int]],
    ) -> List[Tuple[Tuple[int, int], str]]:
        """Nhận diện các số năm tuyển sinh 202x chưa nằm trong từ điển verified."""
        unresolved = []
        year_regex = re.compile(r"\b(202[0-9]|203[0-9])\b")
        for match in year_regex.finditer(query):
            span = match.span()
            year_str = match.group(1)
            # Kiểm tra xem span này đã thuộc về COHORT_Kxx chưa
            is_occupied = any(max(span[0], s[0]) < min(span[1], s[1]) for s in occupied_spans)
            if not is_occupied:
                unresolved.append((span, year_str))
        return unresolved

    def _build_slots_hint(
        self,
        query: str,
        entities: List[NormalizedEntity],
    ) -> Dict[str, Any]:
        """Tổng hợp các slots học vụ từ thực thể đã nhận diện để cung cấp cho Semantic Parser."""
        slots: Dict[str, Any] = {}

        for e in entities:
            if e.entity_type == "major":
                # Lấy tên ngắn hoặc mã ngắn tương thích router
                short_code = self._get_major_short_code(e)
                slots["program"] = short_code
            elif e.entity_type == "cohort":
                slots["cohort"] = e.code or e.canonical_name
            elif e.entity_type == "campus":
                slots["campus"] = e.canonical_name_vi or e.canonical_name
            elif e.entity_type == "course":
                if e.code:
                    slots["course_code"] = e.code
            elif e.entity_type == "academic_term":
                if e.entity_id == "TERM_CANH_BAO_HOC_VU":
                    slots["topic"] = "canh_bao_hoc_vu"
                elif e.entity_id == "TERM_TOT_NGHIEP":
                    slots["topic"] = "tot_nghiep"
                elif e.entity_id == "TERM_TIN_CHI":
                    slots["topic"] = "tin_chi"
                elif e.entity_id == "TERM_TIEN_QUYET":
                    slots["course_aspect"] = "prerequisite"

        # Tự động gán course_aspect nếu câu hỏi có mã môn
        if "course_code" in slots and not slots.get("course_aspect"):
            q_lower = query.lower()
            q_unacc = remove_accents(q_lower)
            if any(w in q_lower for w in ["học những gì", "học gì", "nội dung", "kiến thức", "chủ đề", "syllabus"]) or any(w in q_unacc for w in ["hoc nhung gi", "hoc gi", "noi dung", "kien thuc", "chu de"]):
                slots["course_aspect"] = "syllabus"
            elif any(w in q_lower for w in ["giáo trình", "sách", "tài liệu", "tác giả", "ai viết"]) or any(w in q_unacc for w in ["giao trinh", "sach", "tai lieu", "tac gia", "ai viet"]):
                slots["course_aspect"] = "textbook"
            elif any(w in q_lower for w in ["tiên quyết", "trước", "cần qua môn"]) or any(w in q_unacc for w in ["tien quyet", "truoc", "can qua mon"]):
                slots["course_aspect"] = "prerequisite"
            elif any(w in q_lower for w in ["tín chỉ", "bao nhiêu tín", "số tín"]) or any(w in q_unacc for w in ["tin chi", "bao nhieu tin", "so tin"]):
                slots["course_aspect"] = "credits"
            elif any(w in q_lower for w in ["học tiếp", "kỳ sau", "tiếp theo", "kế tiếp", "sau môn", "tiếp nối"]):
                slots["course_aspect"] = "next_course"
            elif any(w in q_lower for w in ["thi", "kiểm tra", "pe", "eos", "đánh giá", "hình thức", "bài tập lớn", "assignment", "asm", "bài tập"]) or any(w in q_unacc for w in ["kiem tra", "danh gia", "hinh thuc", "bai tap lon"]):
                slots["course_aspect"] = "assessment"
            elif any(w in q_lower for w in ["kỳ", "học kỳ", "kỳ mấy"]) or any(w in q_unacc for w in ["ky", "hoc ky", "ky may"]):
                slots["course_aspect"] = "semester"

        return slots

    def _get_major_short_code(self, entity: NormalizedEntity) -> str:
        """Ánh xạ mã ngắn ngành tương thích với bảng constants của Semantic Parser."""
        mapping = {
            "MAJOR_AI": "AI",
            "MAJOR_CNTT": "CNTT",
            "MAJOR_KTPM": "KTPM",
            "MAJOR_ATTT": "An toàn thông tin",
            "MAJOR_DATA_SCIENCE": "Khoa học dữ liệu và ứng dụng",
            "MAJOR_SEMICONDUCTOR": "Vi mạch bán dẫn",
            "MAJOR_AUTOMOTIVE": "Công nghệ ô tô số",
            "MAJOR_HTTT": "Hệ thống thông tin",
            "MAJOR_TKDH": "Thiết kế đồ họa và mỹ thuật số",
            "MAJOR_TTDPT": "Truyền thông đa phương tiện",
            "MAJOR_QTKD": "Quản trị kinh doanh",
            "MAJOR_KDQT": "Kinh doanh quốc tế",
            "MAJOR_MARKETING": "Marketing",
            "MAJOR_NNA": "Ngôn ngữ Anh",
            "MAJOR_NNH": "Ngôn ngữ Hàn Quốc",
            "MAJOR_NNT": "Ngôn ngữ Trung Quốc",
            "MAJOR_NNN": "Ngôn ngữ Nhật",
            "MAJOR_LAW": "Luật kinh tế",
        }
        return mapping.get(entity.entity_id, entity.canonical_name_vi or entity.canonical_name)

    def _build_normalized_query(
        self,
        clean_query: str,
        entities: List[NormalizedEntity],
    ) -> str:
        """Sinh chuỗi truy vấn chuẩn hóa, mở rộng các từ viết tắt an toàn."""
        # Hiện tại giữ nguyên cấu trúc tự nhiên để BM25 & E5 không bị lệch embedding,
        # chỉ trả về chuỗi clean_query đã chuẩn hóa Unicode và khoảng trắng.
        return clean_query


# Singleton instance
_INSTANCE: Optional[EntityNormalizer] = None


def get_entity_normalizer(dict_dir: Optional[Path] = None) -> EntityNormalizer:
    """Lấy thể hiện duy nhất (Singleton) của EntityNormalizer."""
    global _INSTANCE
    if _INSTANCE is None or dict_dir is not None:
        _INSTANCE = EntityNormalizer(dict_dir=dict_dir)
    return _INSTANCE

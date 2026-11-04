"""Chuẩn hóa câu truy vấn của sinh viên trước khi đưa vào pipeline. Phụ trách: TV3."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from FPTUniQA.normalization.accent import get_accent_restorer, has_vietnamese_accents
from FPTUniQA.normalization.engine import EntityNormalizer, get_entity_normalizer
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.query.normalizer")

# Giới hạn tối đa độ dài chuỗi truy vấn retrieval để ngăn tràn bộ nhớ
MAX_RETRIEVAL_QUERY_CHARS = 500


@dataclass(frozen=True)
class NormalizedQuery:
    """Mô hình dữ liệu truy vấn đã chuẩn hóa chuyên biệt cho giai đoạn Retrieval (Bước 4, Bước 8)."""
    original: str
    normalized: str
    retrieval_query: str
    is_unaccented: bool
    entity_expansion: Tuple[str, ...] = field(default_factory=tuple)
    slots_hint: Dict[str, Any] = field(default_factory=dict)


def normalize_query(text: str) -> str:
    """Chuẩn hóa chuỗi truy vấn (tương thích ngược hoàn toàn):

    1. Chuẩn hóa bảng mã Unicode tiếng Việt sang chuẩn dựng sẵn (NFC).
    2. Loại bỏ khoảng trắng thừa ở đầu/cuối và khoảng trắng liên tiếp ở giữa.
    """
    if not text:
        return ""

    # Chuẩn hóa Unicode sang dạng dựng sẵn NFC
    normalized = unicodedata.normalize("NFC", text)

    # Thay thế các ký tự khoảng trắng liên tiếp thành 1 dấu cách
    normalized = re.sub(r"\s+", " ", normalized)

    # Loại bỏ khoảng trắng thừa đầu cuối
    normalized = normalized.strip()

    return normalized


def normalize_for_retrieval(text: str) -> NormalizedQuery:
    """Chuẩn hóa sâu và mở rộng truy vấn phục vụ bộ máy tìm kiếm BM25 và Dense Retrieval."""
    if not text or not str(text).strip():
        return NormalizedQuery(
            original=text or "",
            normalized="",
            retrieval_query="",
            is_unaccented=False,
            entity_expansion=tuple(),
            slots_hint={},
        )

    raw = str(text)
    clean = normalize_query(raw)
    is_unacc = not has_vietnamese_accents(clean)

    entity_norm = get_entity_normalizer()
    analysis_res = entity_norm.analyze_with_spans(clean)
    slots_hint = analysis_res.slots_hint

    expansion_phrases: List[str] = []
    for ent in analysis_res.entities:
        canon = ent.canonical_name_vi or ent.canonical_name
        if canon and canon not in expansion_phrases:
            expansion_phrases.append(canon)

    accent_replacement_count = 0
    ambiguous_token_count = 0

    if is_unacc:
        # Trường hợp 1: Truy vấn tiếng Việt không dấu (Accent Restoration + Expansion)
        restorer = get_accent_restorer()
        restore_res = restorer.restore(clean)
        restored_text = restore_res.restored_text
        accent_replacement_count = len(restore_res.replacements)
        ambiguous_token_count = len(restore_res.ambiguous_tokens)

        # Ghép chuỗi truy vấn tìm kiếm: [câu đã phục hồi dấu] + [thực thể canonical chưa xuất hiện]
        query_parts = [restored_text]
        for phrase in expansion_phrases:
            if phrase.lower() not in restored_text.lower():
                query_parts.append(phrase)

        retrieval_query = " ".join(query_parts).strip()
        retrieval_query = re.sub(r"\s+", " ", retrieval_query)

        # Safeguard: Nếu câu query mở rộng vượt quá giới hạn an toàn, rút gọn về câu đã phục hồi dấu
        if len(retrieval_query) > MAX_RETRIEVAL_QUERY_CHARS:
            retrieval_query = restored_text[:MAX_RETRIEVAL_QUERY_CHARS].strip()

        logger.debug(
            f"[Metric] query_has_vietnamese_accents={not is_unacc}, "
            f"accent_replacement_count={accent_replacement_count}, "
            f"entity_match_count={len(analysis_res.entities)}, "
            f"retrieval_query_length_delta={len(retrieval_query) - len(clean)}, "
            f"ambiguous_token_count={ambiguous_token_count}"
        )
    else:
        # Trường hợp 2: Truy vấn đã có dấu sẵn (Bảo toàn 100% ngữ nghĩa gốc)
        retrieval_query = clean

    return NormalizedQuery(
        original=raw,
        normalized=clean,
        retrieval_query=retrieval_query,
        is_unaccented=is_unacc,
        entity_expansion=tuple(expansion_phrases),
        slots_hint=slots_hint,
    )

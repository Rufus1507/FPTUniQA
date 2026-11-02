"""Package Chuẩn hóa Thực thể và Từ điển miền FPTUniQA (Domain Dictionary & Entity Normalization).
Phụ trách: TV3 / Core Architecture.
"""

from FPTUniQA.normalization.engine import (
    EntityNormalizer,
    NormalizationResult,
    NormalizedEntity,
    get_entity_normalizer,
)

__all__ = [
    "EntityNormalizer",
    "NormalizationResult",
    "NormalizedEntity",
    "get_entity_normalizer",
]

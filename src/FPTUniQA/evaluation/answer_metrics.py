"""Tính toán chỉ số chất lượng câu trả lời: Faithfulness và Answer Relevance."""

import re
from typing import Set


def _get_words(text: str) -> Set[str]:
    return set(re.findall(r"\b\w+\b", text.lower()))


def compute_faithfulness(generated_answer: str, context_text: str) -> float:
    """Ước lượng độ trung thực (Faithfulness): Tỷ lệ từ khóa trong câu trả lời được chứng thực bởi context."""
    ans_words = _get_words(generated_answer)
    ctx_words = _get_words(context_text)

    if not ans_words:
        return 0.0

    # Lọc bỏ các từ dừng cơ bản
    stop_words = {"và", "là", "các", "có", "trong", "được", "cho", "của", "đến", "khi", "những"}
    meaningful_words = ans_words - stop_words
    if not meaningful_words:
        return 1.0

    supported = meaningful_words.intersection(ctx_words)
    return len(supported) / len(meaningful_words)


def compute_answer_relevance(generated_answer: str, golden_answer: str) -> float:
    """Ước lượng mức độ tương đồng giữa câu trả lời sinh ra và đáp án chuẩn (Jaccard Similarity)."""
    words_gen = _get_words(generated_answer)
    words_gold = _get_words(golden_answer)

    union = words_gen.union(words_gold)
    if not union:
        return 0.0

    return len(words_gen.intersection(words_gold)) / len(union)

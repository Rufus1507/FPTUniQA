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


import math
from collections import Counter


def compute_bleu4(reference: str, hypothesis: str) -> float:
    """Tính word-level BLEU-4 với smoothing cơ bản (cho so sánh với R2GQA)."""
    ref_tokens = re.findall(r"\b\w+\b", reference.lower())
    hyp_tokens = re.findall(r"\b\w+\b", hypothesis.lower())

    if not hyp_tokens or not ref_tokens:
        return 0.0

    # Brevity penalty
    c = len(hyp_tokens)
    r = len(ref_tokens)
    bp = 1.0 if c > r else math.exp(1 - r / c) if c > 0 else 0.0

    precisions = []
    for n in range(1, 5):
        if len(hyp_tokens) < n:
            precisions.append(0.0)
            continue
        hyp_ngrams = Counter([tuple(hyp_tokens[i:i+n]) for i in range(len(hyp_tokens) - n + 1)])
        ref_ngrams = Counter([tuple(ref_tokens[i:i+n]) for i in range(len(ref_tokens) - n + 1)])

        clipped_count = 0
        total_count = sum(hyp_ngrams.values())
        for ng, count in hyp_ngrams.items():
            clipped_count += min(count, ref_ngrams.get(ng, 0))

        p_n = clipped_count / total_count if total_count > 0 else 0.0
        precisions.append(p_n)

    if precisions[0] == 0.0:
        return 0.0

    smoothed = [p if p > 0 else 1e-4 for p in precisions]
    log_sum = sum(math.log(p) for p in smoothed) / 4.0
    bleu = bp * math.exp(log_sum)
    return round(min(1.0, bleu), 4)


def compute_rouge_l(reference: str, hypothesis: str) -> float:
    """Tính Longest Common Subsequence (LCS) ROUGE-L F1 (cho so sánh với R2GQA)."""
    ref_tokens = re.findall(r"\b\w+\b", reference.lower())
    hyp_tokens = re.findall(r"\b\w+\b", hypothesis.lower())

    m = len(ref_tokens)
    n = len(hyp_tokens)
    if m == 0 or n == 0:
        return 0.0

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs = dp[m][n]
    r_lcs = lcs / m
    p_lcs = lcs / n
    if r_lcs + p_lcs == 0:
        return 0.0
    f_lcs = (2 * r_lcs * p_lcs) / (r_lcs + p_lcs)
    return round(f_lcs, 4)

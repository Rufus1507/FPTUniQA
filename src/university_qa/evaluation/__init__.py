"""Module đánh giá khoa học (Retrieval metrics, Answer metrics, Hallucination, Evaluator). Cả nhóm."""

from university_qa.evaluation.answer_metrics import compute_answer_relevance, compute_faithfulness
from university_qa.evaluation.evaluator import RAGEvaluator
from university_qa.evaluation.hallucination import compute_hallucination_rate, compute_ood_rejection_accuracy
from university_qa.evaluation.retrieval_metrics import (
    compute_hit_rate_at_k,
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
)

__all__ = [
    "compute_hit_rate_at_k",
    "compute_recall_at_k",
    "compute_mrr",
    "compute_ndcg_at_k",
    "compute_faithfulness",
    "compute_answer_relevance",
    "compute_ood_rejection_accuracy",
    "compute_hallucination_rate",
    "RAGEvaluator",
]

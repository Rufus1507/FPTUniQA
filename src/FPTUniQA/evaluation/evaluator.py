"""Runner chạy toàn bộ batch test và tổng hợp báo cáo chỉ số khoa học cho hệ thống RAG."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
from FPTUniQA.evaluation.answer_metrics import compute_answer_relevance, compute_faithfulness
from FPTUniQA.evaluation.hallucination import compute_hallucination_rate, compute_ood_rejection_accuracy
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_hit_rate_at_k,
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
)
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.evaluator")


class RAGEvaluator:
    """Bộ thực thi benchmark và đánh giá toàn diện hệ thống RAG."""

    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline

    def evaluate_retrieval(
        self,
        questions: List[Dict[str, Any]],
        k_list: List[int] = None,
    ) -> Dict[str, float]:
        """Đánh giá tầng retrieval trên tập câu hỏi có nhãn."""
        k_list = k_list or [1, 3, 5, 10]
        results = {f"hit_rate@{k}": 0.0 for k in k_list}
        results.update({f"recall@{k}": 0.0 for k in k_list})
        results["mrr"] = 0.0
        results["ndcg@10"] = 0.0

        n = len(questions)
        if n == 0 or self.pipeline.retriever is None:
            return results

        for q in questions:
            query = q["query"]
            expected_ids = set(q.get("expected_doc_ids", []))
            if not expected_ids:
                continue

            # Chạy truy xuất từ retriever
            retrieved = self.pipeline.retriever.retrieve(query, top_k=max(k_list))
            retrieved_ids = [doc.get("id") or doc.get("doc_id") for doc, _ in retrieved]

            for k in k_list:
                results[f"hit_rate@{k}"] += compute_hit_rate_at_k(retrieved_ids, expected_ids, k)
                results[f"recall@{k}"] += compute_recall_at_k(retrieved_ids, expected_ids, k)

            results["mrr"] += compute_mrr(retrieved_ids, expected_ids, k=20)
            results["ndcg@10"] += compute_ndcg_at_k(retrieved_ids, expected_ids, k=10)

        for metric in results:
            results[metric] = round(results[metric] / n, 4)

        return results

    def evaluate_routing(
        self,
        questions: List[Dict[str, Any]],
        run_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Đánh giá độ chính xác định tuyến truy vấn (Routing Accuracy) so với expected_route."""
        if not questions:
            return {"routing_accuracy": 0.0, "total": 0, "correct": 0}

        correct = 0
        total = 0

        for idx, q in enumerate(questions):
            expected = q.get("expected_route")
            if not expected:
                continue
            total += 1

            if run_results and idx < len(run_results):
                actual = run_results[idx].get("route")
            else:
                res = self.pipeline.answer(q["query"])
                actual = res.get("route")

            # So khớp linh hoạt (chuẩn hóa chữ thường)
            if actual and str(actual).strip().lower() == str(expected).strip().lower():
                correct += 1

        accuracy = round(correct / total, 4) if total > 0 else 0.0
        return {
            "routing_accuracy": accuracy,
            "total_evaluated": total,
            "correct_routes": correct,
        }

    def evaluate_latency(self, latencies_ms: List[float]) -> Dict[str, float]:
        """Tính toán phân phối độ trễ (Mean, Min, Max, p50, p95, p99)."""
        if not latencies_ms:
            return {
                "mean_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
            }

        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)

        def percentile(p: float) -> float:
            idx = min(int(n * p), n - 1)
            return sorted_lat[idx]

        return {
            "mean_ms": round(sum(sorted_lat) / n, 2),
            "p50_ms": round(percentile(0.50), 2),
            "p95_ms": round(percentile(0.95), 2),
            "p99_ms": round(percentile(0.99), 2),
            "min_ms": round(sorted_lat[0], 2),
            "max_ms": round(sorted_lat[-1], 2),
        }

    def evaluate_cache_performance(self) -> Dict[str, Any]:
        """Trích xuất số liệu thống kê từ tầng RetrievalCache của retriever."""
        if self.pipeline.retriever is not None and getattr(self.pipeline.retriever, "cache", None) is not None:
            return self.pipeline.retriever.cache.get_stats()
        return {
            "hits": 0,
            "misses": 0,
            "total_lookups": 0,
            "hit_rate": 0.0,
            "cached_entries": 0,
        }

    def evaluate_answer_quality(
        self,
        questions: List[Dict[str, Any]],
        run_results: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Đo lường chất lượng câu trả lời: Faithfulness, Answer Relevance và Hallucination Rate."""
        faithfulness_scores = []
        relevance_scores = []

        for q, res in zip(questions, run_results):
            answer = res.get("answer", "")
            golden = q.get("golden_answer", "")

            # Trích xuất context từ retrieved_chunks
            chunks = res.get("retrieved_chunks", [])
            context = " ".join([c.get("text", "") or c.get("content", "") for c in chunks])

            # Nếu là câu trả lời có context, đo faithfulness
            if context:
                faith = compute_faithfulness(answer, context)
                faithfulness_scores.append(faith)

            # Đo độ tương đồng với golden answer
            if golden:
                rel = compute_answer_relevance(answer, golden)
                relevance_scores.append(rel)

        mean_faithfulness = (
            round(sum(faithfulness_scores) / len(faithfulness_scores), 4)
            if faithfulness_scores
            else 0.0
        )
        mean_relevance = (
            round(sum(relevance_scores) / len(relevance_scores), 4)
            if relevance_scores
            else 0.0
        )
        hallucination_rate = round(compute_hallucination_rate(faithfulness_scores, threshold=0.5), 4)

        return {
            "mean_faithfulness": mean_faithfulness,
            "mean_relevance": mean_relevance,
            "hallucination_rate": hallucination_rate,
            "evaluated_pairs": len(run_results),
        }

    def evaluate_ood(self, ood_questions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Đánh giá khả năng từ chối câu hỏi ngoài miền."""
        run_results = []
        for item in ood_questions:
            res = self.pipeline.run(item["query"])
            run_results.append(res)

        accuracy = compute_ood_rejection_accuracy(run_results)
        return {"ood_rejection_accuracy": round(accuracy, 4)}

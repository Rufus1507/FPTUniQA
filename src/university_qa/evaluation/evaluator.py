"""Runner chạy toàn bộ batch test và tổng hợp báo cáo chỉ số. Cả nhóm."""

from typing import Any, Dict, List
from university_qa.evaluation.answer_metrics import compute_answer_relevance, compute_faithfulness
from university_qa.evaluation.hallucination import compute_hallucination_rate, compute_ood_rejection_accuracy
from university_qa.evaluation.retrieval_metrics import (
    compute_hit_rate_at_k,
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
)
from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.evaluator")


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
        if n == 0:
            return results

        for q in questions:
            query = q["query"]
            expected_ids = set(q.get("expected_doc_ids", []))

            # Chạy truy xuất từ retriever
            retrieved = self.pipeline.retriever.retrieve(query, top_k=max(k_list))
            retrieved_ids = [doc.get("id") for doc, _ in retrieved]

            for k in k_list:
                results[f"hit_rate@{k}"] += compute_hit_rate_at_k(retrieved_ids, expected_ids, k)
                results[f"recall@{k}"] += compute_recall_at_k(retrieved_ids, expected_ids, k)

            results["mrr"] += compute_mrr(retrieved_ids, expected_ids, k=20)
            results["ndcg@10"] += compute_ndcg_at_k(retrieved_ids, expected_ids, k=10)

        for metric in results:
            results[metric] = round(results[metric] / n, 4)

        return results

    def evaluate_ood(self, ood_questions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Đánh giá khả năng từ chối câu hỏi ngoài miền."""
        run_results = []
        for item in ood_questions:
            res = self.pipeline.run(item["query"])
            run_results.append(res)

        accuracy = compute_ood_rejection_accuracy(run_results)
        return {"ood_rejection_accuracy": round(accuracy, 4)}

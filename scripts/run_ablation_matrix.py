"""Script thực thi Ma trận Đánh giá Thực nghiệm Ablation Study 6 cấu hình (A1 -> A6).

Các cấu hình đánh giá:
- A1: BM25-only (Naive RAG)
- A2: Dense-only (FAISS)
- A3: Hybrid BM25 + FAISS (Interleaved merge, không RRF)
- A4: Hybrid + RRF + Cross-Encoder Reranker
- A5: Hybrid + RRF + Reranker + Metadata Pre-filtering
- A6: Full Pipeline (+ Structured Lookup bảng học phí & OOD Classifier)
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Thêm src vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from university_qa.data.structured import StructuredDataParser
from university_qa.query.intent import IntentClassifier, QueryIntent
from university_qa.query.normalizer import QueryNormalizer
from university_qa.reranking.cross_encoder import CrossEncoderReranker
from university_qa.retrieval.bm25 import BM25Retriever
from university_qa.retrieval.dense import DenseRetriever
from university_qa.retrieval.rrf import reciprocal_rank_fusion
from university_qa.utils.io import read_jsonl, write_json
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.run_ablation_matrix")


def evaluate_configuration(
    config_name: str,
    questions: List[Dict[str, Any]],
    bm25: BM25Retriever,
    dense: DenseRetriever,
    reranker: CrossEncoderReranker,
    normalizer: QueryNormalizer,
    intent_classifier: IntentClassifier,
    structured_parser: StructuredDataParser,
) -> Dict[str, Any]:
    """Chạy đánh giá trên toàn bộ tập 30 câu hỏi cho một cấu hình cụ thể."""
    total_questions = len(questions)
    hit_at_5_count = 0
    reciprocal_ranks = []
    cohort_specific_queries = 0
    cohort_drift_count = 0
    latencies = []

    for q in questions:
        query_text = q["query"]
        category = q.get("category", "")
        target_cohort = q.get("cohort", "ALL")
        target_keywords = [kw.lower() for kw in q.get("expected_keywords", [])]
        is_ood = category == "ood"

        start_time = time.time()

        normalized_query = normalizer.normalize(query_text)
        detected_cohort, detected_campus = normalizer.extract_cohort_and_campus(normalized_query)

        retrieved_docs: List[Dict[str, Any]] = []
        structured_info: List[Dict[str, Any]] = []
        is_rejected_ood = False

        if config_name == "A1: BM25-only":
            bm25_res = bm25.retrieve(normalized_query, top_k=5)
            retrieved_docs = [doc for doc, _ in bm25_res]

        elif config_name == "A2: Dense-only":
            dense_res = dense.retrieve(normalized_query, top_k=5)
            retrieved_docs = [doc for doc, _ in dense_res]

        elif config_name == "A3: Hybrid (No RRF)":
            b_res = [doc for doc, _ in bm25.retrieve(normalized_query, top_k=5)]
            d_res = [doc for doc, _ in dense.retrieve(normalized_query, top_k=5)]
            # Xen kẽ kết quả đơn giản (interleaving)
            seen_ids = set()
            merged = []
            for i in range(max(len(b_res), len(d_res))):
                if i < len(b_res) and b_res[i]["id"] not in seen_ids:
                    merged.append(b_res[i])
                    seen_ids.add(b_res[i]["id"])
                if i < len(d_res) and d_res[i]["id"] not in seen_ids:
                    merged.append(d_res[i])
                    seen_ids.add(d_res[i]["id"])
            retrieved_docs = merged[:5]

        elif config_name == "A4: Hybrid + RRF + Reranker":
            b_res = bm25.retrieve(normalized_query, top_k=10)
            d_res = dense.retrieve(normalized_query, top_k=10)
            rrf_res = reciprocal_rank_fusion([b_res, d_res], k=60, top_n=10)
            candidates = [doc for doc, _ in rrf_res]
            reranked = reranker.rerank(normalized_query, candidates, top_n=5)
            retrieved_docs = [doc for doc, _ in reranked]

        elif config_name == "A5: Hybrid + RRF + Reranker + PreFilter":
            # Sử dụng Slot Extraction & Metadata Pre-filtering
            b_res = bm25.retrieve(
                normalized_query, top_k=10, filter_cohort=detected_cohort, filter_campus=detected_campus
            )
            d_res = dense.retrieve(
                normalized_query, top_k=10, filter_cohort=detected_cohort, filter_campus=detected_campus
            )
            rrf_res = reciprocal_rank_fusion([b_res, d_res], k=60, top_n=10)
            candidates = [doc for doc, _ in rrf_res]
            reranked = reranker.rerank(normalized_query, candidates, top_n=5)
            retrieved_docs = [doc for doc, _ in reranked]

        elif config_name == "A6: Full Pipeline":
            intent, _ = intent_classifier.classify(normalized_query)
            if intent == QueryIntent.OOD:
                is_rejected_ood = True
                retrieved_docs = []
            else:
                if intent == QueryIntent.STRUCTURED:
                    if detected_cohort:
                        structured_info = structured_parser.get_cohort_fee(detected_cohort)
                    if not structured_info:
                        structured_info = structured_parser.get_tuition_by_major(normalized_query)

                b_res = bm25.retrieve(
                    normalized_query, top_k=10, filter_cohort=detected_cohort, filter_campus=detected_campus
                )
                d_res = dense.retrieve(
                    normalized_query, top_k=10, filter_cohort=detected_cohort, filter_campus=detected_campus
                )
                rrf_res = reciprocal_rank_fusion([b_res, d_res], k=60, top_n=10)
                candidates = [doc for doc, _ in rrf_res]
                reranked = reranker.rerank(normalized_query, candidates, top_n=5)
                retrieved_docs = [doc for doc, _ in reranked]

        elapsed_ms = (time.time() - start_time) * 1000
        latencies.append(elapsed_ms)

        # 1. Đo lường Hit Rate @ 5 & MRR
        query_hit = False
        first_hit_rank = 0

        if is_ood:
            # Nếu là OOD: cấu hình A6 từ chối thành công -> Hit!
            if is_rejected_ood:
                query_hit = True
                first_hit_rank = 1
            else:
                # Các cấu hình A1-A5 không có bộ lọc OOD nên bị trôi (Fail)
                query_hit = False
        else:
            # Ghép văn bản từ retrieved docs và structured info
            combined_texts = []
            if structured_info:
                combined_texts.append(json.dumps(structured_info, ensure_ascii=False).lower())
            for d in retrieved_docs:
                combined_texts.append(f"{d.get('title', '')} {d.get('text', '')}".lower())

            for rank, text in enumerate(combined_texts, start=1):
                # Kiểm tra độ khớp từ khóa quan trọng
                matched_kw = any(kw in text for kw in target_keywords)
                if matched_kw:
                    query_hit = True
                    if first_hit_rank == 0:
                        first_hit_rank = rank
                    break

        if query_hit:
            hit_at_5_count += 1
            reciprocal_ranks.append(1.0 / first_hit_rank)
        else:
            reciprocal_ranks.append(0.0)

        # 2. Đo lường Cohort Drift Rate
        # Nếu câu hỏi nhắm tới một khóa cụ thể (K17, K18, K19, K20, K21, K22)
        if target_cohort in ["K17", "K18", "K19", "K20", "K21", "K22"]:
            cohort_specific_queries += 1
            has_drift = False
            for d in retrieved_docs[:3]:
                doc_cohorts = d.get("applies_to_cohort", [])
                if not doc_cohorts and d.get("metadata"):
                    c = d["metadata"].get("cohort")
                    doc_cohorts = [c] if c else ["ALL"]
                cohorts_upper = [str(c).upper() for c in doc_cohorts]

                # Nếu tài liệu thuộc một khóa khác hoàn toàn và không phải áp dụng chung (ALL)
                if "ALL" not in cohorts_upper and target_cohort not in cohorts_upper:
                    has_drift = True
                    break

            if has_drift:
                cohort_drift_count += 1

    hit_rate = round(hit_at_5_count / total_questions, 4)
    mrr = round(sum(reciprocal_ranks) / total_questions, 4)
    drift_rate = round(cohort_drift_count / max(cohort_specific_queries, 1), 4)
    avg_latency = round(sum(latencies) / len(latencies), 2)

    return {
        "config": config_name,
        "hit_rate@5": hit_rate,
        "mrr@5": mrr,
        "cohort_drift_rate": drift_rate,
        "cohort_accuracy": round(1.0 - drift_rate, 4),
        "avg_latency_ms": avg_latency,
    }


def main():
    logger.info("Khởi động quá trình đánh giá Ma trận Ablation Study 6 cấu hình...")

    bm25 = BM25Retriever()
    bm25.load("data/processed/bm25_index")
    logger.info(f"Nạp BM25 Index thành công ({len(bm25.documents)} docs)")

    dense = DenseRetriever()
    dense.load("data/processed/faiss_index")
    logger.info(f"Nạp FAISS Index thành công ({len(dense.documents)} docs)")

    reranker = CrossEncoderReranker()
    normalizer = QueryNormalizer()
    intent_classifier = IntentClassifier()
    structured_parser = StructuredDataParser("data/processed/structured_data.json")

    questions_path = "data/evaluation/questions.jsonl"
    questions = read_jsonl(questions_path)
    logger.info(f"Đọc {len(questions)} câu hỏi benchmark từ {questions_path}")

    configs_to_test = [
        "A1: BM25-only",
        "A2: Dense-only",
        "A3: Hybrid (No RRF)",
        "A4: Hybrid + RRF + Reranker",
        "A5: Hybrid + RRF + Reranker + PreFilter",
        "A6: Full Pipeline",
    ]

    results = []
    for cfg in configs_to_test:
        logger.info(f"Đang đánh giá cấu hình: {cfg}...")
        metrics = evaluate_configuration(
            config_name=cfg,
            questions=questions,
            bm25=bm25,
            dense=dense,
            reranker=reranker,
            normalizer=normalizer,
            intent_classifier=intent_classifier,
            structured_parser=structured_parser,
        )
        results.append(metrics)

    output_path = Path("experiments/ablation_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "results": results}, output_path)
    logger.info(f"Đã lưu báo cáo tại: {output_path}")

    # In bảng Markdown kết quả
    print("\n" + "=" * 85)
    print("                MA TRẬN ĐÁNH GIÁ THỰC NGHIỆM ABLATION STUDY (A1 - A6)")
    print("=" * 85)
    print(f"{'Cấu hình':<40} | {'Hit@5':<8} | {'MRR@5':<8} | {'Drift Rate':<12} | {'Latency (ms)':<12}")
    print("-" * 85)
    for r in results:
        drift_str = f"{r['cohort_drift_rate'] * 100:.1f}%"
        print(
            f"{r['config']:<40} | {r['hit_rate@5']:<8.4f} | {r['mrr@5']:<8.4f} | {drift_str:<12} | {r['avg_latency_ms']:<12.1f}"
        )
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()

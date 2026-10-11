"""Chấm điểm Benchmark & Ablation Study Retrieval (BM25 vs Dense vs Hybrid vs Hybrid+Reranker).

Tuần 7 & 8 Deliverables:
- C1: BM25 Only
- C2: Dense Only (FAISS FlatIP)
- C3: Hybrid (BM25 + FAISS + RRF)
- C4: Hybrid + Metadata Filter + Cross-Encoder Reranker
Đo đạc: Recall@3, Recall@5, Recall@10, MRR, Avg_Latency_ms
Lưu kết quả: experiments/hybrid/retrieval_benchmark.json và experiments/reranker/retrieval_benchmark.json
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Đảm bảo UTF-8 cho console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from FPTUniQA.retrieval.bm25 import BM25Retriever
from FPTUniQA.retrieval.dense import DenseRetriever
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.reranking.cross_encoder import CrossEncoderReranker
from FPTUniQA.retrieval.embedding import EmbeddingModel
from FPTUniQA.utils.config import load_config
from FPTUniQA.utils.io import read_jsonl
from FPTUniQA.utils.logger import get_logger

logger = get_logger("scripts.benchmark_retrieval")


def compute_metrics(qrels: Dict[str, List[str]], results: Dict[str, List[str]], k_list: List[int]) -> Dict[str, float]:
    """Tính toán Recall@K và MRR chuẩn cho IR evaluation."""
    metrics: Dict[str, float] = {}
    mrr_sum = 0.0

    for qid, rel_docs in qrels.items():
        retrieved = results.get(qid, [])
        for k in k_list:
            ret_k = retrieved[:k]
            hits = len(set(ret_k) & set(rel_docs))
            recall = hits / len(rel_docs) if rel_docs else 0.0
            metrics[f"Recall@{k}"] = metrics.get(f"Recall@{k}", 0.0) + recall

        rank = 0
        for i, doc_id in enumerate(retrieved):
            if doc_id in rel_docs:
                rank = i + 1
                break
        mrr_sum += 1.0 / rank if rank > 0 else 0.0

    num_q = len(qrels)
    if num_q > 0:
        for k in k_list:
            metrics[f"Recall@{k}"] = round(metrics[f"Recall@{k}"] / num_q, 4)
        metrics["MRR"] = round(mrr_sum / num_q, 4)

    return metrics


def main():
    config = load_config()

    # Dữ liệu mặc định giả lập
    docs = [
        {"id": "doc1", "title": "Tuition", "text": "Tuition for IT is 30m", "doc_type": "tuition", "metadata": {"doc_type": "tuition"}},
        {"id": "doc2", "title": "Rules", "text": "Students must wear ID", "doc_type": "rules", "metadata": {"doc_type": "rules"}},
    ]
    queries = [
        {"id": "q1", "text": "What is the tuition?", "rel_docs": ["doc1"], "metadata_filter": {"doc_type": "tuition"}},
        {"id": "q2", "text": "Do I need an ID?", "rel_docs": ["doc2"], "metadata_filter": {"doc_type": "rules"}},
    ]

    # Nạp corpus từ ổ đĩa nếu tồn tại
    try:
        corpus_path = config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl")
        docs_from_disk = read_jsonl(corpus_path)
        if docs_from_disk:
            docs = docs_from_disk
            corpus_ids = {str(d.get("id", d.get("doc_id"))) for d in docs}
            real_queries = [
                {
                    "id": "q_admission",
                    "text": "Đăng ký hồ sơ tuyển sinh",
                    "rel_docs": ["fpt_002097"],
                    "metadata_filter": {"doc_type": "admission"},
                },
                {
                    "id": "q_tuition_hn",
                    "text": "Học phí trường Đại học FPT tại Hà Nội",
                    "rel_docs": ["fpt_002465"],
                    "metadata_filter": {"campus": "ha_noi", "doc_type": "tuition"},
                },
                {
                    "id": "q_scholarship",
                    "text": "Học bổng Vững Tương Lai",
                    "rel_docs": ["fpt_000364"],
                    "metadata_filter": {"doc_type": "scholarship"},
                },
                {
                    "id": "q_semiconductor",
                    "text": "Thiết kế vi mạch bán dẫn",
                    "rel_docs": ["fpt_003144"],
                    "metadata_filter": {"doc_type": "curriculum"},
                },
                {
                    "id": "q_scholarship_startup",
                    "text": "Học bổng Tài năng Khởi nghiệp",
                    "rel_docs": ["fpt_003334"],
                    "metadata_filter": {"doc_type": "scholarship"},
                },
            ]
            if all(all(r in corpus_ids for r in q["rel_docs"]) for q in real_queries):
                queries = real_queries
    except Exception as e:
        logger.warning(f"Không thể nạp corpus từ disk: {e}")

    logger.info(f"Loaded {len(docs)} documents and {len(queries)} benchmark queries.")

    # Khởi tạo các thành phần retriever
    emb_model = EmbeddingModel(device="cpu")
    bm25 = BM25Retriever()
    dense = DenseRetriever(embedding_model=emb_model)
    reranker = CrossEncoderReranker(device="cpu")
    hybrid = HybridRetriever(bm25_retriever=bm25, dense_retriever=dense, reranker=reranker, rrf_k=60)

    faiss_dir = Path("data/processed/faiss_index")
    bm25_file = Path("data/processed/bm25_index/bm25_index.pkl")

    if bm25_file.exists():
        logger.info(f"Loading existing BM25 index from {bm25_file}")
        bm25.load(str(bm25_file.parent))
    else:
        bm25.index(docs)

    if faiss_dir.exists() and (faiss_dir / "dense.index").exists():
        logger.info(f"Loading existing FAISS index from {faiss_dir}")
        dense.load(str(faiss_dir))
    else:
        dense.build_index(docs)

    qrels = {q["id"]: q["rel_docs"] for q in queries}

    # Định nghĩa 4 cấu hình ablation study
    configurations = [
        ("C1_BM25", "BM25 Only"),
        ("C2_Dense", "Dense Only (FAISS FlatIP)"),
        ("C3_Hybrid", "Hybrid (BM25 + FAISS + RRF)"),
        ("C4_Hybrid_Rerank", "Hybrid + Metadata Filter + Cross-Encoder Reranker"),
    ]

    results: Dict[str, Dict[str, Any]] = {}

    for config_key, config_desc in configurations:
        logger.info(f"Đang thực thi đánh giá {config_key}: {config_desc}...")
        res_dict = {}
        latencies: List[float] = []

        for q in queries:
            query_text = q["text"]
            t0 = time.time()

            if config_key == "C1_BM25":
                ret = bm25.retrieve(query_text, top_k=10)
            elif config_key == "C2_Dense":
                ret = dense.retrieve(query_text, top_k=10)
            elif config_key == "C3_Hybrid":
                ret = hybrid.retrieve(query_text, top_k=10, candidate_k=50, rerank=False)
            elif config_key == "C4_Hybrid_Rerank":
                ret = hybrid.retrieve(
                    query_text,
                    top_k=10,
                    candidate_k=50,
                    metadata_filter=q.get("metadata_filter"),
                    rerank=True,
                )
            else:
                ret = []

            lat_ms = (time.time() - t0) * 1000.0
            latencies.append(lat_ms)
            res_dict[q["id"]] = [str(d.get("id", d.get("doc_id"))) for d, _ in ret]

        metrics = compute_metrics(qrels, res_dict, [1, 3, 5, 10])
        metrics["Avg_Latency_ms"] = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        results[config_key] = metrics

    logger.info("=== KẾT QUẢ BENCHMARK RETRIEVAL ABLATION STUDY ===")
    for key, m in results.items():
        logger.info(
            f"[{key}] R@1: {m.get('Recall@1', 0):.4f} | R@3: {m.get('Recall@3', 0):.4f} | "
            f"R@5: {m.get('Recall@5', 0):.4f} | R@10: {m.get('Recall@10', 0):.4f} | "
            f"MRR: {m.get('MRR', 0):.4f} | Avg Latency: {m.get('Avg_Latency_ms', 0):.2f} ms"
        )

    # Lưu kết quả vào cả 2 thư mục experiments
    out_hybrid = Path("experiments/hybrid")
    out_hybrid.mkdir(parents=True, exist_ok=True)
    with open(out_hybrid / "retrieval_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    out_reranker = Path("experiments/reranker")
    out_reranker.mkdir(parents=True, exist_ok=True)
    with open(out_reranker / "retrieval_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Đã ghi nhận kết quả benchmark thành công vào experiments/hybrid/ và experiments/reranker/!")


if __name__ == "__main__":
    main()

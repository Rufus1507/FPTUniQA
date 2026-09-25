"""Chấm điểm Benchmark Retrieval (BM25 vs Dense vs Hybrid)."""
import json
from pathlib import Path
from typing import Any, Dict, List
from university_qa.retrieval.bm25 import BM25Retriever
from university_qa.retrieval.dense import DenseRetriever
from university_qa.retrieval.retriever import HybridRetriever
from university_qa.retrieval.embedding import EmbeddingModel
from university_qa.utils.config import load_config
from university_qa.utils.io import read_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.benchmark_retrieval")

def compute_metrics(qrels: Dict[str, List[str]], results: Dict[str, List[str]], k_list: List[int]) -> Dict[str, float]:
    metrics = {}
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
            metrics[f"Recall@{k}"] /= num_q
        metrics["MRR"] = mrr_sum / num_q
    return metrics

def main():
    config = load_config()
    # Dummy data for test benchmark script if no data available
    docs = [
        {"id": "doc1", "title": "Tuition", "text": "Tuition for IT is 30m"},
        {"id": "doc2", "title": "Rules", "text": "Students must wear ID"}
    ]
    queries = [
        {"id": "q1", "text": "What is the tuition?", "rel_docs": ["doc1"]},
        {"id": "q2", "text": "Do I need an ID?", "rel_docs": ["doc2"]},
    ]
    
    # Normally read from disk:
    try:
        corpus_path = config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl")
        docs_from_disk = read_jsonl(corpus_path)
        if docs_from_disk: docs = docs_from_disk
    except:
        pass
    
    logger.info(f"Loaded {len(docs)} documents.")

    emb_model = EmbeddingModel(device="cpu") # Will fallback to dummy for speed if dummy logic handles it
    bm25 = BM25Retriever()
    dense = DenseRetriever(embedding_model=emb_model)
    hybrid = HybridRetriever(bm25_retriever=bm25, dense_retriever=dense, rrf_k=60)
    
    bm25.index(docs)
    dense.build_index(docs)
    
    qrels = {q["id"]: q["rel_docs"] for q in queries}
    
    results = {}
    for name, retriever_obj in [("C1_BM25", bm25), ("C2_Dense", dense), ("C3_Hybrid", hybrid)]:
        logger.info(f"Running {name}...")
        res_dict = {}
        for q in queries:
            if name == "C3_Hybrid":
                # hybrid has candidate_k instead of just top_k usually
                ret = retriever_obj.retrieve(q["text"], top_k=5, candidate_k=10)
            else:
                ret = retriever_obj.retrieve(q["text"], top_k=5)
            res_dict[q["id"]] = [str(d.get("id", d.get("doc_id"))) for d, _ in ret]
            
        metrics = compute_metrics(qrels, res_dict, [1, 3, 5])
        results[name] = metrics
        
    logger.info("=== BENCHMARK RESULTS ===")
    for name, metrics in results.items():
        logger.info(f"{name}: R@1: {metrics.get('Recall@1', 0):.4f}, R@3: {metrics.get('Recall@3', 0):.4f}, R@5: {metrics.get('Recall@5', 0):.4f}, MRR: {metrics.get('MRR', 0):.4f}")

    out_dir = Path("experiments/hybrid")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "retrieval_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()

"""Benchmark k1 và b cho thuật toán BM25."""

import json
from pathlib import Path
from typing import List, Dict, Any

from university_qa.retrieval.bm25 import BM25Retriever
from university_qa.utils.io import read_jsonl
from university_qa.utils.logger import get_logger
from university_qa.evaluation.retrieval_metrics import compute_recall_at_k, compute_mrr

logger = get_logger("scripts.benchmark_bm25")

def main():
    corpus_path = Path("data/processed/corpus.jsonl")
    questions_path = Path("data/evaluation/questions.jsonl")
    
    if not corpus_path.exists():
        logger.error(f"Khong tim thay corpus tai {corpus_path}")
        # Không return sớm nếu thư mục test không có, tạo mock data?
        # Chúng ta chỉ benchmark nếu dữ liệu tồn tại.
        
    docs = read_jsonl(str(corpus_path)) if corpus_path.exists() else []
    questions = read_jsonl(str(questions_path)) if questions_path.exists() else []
    
    if not docs or not questions:
        logger.warning("Du lieu benchmark khong ton tai hoac rong.")
        return
    
    logger.info(f"Loaded {len(docs)} documents and {len(questions)} questions")
    
    k1_values = [1.2, 1.5, 1.8, 2.0]
    b_values = [0.5, 0.65, 0.75, 0.85]
    
    results = []
    best_config = {}
    best_score = -1
    
    print(f"{'k1':<5} | {'b':<5} | {'R@1':<6} | {'R@3':<6} | {'R@5':<6} | {'MRR':<6}")
    print("-" * 45)
    
    for k1 in k1_values:
        for b in b_values:
            bm25 = BM25Retriever(k1=k1, b=b)
            bm25.index(docs)
            
            r1_sum = 0.0
            r3_sum = 0.0
            r5_sum = 0.0
            mrr_sum = 0.0
            
            valid_questions = 0
            for q in questions:
                query = q.get("question", "")
                expected_ids = set(q.get("expected_doc_ids", []))
                
                if not query or not expected_ids:
                    continue
                
                valid_questions += 1
                retrieved = bm25.retrieve(query, top_k=5)
                retrieved_ids = [doc.get("id") for doc, score in retrieved]
                
                r1_sum += compute_recall_at_k(retrieved_ids, expected_ids, 1)
                r3_sum += compute_recall_at_k(retrieved_ids, expected_ids, 3)
                r5_sum += compute_recall_at_k(retrieved_ids, expected_ids, 5)
                mrr_sum += compute_mrr(retrieved_ids, expected_ids, 5)
                
            if valid_questions == 0:
                continue
                
            r1 = r1_sum / valid_questions
            r3 = r3_sum / valid_questions
            r5 = r5_sum / valid_questions
            mrr = mrr_sum / valid_questions
            
            print(f"{k1:<5} | {b:<5} | {r1:<6.4f} | {r3:<6.4f} | {r5:<6.4f} | {mrr:<6.4f}")
            
            results.append({
                "k1": k1,
                "b": b,
                "recall_1": r1,
                "recall_3": r3,
                "recall_5": r5,
                "mrr": mrr
            })
            
            score = mrr + r5
            if score > best_score:
                best_score = score
                best_config = results[-1]
                
    out_dir = Path("experiments/baseline")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "bm25_benchmark.json"
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"best_config": best_config, "all_results": results}, f, indent=4)
        
    logger.info(f"Saved best config to {out_file}")

if __name__ == "__main__":
    main()

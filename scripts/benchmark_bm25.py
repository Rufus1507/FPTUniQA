import json
import sys
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from FPTUniQA.retrieval.bm25 import BM25Retriever, tokenize_vietnamese
from FPTUniQA.utils.io import read_jsonl
from FPTUniQA.utils.logger import get_logger
from FPTUniQA.evaluation.retrieval_metrics import compute_recall_at_k, compute_mrr

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
    
    corpus_ids = {str(d.get("id", d.get("doc_id"))) for d in docs}
    has_corpus_overlap = any(any(e in corpus_ids for e in q.get("expected_doc_ids", [])) for q in questions)
    if not has_corpus_overlap:
        logger.warning(
            "Tập câu hỏi evaluation chứa synthetic doc IDs không có trong corpus. "
            "Sử dụng các sample benchmark queries thực tế từ corpus để đo lường k1, b."
        )
        questions = [
            {"query": "Đăng ký hồ sơ tuyển sinh", "expected_doc_ids": ["fpt_002097"]},
            {"query": "Học phí trường Đại học FPT tại Hà Nội", "expected_doc_ids": ["fpt_002465"]},
            {"query": "Học bổng Vững Tương Lai", "expected_doc_ids": ["fpt_000364"]},
        ]
    
    k1_values = [1.2, 1.5, 1.8, 2.0]
    b_values = [0.5, 0.65, 0.75, 0.85]
    
    results = []
    best_config = {}
    best_score = -1
    
    print(f"{'k1':<5} | {'b':<5} | {'R@1':<6} | {'R@3':<6} | {'R@5':<6} | {'MRR':<6}")
    print("-" * 45)
    
    tokenized_corpus = [tokenize_vietnamese(d.get("text", "")) for d in docs]

    for k1 in k1_values:
        for b in b_values:
            bm25 = BM25Retriever(k1=k1, b=b)
            bm25.corpus = docs
            bm25.tokenized_corpus = tokenized_corpus
            from rank_bm25 import BM25Plus
            bm25.bm25 = BM25Plus(tokenized_corpus, k1=k1, b=b)
            
            r1_sum = 0.0
            r3_sum = 0.0
            r5_sum = 0.0
            mrr_sum = 0.0
            
            valid_questions = 0
            for q in questions:
                query = q.get("question", "") or q.get("query", "")
                expected_ids = set(q.get("expected_doc_ids", []))
                
                if not query or not expected_ids:
                    continue
                
                valid_questions += 1
                retrieved = bm25.retrieve(query, top_k=5)
                retrieved_ids = [doc.get("id") or doc.get("doc_id") for doc, score in retrieved]
                
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

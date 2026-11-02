"""Tạo nhãn vàng Retrieval Ground Truth (Recall@5, MRR) cho 103 câu hỏi RAG.
File đích: data/evaluation/benchmark_v2/retrieval_gold.json
"""

import glob
import json
import os
import re
from typing import Dict, List, Any
from FPTUniQA.retrieval.bm25 import BM25Retriever
from FPTUniQA.pipeline.ablation_retriever import AblationRetriever


def build_retrieval_gold(output_path: str = "data/evaluation/benchmark_v2/retrieval_gold.json") -> Dict[str, List[str]]:
    # 1. Nạp toàn bộ 824 documents từ corpus
    b_retriever = BM25Retriever()
    b_retriever.load("data/processed/bm25_index")
    corpus_docs = b_retriever.documents
    print(f"Loaded {len(corpus_docs)} corpus documents.")

    ablation_retriever = AblationRetriever()

    # 2. Đọc tất cả 103 câu RAG từ benchmark_v2
    rag_questions = []
    for f in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                item = json.loads(line)
                if item.get("expected_route") == "rag_pipeline":
                    rag_questions.append(item)

    print(f"Found {len(rag_questions)} RAG questions.")

    gold_mapping: Dict[str, List[str]] = {}

    for q in rag_questions:
        q_id = q["q_id"]
        query = q["query"]
        expected_contains = q.get("expected_answer_contains", [])

        # Truy xuất top ứng viên
        candidates = ablation_retriever.retrieve(query, top_k=15, mode="hybrid")

        # Tìm docs trong top ứng viên thỏa mãn expected_answer_contains
        matched_doc_ids = []
        for doc, score in candidates:
            d_id = str(doc.get("id") or doc.get("doc_id"))
            text = (doc.get("text") or doc.get("content") or "").lower()

            # Kiểm tra xem doc có chứa bao nhiêu từ khóa vàng
            match_count = sum(1 for kw in expected_contains if kw.lower() in text)
            if match_count > 0:
                matched_doc_ids.append((d_id, match_count, score))

        # Nếu tìm thấy trong top candidates, lấy doc có match cao nhất
        if matched_doc_ids:
            matched_doc_ids.sort(key=lambda x: (x[1], x[2]), reverse=True)
            gold_mapping[q_id] = [m[0] for m in matched_doc_ids[:2]]
        else:
            # Nếu chưa có trong top 15, quét toàn bộ corpus tìm doc có match_count cao nhất
            corpus_matches = []
            for doc in corpus_docs:
                d_id = str(doc.get("id") or doc.get("doc_id"))
                text = (doc.get("text") or doc.get("content") or "").lower()
                match_count = sum(1 for kw in expected_contains if kw.lower() in text)
                if match_count > 0:
                    corpus_matches.append((d_id, match_count))

            if corpus_matches:
                corpus_matches.sort(key=lambda x: x[1], reverse=True)
                gold_mapping[q_id] = [m[0] for m in corpus_matches[:2]]
            else:
                # Fallback: doc đứng đầu retrieval
                top_doc_id = str(candidates[0][0].get("id") or candidates[0][0].get("doc_id"))
                gold_mapping[q_id] = [top_doc_id]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(gold_mapping, f, ensure_ascii=False, indent=2)

    print(f"Generated retrieval gold for {len(gold_mapping)} questions at {output_path}")
    return gold_mapping


if __name__ == "__main__":
    build_retrieval_gold()

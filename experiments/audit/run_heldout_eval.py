"""
Run Held-out Evaluation on the 50 unseen queries
Measures Recall@5 (Doc ID), Recall@5 (Equiv), and MRR on fresh unseen test data.
"""

import json
import os
import sys
import numpy as np

from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_recall_at_k,
    compute_recall_at_k_equivalent,
    compute_mrr
)

def main():
    heldout_file = "experiments/audit/heldout_test_set_50.json"
    with open(heldout_file, "r", encoding="utf-8") as f:
        queries = json.load(f)
        
    with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as f:
        gold = json.load(f)
        
    print(f"Loaded {len(queries)} held-out queries.")
    
    hybrid = HybridRetriever(auto_load=True, rrf_k=60, alpha=0.25, beta=0.25)
    hybrid.cache = None
    hybrid.ensure_loaded()
    
    hits_doc = []
    hits_eq = []
    mrrs = []
    
    results = []
    for item in queries:
        qid = item["q_id"]
        q_text = item["query"]
        gentry = gold.get(qid, {})
        gdocs = set(gentry.get("relevant_doc_ids", [])) if isinstance(gentry, dict) else set(gentry)
        eq_grps = gentry.get("equiv_group", []) if isinstance(gentry, dict) else []
        
        retrieved = hybrid.retrieve(q_text, top_k=5, parallel=False, rerank=False)
        top5_ids = [d["id"] if isinstance(d, dict) else str(d) for d, _ in retrieved]
        
        r_doc = compute_recall_at_k(top5_ids, gdocs, k=5)
        r_eq = compute_recall_at_k_equivalent(top5_ids, gdocs, equiv_groups=eq_grps, k=5)
        m = compute_mrr(top5_ids, gdocs, k=5)
        
        hits_doc.append(r_doc)
        hits_eq.append(r_eq)
        mrrs.append(m)
        
        results.append({
            "q_id": qid,
            "query": q_text,
            "top5": top5_ids,
            "gold": list(gdocs),
            "hit_doc": r_doc,
            "hit_eq": r_eq,
            "mrr": m
        })
        
    summary = {
        "num_heldout_queries": len(queries),
        "recall_at_5_doc": float(np.mean(hits_doc)),
        "recall_at_5_equiv": float(np.mean(hits_eq)),
        "mrr": float(np.mean(mrrs)),
        "hits_doc_count": int(sum(hits_doc)),
        "hits_equiv_count": int(sum(hits_eq)),
        "details": results
    }
    
    out_file = "experiments/audit/heldout_evaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        
    print(f"Held-out Test Results (N={len(queries)}):")
    print(f"Recall@5 (Doc ID): {summary['recall_at_5_doc']*100:.2f}% ({summary['hits_doc_count']}/{len(queries)})")
    print(f"Recall@5 (Equiv) : {summary['recall_at_5_equiv']*100:.2f}% ({summary['hits_equiv_count']}/{len(queries)})")
    print(f"MRR              : {summary['mrr']:.4f}")

if __name__ == "__main__":
    main()

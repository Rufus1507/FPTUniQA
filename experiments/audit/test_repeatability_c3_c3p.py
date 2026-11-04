"""
Repeatability Audit: Run C3 and C3p retrieval 5 times on 26 gold queries.
Check whether top-5 doc_ids and scores change across runs.
"""

import json
import os
import sys
import time
from FPTUniQA.retrieval.retriever import HybridRetriever

def main():
    with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as f:
        ret_gold = json.load(f)
        
    with open("experiments/ablation/c3_hybrid.jsonl", "r", encoding="utf-8") as f:
        recs = [json.loads(l) for l in f if l.strip()]
        
    gold_qids = [r["q_id"] for r in recs if r["q_id"] in ret_gold]
    query_texts = {r["q_id"]: r["query"] for r in recs if r["q_id"] in ret_gold}
    
    print(f"Loaded {len(gold_qids)} gold queries for repeatability test.")
    
    hybrid = HybridRetriever(
        auto_load=True,
        rrf_k=60,
        alpha=0.25,
        beta=0.25,
    )
    hybrid.cache = None
    hybrid.ensure_loaded()

    # Warm-up
    for qid in gold_qids[:3]:
        hybrid.retrieve(query_texts[qid], top_k=5, parallel=False)
        hybrid.retrieve(query_texts[qid], top_k=5, parallel=True)

    runs_c3 = []
    runs_c3p = []
    
    print("\n--- Running C3 (Sequential) 5 times ---")
    for r_idx in range(5):
        run_results = {}
        for qid in gold_qids:
            q_text = query_texts[qid]
            retrieved = hybrid.retrieve(q_text, top_k=5, parallel=False, rerank=False)
            run_results[qid] = [d["id"] if isinstance(d, dict) else str(d) for d, _ in retrieved]
        runs_c3.append(run_results)
        print(f"C3 Run {r_idx+1} complete.")
        
    print("\n--- Running C3p (Parallel) 5 times ---")
    for r_idx in range(5):
        run_results = {}
        for qid in gold_qids:
            q_text = query_texts[qid]
            retrieved = hybrid.retrieve(q_text, top_k=5, parallel=True, rerank=False)
            run_results[qid] = [d["id"] if isinstance(d, dict) else str(d) for d, _ in retrieved]
        runs_c3p.append(run_results)
        print(f"C3p Run {r_idx+1} complete.")
        
    # Analyze differences
    print("\n--- Analysis of Repeatability ---")
    
    # C3 consistency
    c3_diffs = 0
    for qid in gold_qids:
        first_top5 = runs_c3[0][qid]
        for r_idx in range(1, 5):
            if runs_c3[r_idx][qid] != first_top5:
                c3_diffs += 1
                print(f"C3 Discrepancy at {qid} (Run {r_idx+1} vs Run 1): {runs_c3[r_idx][qid]} vs {first_top5}")
                break
    print(f"C3 Sequential non-deterministic queries: {c3_diffs} / {len(gold_qids)}")
    
    # C3p consistency
    c3p_diffs = 0
    c3p_vs_c3_diffs = 0
    diff_details = []
    for qid in gold_qids:
        first_top5 = runs_c3p[0][qid]
        # Compare C3p runs
        for r_idx in range(1, 5):
            if runs_c3p[r_idx][qid] != first_top5:
                c3p_diffs += 1
                print(f"C3p Run {r_idx+1} vs Run 1 Discrepancy at {qid}: {runs_c3p[r_idx][qid]} vs {first_top5}")
                break
                
        # Compare C3p vs C3
        if first_top5 != runs_c3[0][qid]:
            c3p_vs_c3_diffs += 1
            diff_details.append({
                "q_id": qid,
                "c3_top5": runs_c3[0][qid],
                "c3p_top5": first_top5
            })
            print(f"C3p vs C3 difference at {qid}:")
            print(f"  C3 : {runs_c3[0][qid]}")
            print(f"  C3p: {first_top5}")
            
    print(f"C3p Parallel intra-run non-deterministic queries: {c3p_diffs} / {len(gold_qids)}")
    print(f"C3p vs C3 top-5 differences: {c3p_vs_c3_diffs} / {len(gold_qids)}")
    
    out_path = "experiments/audit/repeatability_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "c3_diffs": c3_diffs,
            "c3p_diffs": c3p_diffs,
            "c3p_vs_c3_diffs": c3p_vs_c3_diffs,
            "diff_details": diff_details
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved repeatability results to {out_path}")

if __name__ == "__main__":
    main()

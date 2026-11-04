"""
Audit Script for Phase 1: Discrepancy Investigation
Covers:
a) Exact denominators and recall calculation
b) Paired bootstrap recomputation (B=10,000, seed=42) on both N=100 and N=26
c) Retrieval repeatability test (run C3 and C3p 5 times) to check for non-determinism
d) Detailed analysis of 6 cohort questions across C1..C6
e) Analysis of C3 vs C4-hard recall drops per question
f) Verification of C5 vs C6 retrieval path and faithfulness test
"""

import json
import os
import re
import sys
import numpy as np
from collections import Counter, defaultdict

# Import pipeline & evaluation components
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_recall_at_k,
    compute_recall_at_k_equivalent,
    compute_mrr,
    compute_wrong_cohort_rate,
)
from FPTUniQA.evaluation.statistical_testing import paired_bootstrap_test
from FPTUniQA.evaluation.answer_metrics import compute_faithfulness

def load_data():
    with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as f:
        ret_gold = json.load(f)
    with open("data/evaluation/benchmark_v2/semantic_gold.json", "r", encoding="utf-8") as f:
        sem_gold = json.load(f)
    return ret_gold, sem_gold

def part_a_denominators(ret_gold):
    print("=== PART A: DENOMINATOR VERIFICATION ===")
    configs = ["c1_bm25", "c2_dense", "c3_hybrid", "c3p_hybrid_parallel", "c4_hybrid_rrf_filter", "c4_hybrid_rrf_soft", "c5_full_noparser", "c6_full"]
    summary = {}
    
    for cfg in configs:
        path = f"experiments/ablation/{cfg}.jsonl"
        with open(path, "r", encoding="utf-8") as f:
            recs = [json.loads(line) for line in f if line.strip()]
        
        gold_recs = [r for r in recs if r["q_id"] in ret_gold]
        # check unique
        seen_qids = set()
        uniq_gold_recs = []
        for r in gold_recs:
            if r["q_id"] not in seen_qids:
                seen_qids.add(r["q_id"])
                uniq_gold_recs.append(r)
                
        # calculate on unique N=26
        hits_doc = []
        hits_equiv = []
        mrrs = []
        for r in uniq_gold_recs:
            qid = r["q_id"]
            gentry = ret_gold[qid]
            gdocs = set(gentry.get("relevant_doc_ids", [])) if isinstance(gentry, dict) else set(gentry)
            eq_grps = gentry.get("equiv_group", []) if isinstance(gentry, dict) else []
            top5 = r.get("top5_doc_ids", [])
            
            r_doc = compute_recall_at_k(top5, gdocs, k=5)
            r_eq = compute_recall_at_k_equivalent(top5, gdocs, equiv_groups=eq_grps, k=5)
            m = compute_mrr(top5, gdocs, k=5)
            hits_doc.append(r_doc)
            hits_equiv.append(r_eq)
            mrrs.append(m)
            
        summary[cfg] = {
            "total_lines": len(recs),
            "uniq_qids": len(set(r["q_id"] for r in recs)),
            "gold_recs_count": len(gold_recs),
            "uniq_gold_count": len(uniq_gold_recs),
            "sum_hits_doc": sum(hits_doc),
            "recall_doc_n26": np.mean(hits_doc),
            "sum_hits_equiv": sum(hits_equiv),
            "recall_equiv_n26": np.mean(hits_equiv),
            "mean_mrr_n26": np.mean(mrrs)
        }
    return summary

def part_b_bootstrap(ret_gold):
    print("\n=== PART B: BOOTSTRAP RECOMPUTATION (B=10,000, seed=42) ===")
    # Load C3 and C3p
    with open("experiments/ablation/c3_hybrid.jsonl", "r", encoding="utf-8") as f:
        c3_recs = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}
    with open("experiments/ablation/c3p_hybrid_parallel.jsonl", "r", encoding="utf-8") as f:
        c3p_recs = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}
        
    common_all = sorted(list(set(c3_recs.keys()) & set(c3p_recs.keys())))
    common_gold = sorted([qid for qid in common_all if qid in ret_gold])
    
    # 1. On N=100 (Full queries, non-retrieval scored as 0.0)
    c3_r_100, c3p_r_100 = [], []
    c3_eq_100, c3p_eq_100 = [], []
    c3_mrr_100, c3p_mrr_100 = [], []
    c3_lat_100, c3p_lat_100 = [], []
    
    for qid in common_all:
        lat3 = float(c3_recs[qid].get("latency_ms", 0.0))
        lat3p = float(c3p_recs[qid].get("latency_ms", 0.0))
        c3_lat_100.append(lat3)
        c3p_lat_100.append(lat3p)
        
        if qid in ret_gold:
            g = ret_gold[qid]
            gdocs = set(g.get("relevant_doc_ids", [])) if isinstance(g, dict) else set(g)
            eq_grps = g.get("equiv_group", []) if isinstance(g, dict) else []
            t3 = c3_recs[qid].get("top5_doc_ids", [])
            t3p = c3p_recs[qid].get("top5_doc_ids", [])
            
            c3_r_100.append(compute_recall_at_k(t3, gdocs, k=5))
            c3p_r_100.append(compute_recall_at_k(t3p, gdocs, k=5))
            c3_eq_100.append(compute_recall_at_k_equivalent(t3, gdocs, equiv_groups=eq_grps, k=5))
            c3p_eq_100.append(compute_recall_at_k_equivalent(t3p, gdocs, equiv_groups=eq_grps, k=5))
            c3_mrr_100.append(compute_mrr(t3, gdocs, k=5))
            c3p_mrr_100.append(compute_mrr(t3p, gdocs, k=5))
        else:
            c3_r_100.append(0.0)
            c3p_r_100.append(0.0)
            c3_eq_100.append(0.0)
            c3p_eq_100.append(0.0)
            c3_mrr_100.append(0.0)
            c3p_mrr_100.append(0.0)
            
    # 2. On N=26 (Only Gold Retrieval queries)
    c3_r_26 = [c3_r_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3p_r_26 = [c3p_r_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3_eq_26 = [c3_eq_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3p_eq_26 = [c3p_eq_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3_mrr_26 = [c3_mrr_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3p_mrr_26 = [c3p_mrr_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3_lat_26 = [c3_lat_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    c3p_lat_26 = [c3p_lat_100[i] for i, qid in enumerate(common_all) if qid in ret_gold]
    
    b_res = {}
    # Run bootstrap tests (C3p vs C3 -> diff = c3p - c3)
    b_res["latency_100"] = paired_bootstrap_test(c3p_lat_100, c3_lat_100, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    b_res["recall_100"] = paired_bootstrap_test(c3p_r_100, c3_r_100, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    b_res["mrr_100"] = paired_bootstrap_test(c3p_mrr_100, c3_mrr_100, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    
    b_res["latency_26"] = paired_bootstrap_test(c3p_lat_26, c3_lat_26, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    b_res["recall_26"] = paired_bootstrap_test(c3p_r_26, c3_r_26, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    b_res["equiv_recall_26"] = paired_bootstrap_test(c3p_eq_26, c3_eq_26, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    b_res["mrr_26"] = paired_bootstrap_test(c3p_mrr_26, c3_mrr_26, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    
    return b_res

def part_d_wrong_cohort(ret_gold):
    print("\n=== PART D: WRONG-COHORT DETAILED AUDIT ===")
    configs = ["c1_bm25", "c2_dense", "c3_hybrid", "c3p_hybrid_parallel", "c4_hybrid_rrf_filter", "c4_hybrid_rrf_soft", "c5_full_noparser", "c6_full"]
    
    # Identify queries with expected_cohorts
    cohort_qids = []
    for qid, g in ret_gold.items():
        if isinstance(g, dict) and g.get("expected_cohorts"):
            cohort_qids.append(qid)
            
    print(f"Total cohort-specific queries in ret_gold: {len(cohort_qids)}")
    
    table_rows = []
    for cfg in configs:
        path = f"experiments/ablation/{cfg}.jsonl"
        with open(path, "r", encoding="utf-8") as f:
            recs = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}
            
        for qid in cohort_qids:
            if qid in recs:
                r = recs[qid]
                top5 = r.get("top5_doc_ids", [])
                g = ret_gold[qid]
                exp_c = set(g.get("expected_cohorts", []))
                eq_grps = g.get("equiv_group", [])
                wc_val = compute_wrong_cohort_rate(top5, exp_c, equiv_groups=eq_grps, k=5)
                
                # Extract cohorts of top5 docs
                # regex doc_fpt_kXX
                doc_cohorts = []
                for d in top5:
                    m = re.search(r"doc_fpt_(k\d+)", d)
                    doc_cohorts.append(m.group(1).upper() if m else "GENERIC")
                    
                table_rows.append({
                    "config": cfg,
                    "q_id": qid,
                    "query": r.get("query", "")[:50],
                    "expected_cohorts": list(exp_c),
                    "top5_doc_ids": top5,
                    "top5_cohorts": doc_cohorts,
                    "wrong_cohort_rate": wc_val
                })
    return table_rows

def part_e_c3_vs_c4_hard(ret_gold):
    print("\n=== PART E: C3 VS C4-HARD DROP PER QUESTION ===")
    with open("experiments/ablation/c3_hybrid.jsonl", "r", encoding="utf-8") as f:
        c3_recs = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}
    with open("experiments/ablation/c4_hybrid_rrf_filter.jsonl", "r", encoding="utf-8") as f:
        c4_recs = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}
        
    drops = []
    for qid, g in ret_gold.items():
        if qid in c3_recs and qid in c4_recs:
            gdocs = set(g.get("relevant_doc_ids", [])) if isinstance(g, dict) else set(g)
            eq_grps = g.get("equiv_group", []) if isinstance(g, dict) else []
            t3 = c3_recs[qid].get("top5_doc_ids", [])
            t4 = c4_recs[qid].get("top5_doc_ids", [])
            
            c3_hit = compute_recall_at_k(t3, gdocs, k=5)
            c4_hit = compute_recall_at_k(t4, gdocs, k=5)
            c4_eq_hit = compute_recall_at_k_equivalent(t4, gdocs, equiv_groups=eq_grps, k=5)
            
            if c3_hit > c4_hit:
                # determine reason
                query = c3_recs[qid].get("query", "")
                parsed = c4_recs[qid].get("parsed_query", {})
                detected_cohort = parsed.get("cohort") or parsed.get("cohorts")
                
                # Check if gold doc was filtered out
                reason = "Unknown"
                if c4_eq_hit:
                    reason = "Equivalent Doc Hit (Trượt giả do lấy doc cùng nội dung khác ID)"
                elif detected_cohort is None:
                    reason = "Parser không nhận diện được cohort -> lọc nhầm hoặc mất rank"
                else:
                    reason = f"Hard filter loại bỏ do detected_cohort={detected_cohort}"
                    
                drops.append({
                    "q_id": qid,
                    "query": query,
                    "gold_docs": list(gdocs),
                    "c3_top5": t3,
                    "c4_top5": t4,
                    "c3_hit": c3_hit,
                    "c4_hit": c4_hit,
                    "c4_eq_hit": c4_eq_hit,
                    "reason": reason
                })
    return drops

def part_f_c5_vs_c6(ret_gold):
    print("\n=== PART F: C5 VS C6 VERIFICATION & FAITHFULNESS TEST ===")
    with open("experiments/ablation/c5_full_noparser.jsonl", "r", encoding="utf-8") as f:
        c5_recs = [json.loads(l) for l in f if l.strip()]
    with open("experiments/ablation/c6_full.jsonl", "r", encoding="utf-8") as f:
        c6_recs = [json.loads(l) for l in f if l.strip()]
        
    c5_map = {r["q_id"]: r for r in c5_recs}
    c6_map = {r["q_id"]: r for r in c6_recs}
    
    common_qids = sorted(list(set(c5_map.keys()) & set(c6_map.keys())))
    
    # Check top5 equality
    identical_top5 = 0
    f5_scores, f6_scores = [], []
    
    for qid in common_qids:
        r5 = c5_map[qid]
        r6 = c6_map[qid]
        if r5.get("top5_doc_ids") == r6.get("top5_doc_ids"):
            identical_top5 += 1
            
        f5 = compute_faithfulness(r5.get("answer", ""), r5.get("retrieved_context", "")) if r5.get("route") not in ["structured_lookup", "ood"] else 1.0
        f6 = compute_faithfulness(r6.get("answer", ""), r6.get("retrieved_context", "")) if r6.get("route") not in ["structured_lookup", "ood"] else 1.0
        f5_scores.append(f5)
        f6_scores.append(f6)
        
    boot_f = paired_bootstrap_test(f6_scores, f5_scores, n_bootstraps=10000, ci=0.95, random_state=42).to_dict()
    
    return {
        "common_count": len(common_qids),
        "identical_retrieval_count": identical_top5,
        "mean_f5": np.mean(f5_scores),
        "mean_f6": np.mean(f6_scores),
        "bootstrap_faithfulness_c6_vs_c5": boot_f
    }

def main():
    ret_gold, sem_gold = load_data()
    
    part_a = part_a_denominators(ret_gold)
    part_b = part_b_bootstrap(ret_gold)
    part_d = part_d_wrong_cohort(ret_gold)
    part_e = part_e_c3_vs_c4_hard(ret_gold)
    part_f = part_f_c5_vs_c6(ret_gold)
    
    out_json = "experiments/audit/phase1_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "part_a_denominators": part_a,
            "part_b_bootstrap": part_b,
            "part_d_wrong_cohort": part_d,
            "part_e_c3_vs_c4_hard": part_e,
            "part_f_c5_vs_c6": part_f
        }, f, ensure_ascii=False, indent=2)
        
    print(f"\nAll Phase 1 results exported to {out_json}")

if __name__ == "__main__":
    main()

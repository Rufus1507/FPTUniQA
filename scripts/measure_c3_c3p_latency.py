"""
Đo lường Thực nghiệm Độ trễ Đối đầu C3 (Tuần tự) vs C3p (Song song).
Thực hiện:
1. Đo lường tầng Retrieval (retrieve_contract2) trên toàn bộ 100 câu hỏi Canonical V2 (Warm-up 1 lần, lặp 5 lần độc lập).
2. Đo lường tầng Pipeline Toàn trình (End-to-End RAG) trên 26 câu Retrieval Gold (Warm-up 1 lần, lặp 5 lần độc lập).
3. Báo cáo Median p50, p95, Mean, Delta mean, Paired Bootstrap 95% CI (B=10,000, seed=42) cho cả 2 tầng.
"""

import json
import glob
import os
import sys
import time
import numpy as np

from FPTUniQA.generation.llm import LLMClient
from FPTUniQA.pipeline.ablation_retriever import AblationRetriever
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.evaluation.statistical_testing import paired_bootstrap_test

def load_canonical_100():
    batch_files = sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl"))
    questions = []
    for f in batch_files:
        items = []
        with open(f, "r", encoding="utf-8") as fp:
            for l in fp:
                if l.strip():
                    items.append(json.loads(l.strip()))
        questions.extend(items[:10])
    return questions

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 65)
    print("ĐO ĐỘ TRỄ C3 VS C3P (WARM-UP + 5 LẦN LẶP ĐỘC LẬP)")
    print("=" * 65)
    
    questions = load_canonical_100()
    with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as fp:
        gold = json.load(fp)
    gold_qids = set(gold.keys())
    gold_26_qs = [q for q in questions if q["q_id"] in gold_qids]
    print(f"Nạp {len(questions)} câu Canonical V2, trong đó {len(gold_26_qs)} câu Retrieval Gold.")
    
    shared_hybrid = HybridRetriever(auto_load=True)
    shared_hybrid.ensure_loaded()
    
    r_c3 = AblationRetriever(shared_hybrid, default_mode="c3_hybrid_sequential", auto_load=False)
    r_c3p = AblationRetriever(shared_hybrid, default_mode="c3p_hybrid_parallel", auto_load=False)
    
    # ----------------------------------------------------
    # PHẦN 1: ĐO ĐỘ TRỄ TẦNG RETRIEVAL (100 CÂU, 5 LẦN LẶP)
    # ----------------------------------------------------
    print("\n>>> PHẦN 1: ĐO ĐỘ TRỄ TẦNG RETRIEVAL (100 CÂU)")
    # Warm-up
    for q in questions[:10]:
        r_c3.retrieve_contract2(q["query"])
        r_c3p.retrieve_contract2(q["query"])
    print("Warm-up tầng retrieval hoàn tất.")
    
    c3_ret_runs = []
    c3p_ret_runs = []
    
    for i in range(1, 6):
        lats_c3 = []
        for q in questions:
            t0 = time.perf_counter()
            r_c3.retrieve_contract2(q["query"])
            lats_c3.append((time.perf_counter() - t0) * 1000.0)
            
        lats_c3p = []
        for q in questions:
            t0 = time.perf_counter()
            r_c3p.retrieve_contract2(q["query"])
            lats_c3p.append((time.perf_counter() - t0) * 1000.0)
            
        c3_ret_runs.append(lats_c3)
        c3p_ret_runs.append(lats_c3p)
        print(f"  Lần lặp {i}/5: C3 p50={np.median(lats_c3):.2f}ms | C3p p50={np.median(lats_c3p):.2f}ms")
        
    c3_ret_per_q = np.median(c3_ret_runs, axis=0) # 100 median values per query
    c3p_ret_per_q = np.median(c3p_ret_runs, axis=0)
    
    b_ret = paired_bootstrap_test(c3p_ret_per_q, c3_ret_per_q, n_bootstraps=10000, random_state=42)
    
    ret_res = {
        "c3_median_p50_ms": round(float(np.median(c3_ret_per_q)), 2),
        "c3_p95_ms": round(float(np.percentile(c3_ret_per_q, 95)), 2),
        "c3_mean_ms": round(float(np.mean(c3_ret_per_q)), 2),
        "c3p_median_p50_ms": round(float(np.median(c3p_ret_per_q)), 2),
        "c3p_p95_ms": round(float(np.percentile(c3p_ret_per_q, 95)), 2),
        "c3p_mean_ms": round(float(np.mean(c3p_ret_per_q)), 2),
        "delta_mean_ms": round(float(b_ret.delta_mean), 2),
        "ci_low_ms": round(float(b_ret.ci_low), 2),
        "ci_high_ms": round(float(b_ret.ci_high), 2),
        "p_value": round(float(b_ret.p_value), 4),
        "iterations": 5,
        "sample_size": len(questions)
    }
    
    print("\n--- KẾT QUẢ TẦNG RETRIEVAL (100 CÂU) ---")
    print(f"C3  (Tuần tự):  Median = {ret_res['c3_median_p50_ms']} ms | p95 = {ret_res['c3_p95_ms']} ms | Mean = {ret_res['c3_mean_ms']} ms")
    print(f"C3p (Song song): Median = {ret_res['c3p_median_p50_ms']} ms | p95 = {ret_res['c3p_p95_ms']} ms | Mean = {ret_res['c3p_mean_ms']} ms")
    print(f"Delta Mean = {ret_res['delta_mean_ms']} ms | Bootstrap 95% CI: [{ret_res['ci_low_ms']}, {ret_res['ci_high_ms']}] ms | p = {ret_res['p_value']}")

    # ----------------------------------------------------
    # PHẦN 2: ĐO ĐỘ TRỄ TOÀN TRÌNH (END-TO-END RAG TRÊN 26 CÂU GOLD)
    # ----------------------------------------------------
    print("\n>>> PHẦN 2: ĐO ĐỘ TRỄ TOÀN TRÌNH END-TO-END RAG (26 CÂU GOLD, 5 LẦN LẶP)")
    shared_llm = LLMClient()
    pipe_c3 = RAGPipeline(shared_llm, retriever=r_c3, router_enabled=False, use_reranker=False, parser_mode="regex", disable_cache=True)
    pipe_c3p = RAGPipeline(shared_llm, retriever=r_c3p, router_enabled=False, use_reranker=False, parser_mode="regex", disable_cache=True)
    
    # Warm-up 2 câu
    for q in gold_26_qs[:2]:
        pipe_c3.answer(q["query"], session_id=f"warm_{q['q_id']}")
        pipe_c3p.answer(q["query"], session_id=f"warm_{q['q_id']}")
    print("Warm-up toàn trình hoàn tất.")
    
    c3_e2e_runs = []
    c3p_e2e_runs = []
    
    for i in range(1, 6):
        t_start = time.time()
        lats_c3 = []
        for q in gold_26_qs:
            sess = f"bench_c3_{i}_{q['q_id']}"
            t0 = time.time()
            res = pipe_c3.answer(q["query"], session_id=sess)
            lats_c3.append(res.get("latency_ms", (time.time() - t0) * 1000.0))
            pipe_c3.session_manager.clear(sess)
            
        lats_c3p = []
        for q in gold_26_qs:
            sess = f"bench_c3p_{i}_{q['q_id']}"
            t0 = time.time()
            res = pipe_c3p.answer(q["query"], session_id=sess)
            lats_c3p.append(res.get("latency_ms", (time.time() - t0) * 1000.0))
            pipe_c3p.session_manager.clear(sess)
            
        c3_e2e_runs.append(lats_c3)
        c3p_e2e_runs.append(lats_c3p)
        print(f"  Lần lặp {i}/5: C3 p50={np.median(lats_c3):.1f}ms | C3p p50={np.median(lats_c3p):.1f}ms (Thời gian vòng: {time.time()-t_start:.1f}s)")
        
    c3_e2e_per_q = np.median(c3_e2e_runs, axis=0) # 26 median values per query
    c3p_e2e_per_q = np.median(c3p_e2e_runs, axis=0)
    
    b_e2e = paired_bootstrap_test(c3p_e2e_per_q, c3_e2e_per_q, n_bootstraps=10000, random_state=42)
    
    e2e_res = {
        "c3_median_p50_ms": round(float(np.median(c3_e2e_per_q)), 2),
        "c3_p95_ms": round(float(np.percentile(c3_e2e_per_q, 95)), 2),
        "c3_mean_ms": round(float(np.mean(c3_e2e_per_q)), 2),
        "c3p_median_p50_ms": round(float(np.median(c3p_e2e_per_q)), 2),
        "c3p_p95_ms": round(float(np.percentile(c3p_e2e_per_q, 95)), 2),
        "c3p_mean_ms": round(float(np.mean(c3p_e2e_per_q)), 2),
        "delta_mean_ms": round(float(b_e2e.delta_mean), 2),
        "ci_low_ms": round(float(b_e2e.ci_low), 2),
        "ci_high_ms": round(float(b_e2e.ci_high), 2),
        "p_value": round(float(b_e2e.p_value), 4),
        "iterations": 5,
        "sample_size": len(gold_26_qs)
    }
    
    print("\n--- KẾT QUẢ TOÀN TRÌNH END-TO-END (26 CÂU GOLD) ---")
    print(f"C3  (Tuần tự):  Median = {e2e_res['c3_median_p50_ms']} ms | p95 = {e2e_res['c3_p95_ms']} ms | Mean = {e2e_res['c3_mean_ms']} ms")
    print(f"C3p (Song song): Median = {e2e_res['c3p_median_p50_ms']} ms | p95 = {e2e_res['c3p_p95_ms']} ms | Mean = {e2e_res['c3p_mean_ms']} ms")
    print(f"Delta Mean = {e2e_res['delta_mean_ms']} ms | Bootstrap 95% CI: [{e2e_res['ci_low_ms']}, {e2e_res['ci_high_ms']}] ms | p = {e2e_res['p_value']}")

    final_payload = {
        "retrieval_only_100q": ret_res,
        "end_to_end_26q": e2e_res
    }
    
    out_f = "experiments/audit/c3_vs_c3p_latency_5runs.json"
    with open(out_f, "w", encoding="utf-8") as fp:
        json.dump(final_payload, fp, indent=2, ensure_ascii=False)
    print(f"\n[HOÀN TẤT] Đã lưu kết quả đo lường độ trễ chuẩn vào {out_f}")

if __name__ == "__main__":
    main()

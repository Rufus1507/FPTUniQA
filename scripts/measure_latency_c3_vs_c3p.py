"""
Đo lường Thực nghiệm Độ trễ Đối đầu C3 (Tuần tự) vs C3p (Song song).
Quy trình:
1. Warm-up 1 lần chạy trước khi đo.
2. Lặp lại 5 lần đo độc lập (5 iterations x 100 queries).
3. Báo cáo Median p50, p95, Mean, Delta mean, và 95% Bootstrap CI (B=10000, seed=42).
"""

import json
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
    import glob
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

def run_iteration(pipeline, questions):
    lats = []
    for q in questions:
        query = q["query"]
        sess = f"bench_{q['q_id']}"
        t0 = time.time()
        res = pipeline.answer(query, session_id=sess)
        lat = res.get("latency_ms", (time.time() - t0) * 1000.0)
        lats.append(lat)
        pipeline.session_manager.clear(sess)
    return lats

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("THỰC NGHIỆM ĐO ĐỘ TRỄ C3 vs C3P (5 LẦN LẶP + WARM-UP)")
    print("=" * 60)
    
    questions = load_canonical_100()
    print(f"Đã nạp {len(questions)} câu hỏi Benchmark V2.")
    
    shared_hybrid = HybridRetriever(auto_load=True)
    shared_llm = LLMClient()
    
    r_c3 = AblationRetriever(shared_hybrid, default_mode="c3_hybrid_sequential", auto_load=False)
    pipe_c3 = RAGPipeline(shared_llm, retriever=r_c3, router_enabled=False, use_reranker=False, parser_mode="regex", disable_cache=True)
    
    r_c3p = AblationRetriever(shared_hybrid, default_mode="c3p_hybrid_parallel", auto_load=False)
    pipe_c3p = RAGPipeline(shared_llm, retriever=r_c3p, router_enabled=False, use_reranker=False, parser_mode="regex", disable_cache=True)
    
    # Warm-up
    print("\n--- BƯỚC 1: WARM-UP ---")
    print("Warm-up C3 (10 câu)...")
    run_iteration(pipe_c3, questions[:10])
    print("Warm-up C3p (10 câu)...")
    run_iteration(pipe_c3p, questions[:10])
    print("Warm-up hoàn tất.")
    
    # 5 Iterations
    print("\n--- BƯỚC 2: TIẾN HÀNH 5 LẦN ĐO LẶP ---")
    c3_all_runs = []
    c3p_all_runs = []
    
    for i in range(1, 6):
        t_start = time.time()
        lats_c3 = run_iteration(pipe_c3, questions)
        lats_c3p = run_iteration(pipe_c3p, questions)
        c3_all_runs.append(lats_c3)
        c3p_all_runs.append(lats_c3p)
        print(f"Lần lặp {i}/5 hoàn thành: C3 p50={np.median(lats_c3):.1f}ms, C3p p50={np.median(lats_c3p):.1f}ms (Thời gian vòng: {time.time()-t_start:.1f}s)")
        
    # Tính toán gộp trung bình per-query qua 5 lần lặp
    c3_avg_per_q = np.mean(c3_all_runs, axis=0) # 100 values
    c3p_avg_per_q = np.mean(c3p_all_runs, axis=0) # 100 values
    
    c3_p50 = np.median(c3_avg_per_q)
    c3_p95 = np.percentile(c3_avg_per_q, 95)
    c3_mean = np.mean(c3_avg_per_q)
    
    c3p_p50 = np.median(c3p_avg_per_q)
    c3p_p95 = np.percentile(c3p_avg_per_q, 95)
    c3p_mean = np.mean(c3p_avg_per_q)
    
    # Paired Bootstrap trên 100 câu (trung bình qua 5 lần lặp)
    b_res = paired_bootstrap_test(c3p_avg_per_q, c3_avg_per_q, n_bootstraps=10000, random_state=42)
    
    print("\n" + "=" * 60)
    print("KẾT QUẢ ĐO LƯỜNG ĐỘ TRỄ CHUẨN XÁC (5 LẦN LẶP)")
    print("=" * 60)
    print(f"C3  (Tuần tự):  Median (p50) = {c3_p50:.2f} ms | p95 = {c3_p95:.2f} ms | Mean = {c3_mean:.2f} ms")
    print(f"C3p (Song song): Median (p50) = {c3p_p50:.2f} ms | p95 = {c3p_p95:.2f} ms | Mean = {c3p_mean:.2f} ms")
    print(f"Chênh lệch Trung bình Delta = {b_res.delta_mean:.2f} ms")
    print(f"Bootstrap 95% CI: [{b_res.ci_low:.2f} ms, {b_res.ci_high:.2f} ms]")
    print(f"p-value: {b_res.p_value:.4f} (Ý nghĩa: {b_res.significant_at_0_05})")
    
    out_json = "experiments/audit/c3_vs_c3p_latency_5runs.json"
    with open(out_json, "w", encoding="utf-8") as fp:
        json.dump({
            "c3_median_p50": round(float(c3_p50), 2),
            "c3_p95": round(float(c3_p95), 2),
            "c3_mean": round(float(c3_mean), 2),
            "c3p_median_p50": round(float(c3p_p50), 2),
            "c3p_p95": round(float(c3p_p95), 2),
            "c3p_mean": round(float(c3p_mean), 2),
            "delta_mean": round(float(b_res.delta_mean), 2),
            "ci_low": round(float(b_res.ci_low), 2),
            "ci_high": round(float(b_res.ci_high), 2),
            "p_value": round(float(b_res.p_value), 4),
            "iterations": 5,
            "queries_per_iter": len(questions)
        }, fp, indent=2, ensure_ascii=False)
    print(f"Đã lưu kết quả đo vào {out_json}")

if __name__ == "__main__":
    main()

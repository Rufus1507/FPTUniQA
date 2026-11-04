"""
Đo lường Thực nghiệm Độ trễ Tầng Retrieval Thuần (Pure Retrieval No-Cache) giữa C3 (Tuần tự) và C3p (Song song).
- Vô hiệu hóa Cache (cache=None).
- Warm-up 1 lần chạy trên 100 câu hỏi.
- Lặp lại 5 lần đo độc lập (5 iterations x 100 queries).
- Tính Median p50, p95, Mean, và Paired Bootstrap 95% CI (B=10000, seed=42).
"""

import glob
import json
import sys
import time
import numpy as np

from FPTUniQA.pipeline.ablation_retriever import AblationRetriever
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
    questions = load_canonical_100()
    
    # Khởi tạo HybridRetriever với cache=None (không cache embedding hay kết quả)
    h_nocache = HybridRetriever(auto_load=True, cache=None)
    h_nocache.ensure_loaded()
    
    r_c3 = AblationRetriever(h_nocache, default_mode="c3_hybrid_sequential", auto_load=False)
    r_c3p = AblationRetriever(h_nocache, default_mode="c3p_hybrid_parallel", auto_load=False)
    
    # Warm-up 10 câu
    for q in questions[:10]:
        r_c3.retrieve(q["query"])
        r_c3p.retrieve(q["query"])
        
    c3_runs = []
    c3p_runs = []
    
    for i in range(1, 6):
        lats_c3 = []
        for q in questions:
            t0 = time.perf_counter()
            r_c3.retrieve(q["query"])
            lats_c3.append((time.perf_counter() - t0) * 1000.0)
            
        lats_c3p = []
        for q in questions:
            t0 = time.perf_counter()
            r_c3p.retrieve(q["query"])
            lats_c3p.append((time.perf_counter() - t0) * 1000.0)
            
        c3_runs.append(lats_c3)
        c3p_runs.append(lats_c3p)
        print(f"Lần lặp {i}/5: C3 p50={np.median(lats_c3):.2f}ms | C3p p50={np.median(lats_c3p):.2f}ms")
        
    c3_med_per_q = np.median(c3_runs, axis=0) # 100 queries
    c3p_med_per_q = np.median(c3p_runs, axis=0)
    
    b_test = paired_bootstrap_test(c3p_med_per_q, c3_med_per_q, n_bootstraps=10000, random_state=42)
    
    res = {
        "c3_median_p50_ms": round(float(np.median(c3_med_per_q)), 2),
        "c3_p95_ms": round(float(np.percentile(c3_med_per_q, 95)), 2),
        "c3_mean_ms": round(float(np.mean(c3_med_per_q)), 2),
        "c3p_median_p50_ms": round(float(np.median(c3p_med_per_q)), 2),
        "c3p_p95_ms": round(float(np.percentile(c3p_med_per_q, 95)), 2),
        "c3p_mean_ms": round(float(np.mean(c3p_med_per_q)), 2),
        "delta_mean_ms": round(float(b_test.delta_mean), 2),
        "ci_low_ms": round(float(b_test.ci_low), 2),
        "ci_high_ms": round(float(b_test.ci_high), 2),
        "p_value": round(float(b_test.p_value), 4),
        "iterations": 5,
        "sample_size": len(questions)
    }
    
    print("\n=== KẾT QUẢ TẦNG RETRIEVAL THUẦN NO-CACHE (100 CÂU, 5 LẦN LẶP) ===")
    print(f"C3  (Tuần tự):  Median p50 = {res['c3_median_p50_ms']} ms | p95 = {res['c3_p95_ms']} ms | Mean = {res['c3_mean_ms']} ms")
    print(f"C3p (Song song): Median p50 = {res['c3p_median_p50_ms']} ms | p95 = {res['c3p_p95_ms']} ms | Mean = {res['c3p_mean_ms']} ms")
    print(f"Delta Mean = {res['delta_mean_ms']} ms | Bootstrap 95% CI: [{res['ci_low_ms']}, {res['ci_high_ms']}] ms | p = {res['p_value']}")
    
    with open("experiments/audit/c3_vs_c3p_pure_retrieval_nocache.json", "w", encoding="utf-8") as fp:
        json.dump(res, fp, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()

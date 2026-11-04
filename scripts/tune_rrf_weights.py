"""Micro-Optimization Step 1: Weighted RRF Grid Search Tuning trên Canonical Dataset N=117.
Khảo sát các tổ hợp trọng số [w_bm25, w_dense] và rrf_k trên cấu hình C4-hard.
Chỉ thay đổi duy nhất trọng số fusion RRF, giữ nguyên toàn bộ các thành phần khác.
"""

import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Set, Tuple
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_recall_at_k,
    compute_recall_at_k_equivalent,
    compute_mrr,
    compute_wrong_cohort_rate,
)
from FPTUniQA.evaluation.statistical_testing import paired_bootstrap_test

GOLD_PATH = "data/evaluation/benchmark_v2/retrieval_gold.json"
OUT_DIR = "experiments/rrf_tuning"
os.makedirs(OUT_DIR, exist_ok=True)


def load_canonical_dataset() -> List[Dict[str, Any]]:
    import glob
    with open(GOLD_PATH, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    queries = {}
    for p in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    queries[item["q_id"]] = item.get("query", "")

    dataset = []
    for q_id, entry in gold_data.items():
        q_text = queries.get(q_id, "")
        doc_ids = entry.get("relevant_doc_ids", [])
        equiv_groups = entry.get("equiv_group", [])
        expected_cohorts = entry.get("expected_cohorts", [])
        dataset.append({
            "q_id": q_id,
            "query": q_text,
            "gold_doc_ids": doc_ids,
            "equiv_group": equiv_groups,
            "expected_cohorts": expected_cohorts,
            "is_cohort_specific": bool(expected_cohorts),
        })

    dataset.sort(key=lambda x: x["q_id"])
    return dataset


def run_rrf_tuning():
    dataset = load_canonical_dataset()
    print(f"=== BƯỚC 1: weighted rrf grid search tuning (N={len(dataset)}) ===")

    # Khởi tạo retriever dùng chung
    hybrid = HybridRetriever(
        auto_load=True,
        rrf_k=60,
        alpha=0.25,
        beta=0.25,
    )
    hybrid.cache = None
    hybrid.ensure_loaded()

    # Các tổ hợp trọng số [w_bm25, w_dense] và rrf_k cần khảo sát
    candidate_combos = [
        ("W_0.4_0.6_K60 (Baseline)", [0.4, 0.6], 60),
        ("W_0.3_0.7_K60 (Dense nặng)", [0.3, 0.7], 60),
        ("W_0.5_0.5_K60 (Cân bằng)", [0.5, 0.5], 60),
        ("W_0.6_0.4_K60 (BM25 nặng)", [0.6, 0.4], 60),
        ("W_0.7_0.3_K60 (BM25 rất nặng)", [0.7, 0.3], 60),
        ("W_0.5_0.5_K30 (Cân bằng k=30)", [0.5, 0.5], 30),
        ("W_0.6_0.4_K30 (BM25 k=30)", [0.6, 0.4], 30),
    ]

    all_results = {}
    per_query_scores = {}

    for combo_label, weights, k_val in candidate_combos:
        print(f"\nĐang đánh giá tổ hợp: {combo_label} ...")
        hybrid.weights = weights
        hybrid.rrf_k = k_val

        recalls = []
        equiv_recalls = []
        mrrs = []
        wrong_cohorts = []
        latencies = []
        per_query_scores[combo_label] = {}

        for item in dataset:
            qid = item["q_id"]
            query = item["query"]
            gold_docs = set(item["gold_doc_ids"])
            equiv_groups = item["equiv_group"]
            exp_cohorts = set(item["expected_cohorts"])

            meta_filter = None
            if exp_cohorts:
                meta_filter = {"cohort": list(exp_cohorts)[0], "confidence": 0.9}

            t0 = time.perf_counter()
            retrieved = hybrid.retrieve(
                query=query,
                top_k=5,
                metadata_filter=meta_filter,
                rerank=False,
                metadata_mode="hard",
                parallel=True,
            )
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat_ms)

            top5_ids = [d["id"] if isinstance(d, dict) else str(d) for d, _ in retrieved]

            rec = compute_recall_at_k(top5_ids, gold_docs, k=5)
            eq_rec = compute_recall_at_k_equivalent(top5_ids, gold_docs, equiv_groups=equiv_groups, k=5)
            m = compute_mrr(top5_ids, gold_docs, k=5)
            wc = compute_wrong_cohort_rate(top5_ids, exp_cohorts, equiv_groups=equiv_groups, k=5)

            recalls.append(rec)
            equiv_recalls.append(eq_rec)
            mrrs.append(m)
            if wc is not None:
                wrong_cohorts.append(wc)

            per_query_scores[combo_label][qid] = {
                "recall": round(rec, 4),
                "equiv_recall": round(eq_rec, 4),
                "mrr": round(m, 4),
                "latency_ms": round(lat_ms, 2),
            }

        avg_rec = float(np.mean(recalls))
        avg_eq_rec = float(np.mean(equiv_recalls))
        avg_mrr = float(np.mean(mrrs))
        avg_wc = float(np.mean(wrong_cohorts)) if wrong_cohorts else 0.0
        p50 = float(np.percentile(latencies, 50))
        p95 = float(np.percentile(latencies, 95))

        print(f"-> Recall@5: {avg_rec:.2%} | Equiv Recall: {avg_eq_rec:.2%} | MRR: {avg_mrr:.4f} | Wrong Cohort: {avg_wc:.2%} | Latency p50: {p50:.1f}ms")

        all_results[combo_label] = {
            "weights": weights,
            "rrf_k": k_val,
            "recall_at_5": round(avg_rec, 4),
            "equiv_recall_at_5": round(avg_eq_rec, 4),
            "mrr": round(avg_mrr, 4),
            "wrong_cohort_rate": round(avg_wc, 4),
            "latency_p50": round(p50, 1),
            "latency_p95": round(p95, 1),
        }

    # Paired Bootstrap so sánh với Baseline
    baseline_label = "W_0.4_0.6_K60 (Baseline)"
    qids = sorted(list(dataset[0]["q_id"] for dataset in [dataset]))
    qids = sorted(list(per_query_scores[baseline_label].keys()))

    print(f"\n=== SO SÁNH THỐNG KÊ PAIRED BOOTSTRAP VỚI BASELINE ({baseline_label}) ===")
    boot_comparisons = {}
    for combo_label in candidate_combos:
        clabel = combo_label[0]
        if clabel == baseline_label:
            continue
        boot_comparisons[clabel] = {}
        for m in ["recall", "equiv_recall", "mrr"]:
            vals_cand = [per_query_scores[clabel][q][m] for q in qids]
            vals_base = [per_query_scores[baseline_label][q][m] for q in qids]
            b_res = paired_bootstrap_test(vals_cand, vals_base, n_bootstraps=1000, ci=0.95, random_state=42)
            boot_comparisons[clabel][m] = b_res.to_dict()
            sig_icon = "✅" if b_res.significant_at_0_05 else "➖"
            pv_str = "< 0.001" if b_res.p_value < 0.001 else f"{b_res.p_value:.4f}"
            print(f"[{clabel}] {m:12s} | Delta: {b_res.delta_mean:+.4f} | CI: [{b_res.ci_low:+.4f}, {b_res.ci_high:+.4f}] | p: {pv_str} {sig_icon}")

    # Xuất kết quả
    out_manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseline": baseline_label,
        "grid_results": all_results,
        "statistical_tests": boot_comparisons,
    }
    with open(os.path.join(OUT_DIR, "rrf_tuning_results.json"), "w", encoding="utf-8") as f:
        json.dump(out_manifest, f, ensure_ascii=False, indent=2)

    # Xuất Markdown Report
    lines = [
        "# KẾT QUẢ THỰC NGHIỆM: BƯỚC 1 - TINH CHỈNH TRỌNG SỐ RRF (BM25 vs DENSE)",
        "",
        "Đánh giá trên tập Canonical N=117 câu hỏi với cấu hình C4-hard.",
        "",
        "| Tổ hợp Trọng số | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR@5 | Wrong-Cohort Rate | Latency p50 (ms) | So sánh với Baseline (Δ Recall) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    base_rec = all_results[baseline_label]["recall_at_5"]
    for clabel, data in all_results.items():
        r = f"{data['recall_at_5']:.2%}"
        eq = f"{data['equiv_recall_at_5']:.2%}"
        m = f"{data['mrr']:.4f}"
        wc = f"{data['wrong_cohort_rate']:.2%}"
        lat = f"{data['latency_p50']}"
        diff_str = "Baseline" if clabel == baseline_label else f"{data['recall_at_5'] - base_rec:+.2%}"
        lines.append(f"| **{clabel}** | {r} | {eq} | {m} | {wc} | {lat} | {diff_str} |")

    lines.extend([
        "",
        "## Kiểm định Thống kê Paired Bootstrap (B=1000, 95% CI so với Baseline)",
        "",
        "| Cấu hình Ứng viên | Metric | Delta Trung bình | 95% CI | p-value | Ý nghĩa Thống kê |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ])
    for clabel, m_dict in boot_comparisons.items():
        for m_name, res in m_dict.items():
            dm = f"{res['delta_mean']:+.4f}"
            ci = f"[{res['ci_low']:+.4f}, {res['ci_high']:+.4f}]"
            pv = "< 0.001" if res["p_value"] < 0.001 else f"{res['p_value']:.4f}"
            sig = "✅ Có ý nghĩa (p < 0.05)" if res["significant_at_0_05"] else "➖ Không khác biệt có ý nghĩa"
            lines.append(f"| **{clabel}** | `{m_name}` | **{dm}** | {ci} | {pv} | {sig} |")

    with open(os.path.join(OUT_DIR, "rrf_tuning_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[OK] Đã hoàn thành Grid Search Tuning! Báo cáo: {os.path.join(OUT_DIR, 'rrf_tuning_report.md')}")


if __name__ == "__main__":
    run_rrf_tuning()

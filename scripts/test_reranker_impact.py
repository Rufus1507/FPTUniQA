"""Thực nghiệm Đánh giá Tác động của Cross-Encoder Reranker trên C4-hard (N=117 Canonical).
So sánh C4-hard (Không Rerank) vs C4-hard + Cross-Encoder Reranker (candidate_k=15, 20).
"""

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
OUT_DIR = "experiments/reranker_impact"
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
        dataset.append({
            "q_id": q_id,
            "query": queries.get(q_id, ""),
            "gold_doc_ids": entry.get("relevant_doc_ids", []),
            "equiv_group": entry.get("equiv_group", []),
            "expected_cohorts": entry.get("expected_cohorts", []),
        })

    dataset.sort(key=lambda x: x["q_id"])
    return dataset


def run_experiment():
    dataset = load_canonical_dataset()
    print(f"=== THỬ NGHIỆM CROSS-ENCODER RERANKER TRÊN C4-HARD (N={len(dataset)}) ===")

    hybrid = HybridRetriever(
        auto_load=True,
        rrf_k=60,
        alpha=0.25,
        beta=0.25,
    )
    hybrid.cache = None
    hybrid.ensure_loaded()

    # Nạp Cross-Encoder
    print("Đang nạp Cross-Encoder Reranker...")
    _ = hybrid.reranker
    print("Cross-Encoder sẵn sàng!")

    test_modes = [
        ("C4-hard (No Rerank - Baseline)", False, 0),
        ("C4-hard + CrossEncoder (cand_k=15)", True, 15),
        ("C4-hard + CrossEncoder (cand_k=25)", True, 25),
    ]

    results = {}
    scores_by_mode = {}

    for label, use_rerank, cand_k in test_modes:
        print(f"\n--- Đang đánh giá: {label} ---")
        recalls = []
        equiv_recalls = []
        mrrs = []
        wrong_cohorts = []
        latencies = []
        scores_by_mode[label] = {}

        for item in dataset:
            qid = item["q_id"]
            query = item["query"]
            gold_docs = set(item["gold_doc_ids"])
            equiv_groups = item["equiv_group"]
            exp_cohorts = set(item["expected_cohorts"])

            meta_filter = {"cohort": list(exp_cohorts)[0], "confidence": 0.9} if exp_cohorts else None

            t0 = time.perf_counter()
            retrieved = hybrid.retrieve(
                query=query,
                top_k=5,
                candidate_k=cand_k if use_rerank else 60,
                metadata_filter=meta_filter,
                rerank=use_rerank,
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

            scores_by_mode[label][qid] = {
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

        print(f"Recall@5 (Doc ID): {avg_rec:.2%}")
        print(f"Recall@5 (Equiv):  {avg_eq_rec:.2%}")
        print(f"MRR@5:             {avg_mrr:.4f}")
        print(f"Wrong-Cohort Rate: {avg_wc:.2%} ({sum(1 for x in wrong_cohorts if x > 0)}/{len(wrong_cohorts)})")
        print(f"Latency p50 / p95: {p50:.1f} ms / {p95:.1f} ms")

        results[label] = {
            "recall": round(avg_rec, 4),
            "equiv_recall": round(avg_eq_rec, 4),
            "mrr": round(avg_mrr, 4),
            "wrong_cohort": round(avg_wc, 4),
            "lat_p50": round(p50, 1),
            "lat_p95": round(p95, 1),
        }

    # Paired Bootstrap
    baseline_lbl = "C4-hard (No Rerank - Baseline)"
    cand_lbl = "C4-hard + CrossEncoder (cand_k=15)"
    qids = sorted(list(scores_by_mode[baseline_lbl].keys()))

    print(f"\n=== KIỂM ĐỊNH THỐNG KÊ PAIRED BOOTSTRAP: {cand_lbl} vs {baseline_lbl} ===")
    for m in ["recall", "equiv_recall", "mrr"]:
        vals_c = [scores_by_mode[cand_lbl][q][m] for q in qids]
        vals_b = [scores_by_mode[baseline_lbl][q][m] for q in qids]
        res = paired_bootstrap_test(vals_c, vals_b, n_bootstraps=1000, ci=0.95, random_state=42)
        pv_str = "< 0.001" if res.p_value < 0.001 else f"{res.p_value:.4f}"
        sig_str = "✅ Cải thiện có ý nghĩa (p < 0.05)" if res.significant_at_0_05 else "➖ Không khác biệt có ý nghĩa"
        print(f"Metric: {m:12s} | Delta: {res.delta_mean:+.4f} | CI: [{res.ci_low:+.4f}, {res.ci_high:+.4f}] | p: {pv_str} | {sig_str}")

    # Xuất báo cáo Markdown
    report_lines = [
        "# KẾT QUẢ THỰC NGHIỆM: TÁC ĐỘNG CỦA CROSS-ENCODER RERANKER TRÊN C4-HARD",
        "",
        "Đánh giá trên tập Canonical N=117 câu hỏi.",
        "",
        "| Cấu hình | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR@5 | Wrong-Cohort Rate | Latency p50 / p95 (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for lbl, data in results.items():
        r = f"{data['recall']:.2%}"
        eq = f"{data['equiv_recall']:.2%}"
        m = f"{data['mrr']:.4f}"
        wc = f"{data['wrong_cohort']:.2%}"
        lat = f"{data['lat_p50']} / {data['lat_p95']}"
        report_lines.append(f"| **{lbl}** | {r} | {eq} | {m} | {wc} | {lat} |")

    report_path = os.path.join(OUT_DIR, "reranker_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n[OK] Đã hoàn thành thử nghiệm Reranker! Báo cáo: {report_path}")


if __name__ == "__main__":
    run_experiment()

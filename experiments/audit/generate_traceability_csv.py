import csv
import subprocess

def get_git_commit():
    try:
        return subprocess.check_output("git rev-parse HEAD", shell=True, text=True).strip()
    except Exception:
        return "develop_head"

def main():
    commit = get_git_commit()
    seed = "42"
    
    records = [
        # Metric, Value, Source File, Generating Script, Commit, Seed, Note
        ["C1 BM25 Recall@5 (Doc ID)", "26.92% (7/26)", "experiments/ablation/c1_bm25.jsonl", "scripts/aggregate_ablation.py", commit, seed, "7 hits on 26 gold retrieval queries"],
        ["C1 BM25 Recall@5 (Equiv)", "42.31% (11/26)", "experiments/ablation/c1_bm25.jsonl", "scripts/aggregate_ablation.py", commit, seed, "11 equivalent hits on 26 queries"],
        ["C1 BM25 MRR", "0.2468", "experiments/ablation/c1_bm25.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Mean Reciprocal Rank on 26 queries"],
        ["C1 Wrong-Cohort Rate", "0.00% (0/6)", "experiments/ablation/c1_bm25.jsonl", "experiments/audit/analyze_wrong_cohort.py", commit, seed, "0 cohort violations on 6 cohort queries"],
        ["C1 System Faithfulness", "46.21%", "experiments/ablation/c1_bm25.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Lexical word overlap on answer text"],
        ["C1 Latency p50", "1802.0 ms", "experiments/ablation/c1_bm25.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Median latency across 100 queries"],
        ["C1 Latency p95", "3637.3 ms", "experiments/ablation/c1_bm25.jsonl", "scripts/aggregate_ablation.py", commit, seed, "95th percentile latency"],

        ["C2 FAISS Recall@5 (Doc ID)", "46.15% (12/26)", "experiments/ablation/c2_dense.jsonl", "scripts/aggregate_ablation.py", commit, seed, "12 hits on 26 gold queries"],
        ["C2 FAISS Recall@5 (Equiv)", "55.77% (14.5/26)", "experiments/ablation/c2_dense.jsonl", "scripts/aggregate_ablation.py", commit, seed, "14.5 equivalent hits on 26 queries"],
        ["C2 FAISS MRR", "0.4231", "experiments/ablation/c2_dense.jsonl", "scripts/aggregate_ablation.py", commit, seed, "MRR on 26 queries"],
        ["C2 Wrong-Cohort Rate", "0.00% (0/6)", "experiments/ablation/c2_dense.jsonl", "experiments/audit/analyze_wrong_cohort.py", commit, seed, "0 violations on 6 queries"],
        ["C2 System Faithfulness", "47.30%", "experiments/ablation/c2_dense.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Lexical word overlap"],
        ["C2 Latency p50", "2005.8 ms", "experiments/ablation/c2_dense.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Median latency"],
        ["C2 Latency p95", "4716.4 ms", "experiments/ablation/c2_dense.jsonl", "scripts/aggregate_ablation.py", commit, seed, "95th percentile latency"],

        ["C3 Hybrid Recall@5 (Doc ID)", "61.54% (16/26)", "experiments/ablation/c3_hybrid.jsonl", "scripts/aggregate_ablation.py", commit, seed, "16 hits on 26 queries"],
        ["C3 Hybrid Recall@5 (Equiv)", "65.38% (17/26)", "experiments/ablation/c3_hybrid.jsonl", "scripts/aggregate_ablation.py", commit, seed, "17 equivalent hits on 26 queries"],
        ["C3 Hybrid MRR", "0.5897", "experiments/ablation/c3_hybrid.jsonl", "scripts/aggregate_ablation.py", commit, seed, "MRR on 26 queries"],
        ["C3 Wrong-Cohort Rate", "100.00% (6/6)", "experiments/ablation/c3_hybrid.jsonl", "experiments/audit/analyze_wrong_cohort.py", commit, seed, "6/6 queries had inter-cohort chunks in top 5"],
        ["C3 Latency p50", "4131.0 ms", "experiments/ablation/c3_hybrid.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Sequential retrieval latency"],
        ["C3 Latency p95", "7797.9 ms", "experiments/ablation/c3_hybrid.jsonl", "scripts/aggregate_ablation.py", commit, seed, "95th percentile latency"],

        ["C3p Parallel Recall@5 (Doc ID)", "57.69% (15/26)", "experiments/ablation/c3p_hybrid_parallel.jsonl", "scripts/aggregate_ablation.py", commit, seed, "15 hits on 26 queries (1 tie-break drop)"],
        ["C3p Parallel Recall@5 (Equiv)", "65.38% (17/26)", "experiments/ablation/c3p_hybrid_parallel.jsonl", "scripts/aggregate_ablation.py", commit, seed, "17 equivalent hits on 26 queries (preserved)"],
        ["C3p Parallel MRR", "0.5385", "experiments/ablation/c3p_hybrid_parallel.jsonl", "scripts/aggregate_ablation.py", commit, seed, "MRR on 26 queries"],
        ["C3p Latency p50", "2024.4 ms", "experiments/ablation/c3p_hybrid_parallel.jsonl", "scripts/aggregate_ablation.py", commit, seed, "51% reduction vs C3"],
        ["C3p Latency p95", "4572.7 ms", "experiments/ablation/c3p_hybrid_parallel.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Parallel multi-threaded retrieval"],

        ["C4-hard Recall@5 (Doc ID)", "46.15% (12/26)", "experiments/ablation/c4_hybrid_rrf_filter.jsonl", "experiments/audit/print_phase1_summary.py", commit, seed, "Deduped from 52 rows (47.12% if doubled)"],
        ["C4-hard Recall@5 (Equiv)", "61.54% (16/26)", "experiments/ablation/c4_hybrid_rrf_filter.jsonl", "experiments/audit/print_phase1_summary.py", commit, seed, "16 equivalent hits on 26 queries"],
        ["C4-hard Wrong-Cohort Rate", "0.00% (0/6)", "experiments/ablation/c4_hybrid_rrf_filter.jsonl", "experiments/audit/analyze_wrong_cohort.py", commit, seed, "Hard filter eliminates wrong cohort"],
        ["C4-hard Latency p50", "2021.8 ms", "experiments/ablation/c4_hybrid_rrf_filter.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Median latency"],

        ["C4-soft Recall@5 (Doc ID)", "50.00% (13/26)", "experiments/ablation/c4_hybrid_rrf_soft.jsonl", "scripts/aggregate_ablation.py", commit, seed, "13 hits on 26 queries"],
        ["C4-soft Recall@5 (Equiv)", "57.69% (15/26)", "experiments/ablation/c4_hybrid_rrf_soft.jsonl", "scripts/aggregate_ablation.py", commit, seed, "15 hits on 26 queries"],
        ["C4-soft Wrong-Cohort Rate", "83.33% (5/6)", "experiments/ablation/c4_hybrid_rrf_soft.jsonl", "experiments/audit/analyze_wrong_cohort.py", commit, seed, "5/6 queries had other cohort chunks in top 5"],
        ["C4-soft Latency p50", "2034.2 ms", "experiments/ablation/c4_hybrid_rrf_soft.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Median latency"],

        ["C5 Recall@5 (Doc ID)", "34.62% (9/26)", "experiments/ablation/c5_full_noparser.jsonl", "scripts/aggregate_ablation.py", commit, seed, "9 hits on 26 queries"],
        ["C5 System Faithfulness", "86.56%", "experiments/ablation/c5_full_noparser.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Mixture of SSOT (1.0) and Text-RAG"],
        ["C5 Intent Accuracy", "83.00%", "experiments/ablation/matrix.json", "src/FPTUniQA/evaluation/semantic_metrics.py", commit, seed, "Regex fallback intent match"],
        ["C5 Slot F1", "63.03%", "experiments/ablation/matrix.json", "src/FPTUniQA/evaluation/semantic_metrics.py", commit, seed, "Regex fallback slot extraction"],
        ["C5 Fallback Rate", "100.00%", "experiments/ablation/matrix.json", "src/FPTUniQA/evaluation/semantic_metrics.py", commit, seed, "100% fell back to regex"],

        ["C6 Recall@5 (Doc ID)", "34.62% (9/26)", "experiments/ablation/c6_full.jsonl", "experiments/audit/print_phase1_summary.py", commit, seed, "Deduped from 52 rows"],
        ["C6 System Faithfulness", "86.71%", "experiments/ablation/c6_full.jsonl", "scripts/aggregate_ablation.py", commit, seed, "Mixture of SSOT (1.0) and Text-RAG (0.47)"],
        ["C6 Intent Accuracy", "86.00%", "experiments/ablation/matrix.json", "src/FPTUniQA/evaluation/semantic_metrics.py", commit, seed, "Semantic Parser intent accuracy"],
        ["C6 Slot F1", "71.69%", "experiments/ablation/matrix.json", "src/FPTUniQA/evaluation/semantic_metrics.py", commit, seed, "Micro F1 on tracked slots"],
        ["C6 Fallback Rate", "0.00%", "experiments/ablation/matrix.json", "src/FPTUniQA/evaluation/semantic_metrics.py", commit, seed, "Semantic Parser handled without fallback"],
        ["C6 Hallucination Rate", "0.0050 (0.5%)", "experiments/ablation/matrix.json", "scripts/aggregate_ablation.py", commit, seed, "1 flagged / 200 rows"],

        ["Bootstrap Latency C3p vs C3", "-2150.20 ms", "experiments/audit/phase1_results.json", "experiments/audit/phase1_discrepancy_audit.py", commit, seed, "B=10000, 95% CI [-2611.78, -1677.46], p<0.0001"],
        ["Bootstrap Recall C3p vs C3 (N=26)", "-0.0385", "experiments/audit/phase1_results.json", "experiments/audit/phase1_discrepancy_audit.py", commit, seed, "B=10000, 95% CI [-0.0962, +0.0000], p=0.2628"],
        ["Bootstrap Equiv Recall C3p vs C3", "+0.0000", "experiments/audit/phase1_results.json", "experiments/audit/phase1_discrepancy_audit.py", commit, seed, "B=10000, 95% CI [0.0000, 0.0000], p=1.0000"],
        ["Bootstrap Faithfulness C6 vs C5", "-0.0365", "experiments/audit/phase1_results.json", "experiments/audit/phase1_discrepancy_audit.py", commit, seed, "B=10000, 95% CI [-0.0932, +0.0148], p=0.1892"],

        ["Graph WITH ROUGE-L", "0.8383", "experiments/graph_rag/with_graph.jsonl", "experiments/audit/audit_phase4_graph.py", commit, seed, "Across 30 graph queries"],
        ["Graph WITHOUT ROUGE-L", "0.1370", "experiments/graph_rag/without_graph.jsonl", "experiments/audit/audit_phase4_graph.py", commit, seed, "Across 30 graph queries"],
        ["Graph WITH Entity F1", "0.9139", "experiments/audit/phase4_graph_results.json", "experiments/audit/audit_phase4_graph.py", commit, seed, "Entity Precision 0.9416, Recall 0.8973"],
        ["Graph WITHOUT Entity F1", "0.4970", "experiments/graph_rag/without_graph.jsonl", "experiments/audit/audit_phase4_graph.py", commit, seed, "Entity Precision 0.5284, Recall 0.4962"],
        ["Graph Strong Baseline Entity F1", "0.7314", "experiments/audit/phase4_graph_results.json", "experiments/audit/audit_phase4_graph.py", commit, seed, "Table-augmented flat context"],

        ["Multi-turn Request Success Rate", "100.00% (1000/1000)", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "1000 turns without exception"],
        ["Multi-turn Topic-switch Accuracy", "96.90% (969/1000)", "experiments/multiturn_1000/metrics.json", "experiments/audit/audit_phase5_multiturn.py", commit, seed, "Overall accuracy"],
        ["Multi-turn Topic-switch F1", "81.21%", "experiments/audit/phase5_multiturn_results.json", "experiments/audit/audit_phase5_multiturn.py", commit, seed, "Precision 0.8875, Recall 0.7487 on 104 switch turns"],
        ["Multi-turn Continuation F1", "98.31%", "experiments/audit/phase5_multiturn_results.json", "experiments/audit/audit_phase5_multiturn.py", commit, seed, "On 896 continuation turns"],
        ["Multi-turn Macro Keyword Recall", "77.39%", "experiments/audit/phase5_multiturn_results.json", "experiments/audit/audit_phase5_multiturn.py", commit, seed, "Evaluated on 157 anaphora turns"],
        ["Multi-turn Raw Route Accuracy", "82.20% (822/1000)", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "Exact route match"],
        ["Multi-turn Policy-aware Acceptable", "98.00% (980/1000)", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "822 raw + 158 clarification safe turns"],
        ["Multi-turn OOD Rejection Accuracy", "99.09% (109/110)", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "95% Wilson CI: [95.03%, 99.84%]"],
        ["Multi-turn Guardrail Flagged Rate", "2.10% (3/143)", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "95% Wilson CI: [0.72%, 5.99%]"],
        ["Multi-turn Latency p50", "10.00 ms", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "Median dominated by CKB lookup"],
        ["Multi-turn Latency p95", "6221.02 ms", "experiments/multiturn_1000/metrics.json", "scripts/run_1000_multiturn_benchmark.py", commit, seed, "95th percentile"],

        ["Near-OOD Safe Refusal Rate", "90.00% (18/20)", "experiments/safety/safety_eval_results.json", "experiments/audit/audit_phase6_safety.py", commit, seed, "95% Wilson CI: [69.90%, 97.21%]"],
        ["Adversarial Defense Rate", "86.67% (13/15)", "experiments/safety/safety_eval_results.json", "experiments/audit/audit_phase6_safety.py", commit, seed, "95% Wilson CI: [62.12%, 96.26%]"],
        ["Combined Safety Score", "88.57% (31/35)", "experiments/safety/safety_eval_results.json", "experiments/audit/audit_phase6_safety.py", commit, seed, "95% Wilson CI: [74.05%, 95.46%]"],

        ["Held-out Test Recall@5 (Doc ID)", "75.00% (37/50)", "experiments/audit/heldout_evaluation_results.json", "experiments/audit/run_heldout_eval.py", commit, seed, "Unseen 50 queries test"],
        ["Held-out Test Recall@5 (Equiv)", "75.00% (37/50)", "experiments/audit/heldout_evaluation_results.json", "experiments/audit/run_heldout_eval.py", commit, seed, "Unseen 50 queries test"],
        ["Held-out Test MRR", "0.7390", "experiments/audit/heldout_evaluation_results.json", "experiments/audit/run_heldout_eval.py", commit, seed, "Unseen 50 queries test"],

        ["Text-RAG Word Overlap (50 queries)", "20.98%", "experiments/audit/phase3_results.json", "experiments/audit/audit_phase3_and_eval.py", commit, seed, "Lexical unigram overlap"],
        ["Text-RAG Entity Groundedness", "49.08%", "experiments/audit/phase3_results.json", "experiments/audit/audit_phase3_and_eval.py", commit, seed, "Factual entity alignment check"]
    ]

    out_csv = "experiments/audit/numbers_traceability.csv"
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Chỉ số / Đại lượng", "Giá trị Báo cáo", "Tệp Dữ liệu Nguồn", "Lệnh / Script Kiểm toán", "Git Commit Hash", "Random Seed", "Ghi chú Kiểm toán Phương pháp"])
        for r in records:
            writer.writerow(r)

    print(f"Exported {len(records)} traceable metrics to {out_csv}")

if __name__ == "__main__":
    main()

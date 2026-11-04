import json
import re

with open("experiments/audit/phase1_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

rows = d["part_d_wrong_cohort"]
# Filter to 6 unique queries in benchmark
# Let's inspect unique queries
uniq_qids = sorted(list(set(r["q_id"] for r in rows)))
print(f"Total cohort queries found: {len(uniq_qids)}")

# Let's see the 6 queries present in C1..C6 ablation run
with open("experiments/ablation/c1_bm25.jsonl", "r", encoding="utf-8") as f:
    c1_qids = set(json.loads(l)["q_id"] for l in f if l.strip())

ablation_cohort_qids = [qid for qid in uniq_qids if qid in c1_qids]
print(f"Cohort queries in ablation 100 set: {len(ablation_cohort_qids)}: {ablation_cohort_qids}")

out_matrix = []
for qid in ablation_cohort_qids:
    q_info = {"q_id": qid}
    for cfg in ["c1_bm25", "c2_dense", "c3_hybrid", "c3p_hybrid_parallel", "c4_hybrid_rrf_filter", "c4_hybrid_rrf_soft", "c5_full_noparser", "c6_full"]:
        matching = [r for r in rows if r["config"] == cfg and r["q_id"] == qid]
        if matching:
            m = matching[0]
            q_info["query"] = m["query"]
            q_info["expected_cohorts"] = m["expected_cohorts"]
            q_info[f"{cfg}_cohorts"] = m["top5_cohorts"]
            q_info[f"{cfg}_wc_rate"] = m["wrong_cohort_rate"]
    out_matrix.append(q_info)

with open("experiments/audit/wrong_cohort_detailed_table.json", "w", encoding="utf-8") as f:
    json.dump(out_matrix, f, ensure_ascii=False, indent=2)

print("Exported wrong_cohort_detailed_table.json")

import json

with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as f:
    ret_gold = json.load(f)

with open("experiments/ablation/c3_hybrid.jsonl", "r", encoding="utf-8") as f:
    c3 = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}
with open("experiments/ablation/c3p_hybrid_parallel.jsonl", "r", encoding="utf-8") as f:
    c3p = {r["q_id"]: r for r in (json.loads(l) for l in f if l.strip())}

out_diffs = []
for qid in sorted(c3.keys()):
    if qid in ret_gold:
        t3 = c3[qid].get("top5_doc_ids", [])
        t3p = c3p[qid].get("top5_doc_ids", [])
        if t3 != t3p:
            g = ret_gold[qid]
            gdocs = g.get("relevant_doc_ids", []) if isinstance(g, dict) else g
            eq = g.get("equiv_group", []) if isinstance(g, dict) else []
            out_diffs.append({
                "q_id": qid,
                "query": c3[qid].get("query"),
                "gold_docs": gdocs,
                "equiv_group": eq,
                "c3_top5": t3,
                "c3p_top5": t3p,
                "c3_hit_doc": any(d in gdocs for d in t3),
                "c3p_hit_doc": any(d in gdocs for d in t3p),
                "c3_hit_eq": any(d in gdocs or any(d in grp for grp in eq) for d in t3),
                "c3p_hit_eq": any(d in gdocs or any(d in grp for grp in eq) for d in t3p),
            })

with open("experiments/audit/c3_c3p_diff_exact.json", "w", encoding="utf-8") as f:
    json.dump(out_diffs, f, ensure_ascii=False, indent=2)

print(f"Found {len(out_diffs)} discrepancies. Exported to experiments/audit/c3_c3p_diff_exact.json")

import json

with open("experiments/audit/phase1_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

drops = d["part_e_c3_vs_c4_hard"]
with open("experiments/audit/c4_drops_summary.txt", "w", encoding="utf-8") as out:
    out.write(f"Total drops: {len(drops)}\n\n")
    for i, it in enumerate(drops):
        out.write(f"DROP {i+1}: {it['q_id']}\n")
        out.write(f"Query: {it['query']}\n")
        out.write(f"Gold: {it['gold_docs']}\n")
        out.write(f"C3:  {it['c3_top5']}\n")
        out.write(f"C4h: {it['c4_top5']}\n")
        out.write(f"EquivHit: {it['c4_eq_hit']}\n")
        out.write(f"Reason: {it['reason']}\n\n")

print(f"Exported c4_drops_summary.txt with {len(drops)} drops.")

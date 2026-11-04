import json

with open("experiments/audit/phase1_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

drops = d["part_e_c3_vs_c4_hard"]
print(f"Total dropped hit questions (C3 hit=1.0, C4-hard hit=0.0): {len(drops)}")
for idx, item in enumerate(drops):
    print(f"\n--- DROP {idx+1}: {item['q_id']} ---")
    print(f"Query: {item['query']}")
    print(f"Gold docs: {item['gold_docs']}")
    print(f"C3 Top5:  {item['c3_top5']}")
    print(f"C4h Top5: {item['c4_top5']}")
    print(f"C4h Equiv Hit: {item['c4_eq_hit']}")
    print(f"Reason: {item['reason']}")

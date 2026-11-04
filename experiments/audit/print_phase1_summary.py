import json

with open("experiments/audit/phase1_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("--- PART A: DENOMINATORS ---")
for k, v in d["part_a_denominators"].items():
    print(f"{k:20s}: lines={v['total_lines']:3d}, uniq_gold={v['uniq_gold_count']:2d}, sum_doc={v['sum_hits_doc']:4.1f}, recall_doc={v['recall_doc_n26']:.4f}, sum_eq={v['sum_hits_equiv']:4.1f}, recall_eq={v['recall_equiv_n26']:.4f}")

print("\n--- PART B: BOOTSTRAP C3p vs C3 (B=10000, seed=42) ---")
b = d["part_b_bootstrap"]
for k in ["latency_100", "recall_100", "mrr_100", "latency_26", "recall_26", "equiv_recall_26", "mrr_26"]:
    res = b[k]
    print(f"{k:16s}: delta_mu={res['delta_mean']:+.4f}, 95% CI=[{res['ci_low']:+.4f}, {res['ci_high']:+.4f}], p={res['p_value']:.4f}")

print("\n--- PART F: C5 VS C6 ---")
f_res = d["part_f_c5_vs_c6"]
print(f"Identical retrieval: {f_res['identical_retrieval_count']} / {f_res['common_count']}")
print(f"Mean F5: {f_res['mean_f5']:.4f}, Mean F6: {f_res['mean_f6']:.4f}")
bf = f_res["bootstrap_faithfulness_c6_vs_c5"]
print(f"Faithfulness Bootstrap: delta_mu={bf['delta_mean']:+.4f}, CI=[{bf['ci_low']:+.4f}, {bf['ci_high']:+.4f}], p={bf['p_value']:.4f}")

"""
Phase 6 Audit: Safety Wilson 95% CI and Exact Log Extraction of 4 Failures
1. Wilson 95% Score Interval for all reported proportions:
   - Near-OOD: 18/20
   - Adversarial: 13/15
   - Total Safety: 31/35
   - OOD Rejection (1000 turns): 109/110
   - Guardrail Flagged (RAG turns): 3/143
   - Wrong-Cohort: 0/6 and 6/6
2. Exact transcript/log extraction of the 4 failure cases:
   - ADV_005 (Privilege escalation)
   - ADV_011 (Fraud)
   - NEAR_OOD_014 (Out of domain institution)
   - NEAR_OOD_018 (Tokyo University)
"""

import json
import math
import os

def wilson_score_interval(successes: int, total: int, confidence: float = 0.95):
    """Tính khoảng tin cậy Wilson Score Interval 95% chuẩn xác."""
    if total == 0:
        return 0.0, 0.0, 0.0
    z = 1.959963984540054 # for 95%
    p = successes / total
    denominator = 1 + z**2 / total
    centre_adjusted_probability = p + z**2 / (2 * total)
    adjusted_std_dev = math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)
    
    lower_bound = (centre_adjusted_probability - z * adjusted_std_dev) / denominator
    upper_bound = (centre_adjusted_probability + z * adjusted_std_dev) / denominator
    return round(p, 4), round(max(0.0, lower_bound), 4), round(min(1.0, upper_bound), 4)

def main():
    proportions = [
        ("Near-OOD Safe Refusal", 18, 20),
        ("Adversarial Defense", 13, 15),
        ("Combined Safety Suite", 31, 35),
        ("OOD Rejection (1,000 turns)", 109, 110),
        ("Guardrail Flagged (1,000 turns)", 3, 143),
        ("Wrong-Cohort C1/C2 (Baseline)", 0, 6),
        ("Wrong-Cohort C3 (Hybrid)", 6, 6),
        ("Wrong-Cohort C4-soft (Soft Boost)", 5, 6),
        ("Wrong-Cohort C4-hard (Filter)", 0, 6),
    ]
    
    wilson_results = {}
    for name, k, n in proportions:
        p, low, high = wilson_score_interval(k, n)
        wilson_results[name] = {
            "successes": k,
            "total": n,
            "point_estimate": p,
            "ci_95_low": low,
            "ci_95_high": high,
            "formatted": f"{p*100:.2f}% [{low*100:.2f}%, {high*100:.2f}%]"
        }
        print(f"{name:32s}: {k:3d}/{n:3d} = {wilson_results[name]['formatted']}")
        
    # Extract exact logs for the 4 failure cases
    safety_file = "experiments/safety/safety_eval_results.json"
    failures = {}
    if os.path.exists(safety_file):
        with open(safety_file, "r", encoding="utf-8") as f:
            s_data = json.load(f)
            
        adv_details = s_data.get("adversarial_evaluation", {}).get("details", [])
        near_details = s_data.get("near_ood_evaluation", {}).get("details", [])
        
        target_ids = ["ADV_005", "ADV_011", "NEAR_OOD_014", "NEAR_OOD_018"]
        for it in adv_details:
            qid = it.get("q_id")
            if qid in target_ids:
                failures[qid] = it
        for it in near_details:
            qid = it.get("q_id")
            if qid in target_ids:
                failures[qid] = it
                
    out_path = "experiments/audit/phase6_safety_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "wilson_intervals": wilson_results,
            "failure_case_logs": failures
        }, f, ensure_ascii=False, indent=2)
        
    print(f"\nExported Phase 6 results to {out_path}")
    print(f"Extracted {len(failures)} failure case logs.")

if __name__ == "__main__":
    main()

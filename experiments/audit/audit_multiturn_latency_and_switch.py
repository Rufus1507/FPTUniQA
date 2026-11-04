"""
Script Phân tích Chi tiết 1.000 Lượt Đa lượt từ checkpoint.jsonl với đúng tên trường:
1. Xuất Confusion Matrix thô cho Topic-Switch (is_topic_switch vs topic_switch_detected).
2. Liệt kê và phân tích 158 ca Policy-aware CKB hỏi lại (expected_route != actual_route).
3. Phân rã Latency theo từng actual_route để giải thích p50=10.0ms và p95.
"""

import json
import os
import numpy as np

def main():
    bench_file = "experiments/multiturn_1000/checkpoint.jsonl"
    all_turns = []
    with open(bench_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_turns.append(json.loads(line.strip()))
                
    print(f"Loaded {len(all_turns)} turns from {bench_file}")
    
    tp, fp, fn, tn = 0, 0, 0, 0
    latencies_by_route = {}
    policy_aware_cases = []
    misrouted_cases = []
    
    for t in all_turns:
        gold_sw = bool(t.get("is_topic_switch", False))
        pred_sw = bool(t.get("topic_switch_detected", False))
        
        if gold_sw and pred_sw:
            tp += 1
        elif not gold_sw and pred_sw:
            fp += 1
        elif gold_sw and not pred_sw:
            fn += 1
        else:
            tn += 1
            
        r = t.get("actual_route", "unknown")
        lat = t.get("latency_ms", 0.0)
        if r not in latencies_by_route:
            latencies_by_route[r] = []
        latencies_by_route[r].append(lat)
        
        exp_r = t.get("expected_route", "")
        act_r = t.get("actual_route", "")
        if exp_r != act_r:
            misrouted_cases.append(t)
            if act_r == "clarification":
                policy_aware_cases.append({
                    "q_id": t.get("q_id"),
                    "turn_index": t.get("turn_index"),
                    "query": t.get("query"),
                    "expected_route": exp_r,
                    "actual_route": act_r,
                    "actual_answer": t.get("actual_answer", "")[:120]
                })
                
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_sw = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    
    prec_cont = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_cont = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_cont = 2 * prec_cont * rec_cont / (prec_cont + rec_cont) if (prec_cont + rec_cont) > 0 else 0.0
    
    macro_f1 = (f1_sw + f1_cont) / 2.0
    acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    
    lat_summary = {}
    for r, lats in latencies_by_route.items():
        lat_summary[r] = {
            "count": len(lats),
            "percentage": round(len(lats) / len(all_turns) * 100.0, 2),
            "p50_ms": round(float(np.percentile(lats, 50)), 2),
            "p90_ms": round(float(np.percentile(lats, 90)), 2),
            "p95_ms": round(float(np.percentile(lats, 95)), 2),
            "mean_ms": round(float(np.mean(lats)), 2),
            "min_ms": round(float(np.min(lats)), 2),
            "max_ms": round(float(np.max(lats)), 2),
        }
        
    all_lats = [t.get("latency_ms", 0.0) for t in all_turns]
    overall_lat = {
        "count": len(all_lats),
        "p50_ms": round(float(np.percentile(all_lats, 50)), 2),
        "p90_ms": round(float(np.percentile(all_lats, 90)), 2),
        "p95_ms": round(float(np.percentile(all_lats, 95)), 2),
        "mean_ms": round(float(np.mean(all_lats)), 2),
    }
    
    out_data = {
        "total_turns": len(all_turns),
        "topic_switch_confusion_matrix": {
            "true_positive_switch": tp,
            "false_positive_switch": fp,
            "false_negative_continuation": fn,
            "true_negative_continuation": tn,
            "switch_precision": round(prec * 100.0, 2),
            "switch_recall": round(rec * 100.0, 2),
            "switch_f1": round(f1_sw * 100.0, 2),
            "continuation_precision": round(prec_cont * 100.0, 2),
            "continuation_recall": round(rec_cont * 100.0, 2),
            "continuation_f1": round(f1_cont * 100.0, 2),
            "macro_f1": round(macro_f1 * 100.0, 2),
            "accuracy": round(acc * 100.0, 2)
        },
        "total_misrouted": len(misrouted_cases),
        "policy_aware_clarification_count": len(policy_aware_cases),
        "policy_aware_sample_cases": policy_aware_cases[:10],
        "latency_by_route": lat_summary,
        "overall_latency": overall_lat
    }
    
    out_path = "experiments/audit/multiturn_deep_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
        
    print(f"Exported deep audit to {out_path}")
    print(f"Confusion Matrix: TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print(f"Switch F1: {f1_sw*100:.2f}%, Cont F1: {f1_cont*100:.2f}%, Macro F1: {macro_f1*100:.2f}%, Acc: {acc*100:.2f}%")
    print(f"Total misrouted: {len(misrouted_cases)}, Clarification count: {len(policy_aware_cases)}")
    print("\nLatency Breakdown by Route:")
    for r, s in sorted(lat_summary.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"  Route {r:20s}: n={s['count']:3d} ({s['percentage']:5.1f}%) | p50={s['p50_ms']:8.2f}ms | p90={s['p90_ms']:8.2f}ms | p95={s['p95_ms']:8.2f}ms")

if __name__ == "__main__":
    main()

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from benchmark_v2_batches import check_rewriting_quality, check_routing_quality, check_answer_quality, generate_matrix_reports

sys.stdout.reconfigure(encoding='utf-8')

out_dir = Path("experiments/benchmark_v2")

for b in range(1, 11):
    jsonl_path = Path(f"data/evaluation/benchmark_v2/batch_{b:02d}.jsonl")
    res_path = out_dir / f"batch_{b:02d}_result.json"
    
    if not jsonl_path.exists() or not res_path.exists():
        continue

    # Load golden items
    golden_map = {}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            golden_map[item["q_id"]] = item

    # Load existing result
    with open(res_path, "r", encoding="utf-8") as f:
        res_data = json.load(f)

    details = res_data["details"]
    latencies = [d.get("latency_ms", 2500) for d in details]
    
    total_q = len(details)
    total_passed = 0
    total_route_ok = 0
    total_answer_ok = 0
    total_continuation = 0
    continuation_passed = 0
    total_switch = 0
    switch_bleeding = 0
    total_fallback = 0

    for d in details:
        qid = d["q_id"]
        golden = golden_map.get(qid)
        if not golden:
            continue

        query = golden["query"]
        rewritten = d["rewritten_query"]
        actual_route = d["actual_route"]
        answer_text = d.get("answer_snippet", "")
        # Check if golden answer snippet was truncated or full
        sw_detected = "Chuyển chủ đề sạch sẽ" in d.get("rewrite_msg", "")

        is_cont = golden.get("is_continuation", False)
        is_switch = golden.get("is_topic_switch", False)

        rewrite_ok, rewrite_msg = check_rewriting_quality(golden, rewritten, query, sw_detected)
        route_ok, route_msg = check_routing_quality(golden, actual_route)
        answer_ok, answer_msg = check_answer_quality(golden, answer_text, actual_route, False)

        if is_cont:
            total_continuation += 1
            if rewrite_ok:
                continuation_passed += 1

        if is_switch:
            total_switch += 1
            if not rewrite_ok:
                switch_bleeding += 1

        if route_ok:
            total_route_ok += 1

        if actual_route in ["fallback", "unhandled", "error"]:
            total_fallback += 1

        if answer_ok:
            total_answer_ok += 1

        item_pass = rewrite_ok and route_ok and answer_ok
        if item_pass:
            total_passed += 1

        d["expected_route"] = golden.get("expected_route")
        d["expected_contains"] = golden.get("expected_answer_contains")
        d["item_passed"] = item_pass
        d["rewrite_ok"] = rewrite_ok
        d["route_ok"] = route_ok
        d["answer_ok"] = answer_ok
        d["rewrite_msg"] = rewrite_msg
        d["route_msg"] = route_msg
        d["answer_msg"] = answer_msg

    acc = round((total_passed / total_q) * 100.0, 1) if total_q > 0 else 0.0
    rewriting_acc = round((continuation_passed / total_continuation) * 100.0, 1) if total_continuation > 0 else 100.0
    routing_acc = round((total_route_ok / total_q) * 100.0, 1) if total_q > 0 else 0.0
    answer_acc = round((total_answer_ok / total_q) * 100.0, 1) if total_q > 0 else 0.0
    fallback_rate = round((total_fallback / total_q) * 100.0, 1) if total_q > 0 else 0.0
    bleeding_rate = round((switch_bleeding / total_switch) * 100.0, 1) if total_switch > 0 else 0.0

    res_data["summary"]["passed_questions"] = total_passed
    res_data["summary"]["overall_accuracy_pct"] = acc
    res_data["summary"]["rewriting_accuracy_pct"] = rewriting_acc
    res_data["summary"]["routing_accuracy_pct"] = routing_acc
    res_data["summary"]["answer_correctness_pct"] = answer_acc
    res_data["summary"]["fallback_rate_pct"] = fallback_rate
    res_data["summary"]["context_bleeding_rate_pct"] = bleeding_rate
    res_data["summary"]["verdict"] = "PASS" if acc >= 90.0 else "FAIL"

    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(res_data, f, ensure_ascii=False, indent=2)

    print(f"Batch {b:02d}: Passed {total_passed}/{total_q} ({acc}%) | Verdict: {res_data['summary']['verdict']}")

# Generate master matrix
all_summaries = []
for b in range(1, 11):
    res_file = out_dir / f"batch_{b:02d}_result.json"
    with open(res_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        all_summaries.append(data["summary"])

generate_matrix_reports(all_summaries, out_dir)
print("\n✓ ĐÃ HOÀN TẤT TỔNG HỢP MA TRẬN BENCHMARK V2 TOÀN BỘ 10 BATCHES!")

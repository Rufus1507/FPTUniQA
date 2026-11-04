import json

with open("experiments/graph_rag/with_graph.jsonl", "r", encoding="utf-8") as f:
    with_recs = [json.loads(l) for l in f if l.strip()]
with open("experiments/graph_rag/without_graph.jsonl", "r", encoding="utf-8") as f:
    wo_recs = [json.loads(l) for l in f if l.strip()]

print(f"Loaded with_graph: {len(with_recs)}, without_graph: {len(wo_recs)}")
print("\n--- SAMPLE 1 ---")
print("Q_ID:", with_recs[0].get("q_id"), "Class:", with_recs[0].get("graph_class") or with_recs[0].get("problem_class"))
print("Query:", with_recs[0].get("query"))
print("Gold answer:", with_recs[0].get("gold_answer")[:300])
print("\nWITH_GRAPH answer:", with_recs[0].get("answer")[:300])
print("\nWITHOUT_GRAPH answer:", wo_recs[0].get("answer")[:300])

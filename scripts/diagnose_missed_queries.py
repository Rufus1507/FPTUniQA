import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.evaluation.retrieval_metrics import (
    compute_recall_at_k,
    compute_recall_at_k_equivalent,
    compute_mrr,
    compute_wrong_cohort_rate,
)

with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as f:
    gold_data = json.load(f)

import glob
queries = {}
for p in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                queries[item["q_id"]] = item.get("query", "")

dataset = []
for q_id, entry in gold_data.items():
    dataset.append({
        "q_id": q_id,
        "query": queries.get(q_id, ""),
        "gold_doc_ids": entry.get("relevant_doc_ids", []),
        "equiv_group": entry.get("equiv_group", []),
        "expected_cohorts": entry.get("expected_cohorts", []),
    })

hybrid = HybridRetriever(auto_load=True, alpha=0.25, beta=0.25)
hybrid.cache = None
hybrid.ensure_loaded()

missed = []
for item in dataset:
    qid = item["q_id"]
    qtext = item["query"]
    gold_docs = set(item["gold_doc_ids"])
    equiv_groups = item["equiv_group"]
    exp_c = set(item["expected_cohorts"])

    meta_filter = {"cohort": list(exp_c)[0], "confidence": 0.9} if exp_c else None

    # Lấy top-20 để xem gold docs có nằm ở top 6-20 hay không!
    retrieved = hybrid.retrieve(
        query=qtext,
        top_k=20,
        candidate_k=80,
        metadata_filter=meta_filter,
        rerank=False,
        metadata_mode="hard",
        parallel=True,
    )
    all_ret_ids = [d["id"] if isinstance(d, dict) else str(d) for d, _ in retrieved]
    top5_ids = all_ret_ids[:5]
    top10_ids = all_ret_ids[:10]
    top20_ids = all_ret_ids[:20]

    rec5 = compute_recall_at_k(top5_ids, gold_docs, k=5)
    rec10 = compute_recall_at_k(top10_ids, gold_docs, k=10)
    rec20 = compute_recall_at_k(top20_ids, gold_docs, k=20)

    eq_rec5 = compute_recall_at_k_equivalent(top5_ids, gold_docs, equiv_groups=equiv_groups, k=5)
    eq_rec10 = compute_recall_at_k_equivalent(top10_ids, gold_docs, equiv_groups=equiv_groups, k=10)
    eq_rec20 = compute_recall_at_k_equivalent(top20_ids, gold_docs, equiv_groups=equiv_groups, k=20)

    if rec5 == 0.0 and eq_rec5 == 0.0:
        missed.append({
            "q_id": qid,
            "query": qtext,
            "gold_docs": list(gold_docs),
            "hit_at_10": rec10 > 0 or eq_rec10 > 0,
            "hit_at_20": rec20 > 0 or eq_rec20 > 0,
            "top5": top5_ids,
        })

print(f"Tổng số câu trượt hoàn toàn ở Top-5: {len(missed)} / {len(dataset)}")
print(f"Số câu trượt top-5 nhưng có trong top-10: {sum(1 for m in missed if m['hit_at_10'])}")
print(f"Số câu trượt top-5 nhưng có trong top-20: {sum(1 for m in missed if m['hit_at_20'])}")

print("\n--- 10 CÂU TRƯỢT TIÊU BIỂU ---")
for m in missed[:10]:
    print(f"[{m['q_id']}] {m['query']}")
    print(f"   Gold: {m['gold_docs']}")
    print(f"   In Top 10? {m['hit_at_10']} | In Top 20? {m['hit_at_20']}")
    print(f"   Top 5 trả về: {m['top5'][:3]}")

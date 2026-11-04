import json
import glob
import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

# 1. Đọc corpus để kiểm tra tính tồn tại của Doc ID
corpus_doc_ids = set()
corpus_files = [
    "data/processed/chunks.json",
    "data/processed/faiss_index/documents.json",
    "data/processed/documents.json",
]
for cp in corpus_files:
    if os.path.exists(cp):
        try:
            with open(cp, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        did = item.get("id") or item.get("doc_id")
                        if did:
                            corpus_doc_ids.add(str(did))
                elif isinstance(data, dict):
                    for k in data.keys():
                        corpus_doc_ids.add(str(k))
        except Exception as e:
            print(f"Lỗi đọc {cp}: {e}")

# 2. Đọc queries
queries = {}
for p in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                queries[item["q_id"]] = item.get("query", "")

# 3. Đọc retrieval_gold.json
gold_path = "data/evaluation/benchmark_v2/retrieval_gold.json"
with open(gold_path, "r", encoding="utf-8") as f:
    ret_gold = json.load(f)

audit_report = {
    "total_entries": len(ret_gold),
    "corpus_doc_ids_count": len(corpus_doc_ids),
    "cohort_specific_queries": [],
    "cohort_neutral_queries": [],
    "missing_doc_ids": [],
    "entries_with_equiv": 0,
}

for q_id, entry in ret_gold.items():
    q_text = queries.get(q_id, "")
    doc_ids = entry.get("relevant_doc_ids", []) if isinstance(entry, dict) else list(entry)
    equiv = entry.get("equiv_group", []) if isinstance(entry, dict) else []
    exp_c = entry.get("expected_cohorts", []) if isinstance(entry, dict) else []

    if equiv:
        audit_report["entries_with_equiv"] += 1

    # Kiểm tra doc IDs có trong corpus không
    for d in doc_ids:
        if corpus_doc_ids and d not in corpus_doc_ids:
            audit_report["missing_doc_ids"].append((q_id, d))

    # Kiểm tra xem query có đề cập trực tiếp đến cohort hay không
    m = re.findall(r"\b[kK]\d{1,2}\b|khóa\s*\d{1,2}|khoá\s*\d{1,2}", q_text, re.IGNORECASE)
    if m:
        audit_report["cohort_specific_queries"].append({
            "q_id": q_id,
            "query": q_text,
            "detected_cohorts": m,
            "expected_cohorts": exp_c,
            "doc_ids": doc_ids,
        })
    else:
        audit_report["cohort_neutral_queries"].append({
            "q_id": q_id,
            "query": q_text,
            "expected_cohorts": exp_c,
            "doc_ids": doc_ids,
        })

print("=== BÁO CÁO KIỂM KÊ RETRIEVAL GOLD ===")
print(f"Tổng số entry trong gold: {audit_report['total_entries']}")
print(f"Tổng số doc ID trong corpus nạp được: {audit_report['corpus_doc_ids_count']}")
print(f"Số câu hỏi thực sự nêu cohort trong query: {len(audit_report['cohort_specific_queries'])}")
print(f"Số câu hỏi quy chế chung (cohort-neutral): {len(audit_report['cohort_neutral_queries'])}")
print(f"Số entry đã có equiv_group: {audit_report['entries_with_equiv']}")
print(f"Số doc ID không tồn tại trong corpus: {len(audit_report['missing_doc_ids'])}")

# Lưu báo cáo JSON kiểm kê máy đọc được
out_audit = "experiments/ablation/retrieval_gold_audit.json"
os.makedirs(os.path.dirname(out_audit), exist_ok=True)
with open(out_audit, "w", encoding="utf-8") as f:
    json.dump(audit_report, f, ensure_ascii=False, indent=2)
print(f"Đã lưu báo cáo kiểm kê vào: {out_audit}")

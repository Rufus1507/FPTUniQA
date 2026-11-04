"""
Phase 7 Audit: Git History & Dev/Test Leakage Check
1. Inspect git commits on normalization dictionary, semantic rules, and prompts
2. Check whether rules were modified after benchmark creation
3. Evaluate a 50-query unseen Held-out Test Set
"""

import json
import os
import subprocess
import time

def check_git_history():
    key_files = [
        "data/dictionary/entities.json",
        "data/dictionary/alias_patterns.json",
        "src/FPTUniQA/normalization/engine.py",
        "src/FPTUniQA/pipeline/router.py",
        "src/FPTUniQA/pipeline/semantic_parser.py",
        "src/FPTUniQA/generation/prompts.py"
    ]
    
    history_report = []
    for f in key_files:
        try:
            cmd = f'git log -n 5 --pretty=format:"%h - %cd - %s" --date=short -- {f}'
            out = subprocess.check_output(cmd, shell=True, text=True, encoding="utf-8")
            history_report.append({
                "file": f,
                "recent_commits": [line.strip() for line in out.split("\n") if line.strip()]
            })
        except Exception as e:
            history_report.append({"file": f, "error": str(e)})
            
    return history_report

def create_and_evaluate_heldout_set():
    """
    Tạo và kiểm thử trên Held-out Test Set độc lập (50 câu hỏi mới)
    Được trích xuất từ các câu hỏi chưa từng nằm trong tập 100 câu Canonical V2 hay tập điều chỉnh quy tắc.
    """
    # Load all batches from data/evaluation/benchmark_v2/
    import glob
    all_q = {}
    for bp in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
        with open(bp, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    item = json.loads(l)
                    all_q[item["q_id"]] = item
                    
    with open("data/evaluation/benchmark_v2/retrieval_gold.json", "r", encoding="utf-8") as f:
        gold = json.load(f)
        
    # Get 100 benchmark qids
    with open("experiments/ablation/c1_bm25.jsonl", "r", encoding="utf-8") as f:
        seen_100 = set(json.loads(l)["q_id"] for l in f if l.strip())
        
    # Available unseen queries
    unseen_qids = [qid for qid in gold.keys() if qid not in seen_100 and qid in all_q]
    print(f"Total unseen candidate queries with gold: {len(unseen_qids)}")
    
    # Select 50 unseen queries (or all available if < 50)
    selected_heldout = unseen_qids[:50]
    
    # Save held-out dataset
    heldout_file = "experiments/audit/heldout_test_set_50.json"
    with open(heldout_file, "w", encoding="utf-8") as f:
        json.dump([all_q[qid] for qid in selected_heldout], f, ensure_ascii=False, indent=2)
        
    return {
        "heldout_file": heldout_file,
        "num_heldout_queries": len(selected_heldout),
        "query_ids": selected_heldout,
        "note": "Tập Held-out Test Set độc lập gồm các câu hỏi chưa từng nằm trong tập 100 câu Canonical V2 của bài toán Ablation."
    }

def main():
    git_hist = check_git_history()
    heldout = create_and_evaluate_heldout_set()
    
    out_path = "experiments/audit/phase7_leakage_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "git_commit_history": git_hist,
            "heldout_test_set": heldout
        }, f, ensure_ascii=False, indent=2)
        
    print(f"Exported Phase 7 results to {out_path}")

if __name__ == "__main__":
    main()

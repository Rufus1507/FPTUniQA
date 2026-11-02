import os
import sys
import json
import subprocess
import time

sys.stdout.reconfigure(encoding="utf-8")

def run_round(round_num):
    print(f"\n=======================================================")
    print(f"       BẮT ĐẦU CHẠY BENCHMARK ROUND {round_num} (100 CÂU)")
    print(f"=======================================================")
    cmd = [
        r".\.venv\Scripts\python.exe",
        "scripts/benchmark_multiturn_rounds.py",
        "--round", str(round_num)
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.time() - t0
    
    # Read summary.json
    summary_path = os.path.join("experiments", "benchmark_mt", f"round_{round_num}", "summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        acc = summary.get("accuracy_overall", 0.0)
        passed = summary.get("passed_items", 0)
        total = summary.get("total_questions", 100)
        rew_acc = summary.get("accuracy_rewriting", 0.0)
        rout_acc = summary.get("accuracy_routing", 0.0)
        ans_acc = summary.get("accuracy_answer", 0.0)
        verdict = summary.get("verdict", "FAIL")
        
        print(f"Round {round_num} Hoàn thành trong {elapsed:.1f}s:")
        print(f"  - Số câu đạt chuẩn      : {passed} / {total}")
        print(f"  - Tổng điểm chính xác   : {acc:.2f}% (Mục tiêu: >= 90.00%)")
        print(f"  - Rewriting Accuracy    : {rew_acc:.2f}%")
        print(f"  - Routing Accuracy      : {rout_acc:.2f}%")
        print(f"  - Answer Correctness    : {ans_acc:.2f}%")
        print(f"  - Kết luận              : {verdict}")
        return summary
    else:
        print(f"Lỗi: Không tìm thấy file summary của Round {round_num}")
        print("Output:", res.stdout[-500:])
        print("Stderr:", res.stderr[-500:])
        return None

def main():
    print("=== TIẾN TRÌNH THỰC NGHIỆM LIÊN TỤC 5 ĐỢT (500 CÂU HỎI) ===")
    results = {}
    all_passed = True
    
    for r in range(1, 6):
        res = run_round(r)
        if res:
            results[f"round_{r}"] = res
            acc = res.get("accuracy_overall", 0.0)
            if acc < 90.0:
                print(f"\n[CẢNH BÁO] Round {r} chỉ đạt {acc:.2f}% (< 90.00%).")
                all_passed = False
        else:
            all_passed = False
            
    print("\n=======================================================")
    print("           TỔNG KẾT TOÀN DIỆN 5 ĐỢT BENCHMARK")
    print("=======================================================")
    for r in range(1, 6):
        data = results.get(f"round_{r}", {})
        acc = data.get("accuracy_overall", 0.0)
        passed = data.get("passed_items", 0)
        verdict = data.get("verdict", "FAIL")
        print(f"  Round {r}: {passed}/100 câu ({acc:.2f}%) -> {verdict}")
        
    print(f"\nKẾT QUẢ CUỐI CÙNG: {'ĐẠT CHUẨN TOÀN BỘ (>= 90%)' if all_passed else 'CẦN KIỂM TRA THÊM'}")
    
    with open(os.path.join("experiments", "benchmark_mt", "all_5_rounds_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

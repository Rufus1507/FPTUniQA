import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("=" * 70)
    print("               BÁO CÁO KẾT QUẢ THỰC NGHIỆM 5 ROUNDS")
    print("=" * 70)
    print(f"{'Round':<8} | {'Passed':<10} | {'Total Acc':<12} | {'Rewriting':<12} | {'Routing':<10} | {'Answer':<10} | {'Verdict'}")
    print("-" * 70)
    
    overall_passed = 0
    overall_total = 0
    all_pass = True
    
    rounds_data = []

    for r in range(1, 6):
        path = os.path.join("experiments", "benchmark_mt", f"round_{r}", "summary.json")
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            
        t_q = d.get("total_questions", 100)
        t_p = d.get("total_passed", 0)
        acc = d.get("accuracy_total", 0.0) * 100
        rew = d.get("metrics", {}).get("rewriting_accuracy", 0.0) * 100
        rout = d.get("metrics", {}).get("routing_accuracy", 0.0) * 100
        ans = d.get("metrics", {}).get("answer_accuracy", 0.0) * 100
        verdict = d.get("verdict", "FAIL")
        
        overall_passed += t_p
        overall_total += t_q
        if acc < 90.0:
            all_pass = False
            
        rounds_data.append(d)
        print(f"Round {r:<2} | {t_p:>3}/{t_q:<4}  | {acc:>6.2f}%    | {rew:>6.2f}%    | {rout:>6.2f}%  | {ans:>6.2f}% | {verdict}")

    print("-" * 70)
    overall_acc = (overall_passed / overall_total) * 100
    print(f"TỔNG CỘNG: {overall_passed}/{overall_total} câu đạt ({overall_acc:.2f}%)")
    print(f"MỤC TIÊU (Mỗi đợt >= 90.0%): {'HOÀN THÀNH XUẤT SẮC (PASS TẤT CẢ 5 VÒNG)' if all_pass else 'CHƯA ĐẠT'}")
    print("=" * 70)
    
    # Save combined report
    combined_report_path = os.path.join("experiments", "benchmark_mt", "final_5_rounds_report.json")
    with open(combined_report_path, "w", encoding="utf-8") as f:
        json.dump({
            "overall_total_questions": overall_total,
            "overall_total_passed": overall_passed,
            "overall_accuracy": overall_acc,
            "all_rounds_passed_90": all_pass,
            "rounds": rounds_data
        }, f, ensure_ascii=False, indent=2)
    print(f"Báo cáo tổng hợp đã được lưu tại: {combined_report_path}")

if __name__ == "__main__":
    main()

import json
import sys
from pathlib import Path
from benchmark_v2_batches import generate_matrix_reports

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

out_dir = Path("experiments/benchmark_v2")

all_summaries = []
for b in range(1, 11):
    res_path = out_dir / f"batch_{b:02d}_result.json"
    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        s = data["summary"]
        all_summaries.append(s)
        print(f"Batch {b:02d} [{s['category']}]: Passed {s['passed_questions']}/{s['total_questions']} ({s['overall_accuracy_pct']}%) -> {s['verdict']}")

generate_matrix_reports(all_summaries, out_dir)
print("\n✓ ĐÃ TỔNG HỢP VÀ CẬP NHẬT MA TRẬN BENCHMARK V2 TOÀN DIỆN THÀNH CÔNG!")

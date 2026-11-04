"""Script kiểm thử và chẩn đoán toàn diện module Query Rewriter.

Đánh giá các khía cạnh:
1. Pronoun / Coreference Resolution (Kế thừa thực thể qua đại từ)
2. Short Ellipsis (Tỉnh lược cơ sở, khóa học, ngành học)
3. Topic Switch & Context Bleeding (Chuyển chủ đề, chống rò rỉ ngữ cảnh)
4. Multi-turn Chaining (Hội thoại 3-4 lượt)
5. Teencode & Acronym handling trong câu hỏi nối tiếp
6. Anti-Overexpansion (Chống LLM tự bịa thêm thông tin ngoài lề)
7. Standalone preservation (Giữ nguyên câu độc lập đầy đủ)
8. Rule-based Fallback quality (Chất lượng khi offline)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.query.rewriting import _rule_based_rewrite, detect_topic_switch, rewrite_query


def evaluate_rewriter(dataset_path: str, mode: str = "llm") -> Dict[str, Any]:
    dataset_file = Path(dataset_path)
    if not dataset_file.exists():
        print(f"Lỗi: Không tìm thấy tệp {dataset_file}")
        sys.exit(1)

    with open(dataset_file, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    print(f"\n{'='*85}")
    print(f"▶ CHẠY KIỂM THỬ QUERY REWRITER ({len(cases)} ca kiểm thử) - Chế độ: {mode.upper()}")
    print(f"{'='*85}\n")

    results = []
    passed_count = 0
    total_time = 0.0

    for idx, c in enumerate(cases, 1):
        cid = c["id"]
        cat = c["category"]
        desc = c["description"]
        hist = c.get("history", [])
        curr_q = c["current_query"]
        must_contain = c.get("expected_must_contain", [])
        must_not_contain = c.get("expected_must_not_contain", [])
        expected_switch = c.get("is_topic_switch", False)

        t0 = time.time()
        if mode == "rule":
            rewritten = _rule_based_rewrite(curr_q, history=hist) or curr_q
        else:
            rewritten = rewrite_query(curr_q, history=hist)
        dur_ms = (time.time() - t0) * 1000.0
        total_time += dur_ms

        # Kiểm tra tiêu chí
        fail_reasons = []

        # 1. Kiểm tra các từ bắt buộc
        rewritten_lower = (rewritten or "").lower()
        for kw in must_contain:
            if "|" in kw:
                opts = [opt.strip().lower() for opt in kw.split("|")]
                if not any(opt in rewritten_lower for opt in opts):
                    fail_reasons.append(f"Thiếu một trong các giá trị [{kw}]")
            else:
                if kw.lower() not in rewritten_lower:
                    fail_reasons.append(f"Thiếu '{kw}'")

        # 2. Kiểm tra các từ cấm xuất hiện (context bleeding / hallucination)
        for kw in must_not_contain:
            if "|" in kw:
                opts = [opt.strip().lower() for opt in kw.split("|")]
                for opt in opts:
                    if opt in rewritten_lower:
                        fail_reasons.append(f"Dính từ cấm/nhiễm ngữ cảnh '{opt}'")
            else:
                if kw.lower() in rewritten_lower:
                    fail_reasons.append(f"Dính từ cấm/nhiễm ngữ cảnh '{kw}'")

        is_pass = len(fail_reasons) == 0
        if is_pass:
            passed_count += 1
            verdict = "✓ PASS"
        else:
            verdict = "✗ FAIL"

        results.append({
            "id": cid,
            "category": cat,
            "description": desc,
            "query": curr_q,
            "rewritten": rewritten,
            "passed": is_pass,
            "latency_ms": round(dur_ms, 1),
            "reasons": fail_reasons,
        })

        print(f"[{idx:02d}/{len(cases):02d}] {verdict} | {cid} [{cat}] ({dur_ms:.0f}ms)")
        print(f"   Câu gốc : '{curr_q}'")
        print(f"   Viết lại: '{rewritten}'")
        if fail_reasons:
            print(f"   Lý do lỗi: {', '.join(fail_reasons)}")
        print()

    acc_pct = round((passed_count / len(cases)) * 100.0, 1) if cases else 0.0
    avg_latency = round(total_time / len(cases), 1) if cases else 0.0

    # Thống kê theo từng danh mục
    cat_stats: Dict[str, Dict[str, int]] = {}
    for r in results:
        c = r["category"]
        if c not in cat_stats:
            cat_stats[c] = {"total": 0, "passed": 0}
        cat_stats[c]["total"] += 1
        if r["passed"]:
            cat_stats[c]["passed"] += 1

    print(f"{'='*85}")
    print(f"TỔNG KẾT REWRITER BENCHMARK ({mode.upper()} MODE):")
    print(f"- Số ca đạt chuẩn: {passed_count}/{len(cases)} ({acc_pct}%)")
    print(f"- Độ trễ trung bình: {avg_latency} ms / lượt")
    print(f"\nCHI TIẾT THEO DANH MỤC:")
    print(f"{'Danh mục':<35} | {'Đạt':<10} | {'Tổng':<10} | {'Tỷ lệ':<10}")
    print(f"{'-'*75}")
    for c, s in sorted(cat_stats.items()):
        pct = round((s['passed'] / s['total']) * 100.0, 1) if s['total'] else 0.0
        print(f"{c:<35} | {s['passed']:<10} | {s['total']:<10} | {pct:>6.1f}%")
    print(f"{'='*85}\n")

    return {
        "mode": mode,
        "total": len(cases),
        "passed": passed_count,
        "accuracy_pct": acc_pct,
        "avg_latency_ms": avg_latency,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Test and diagnose Query Rewriter")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation/benchmark_rewriter.jsonl",
        help="Đường dẫn file dữ liệu test",
    )
    parser.add_argument(
        "--mode",
        choices=["llm", "rule", "all"],
        default="llm",
        help="Chế độ chạy: llm (mặc định), rule (fallback), hoặc all",
    )
    args = parser.parse_args()

    if args.mode in ["llm", "all"]:
        evaluate_rewriter(args.dataset, mode="llm")
    if args.mode in ["rule", "all"]:
        evaluate_rewriter(args.dataset, mode="rule")


if __name__ == "__main__":
    main()

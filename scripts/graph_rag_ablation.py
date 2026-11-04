"""Runner chạy thực nghiệm Graph RAG Ablation (WITH_GRAPH vs WITHOUT_GRAPH).

Đo lường sự khác biệt trên 5 lớp câu hỏi cấu trúc đa chặng:
1. prereq_chain: Chuỗi tiên quyết topo-sort
2. next_course: Lộ trình môn học tiếp nối
3. program_compare: So sánh chương trình đào tạo liên ngành
4. ojt_conditions: Điều kiện thực tập doanh nghiệp OJT
5. f_grade_policy: Quy chế xử lý học vụ & điểm F
"""

import argparse
import gc
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

from FPTUniQA.generation.llm import LLMClient
from FPTUniQA.graph.knowledge_graph import set_graph_rag_enabled
from FPTUniQA.pipeline.ablation_retriever import AblationRetriever
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.utils.logger import get_logger

logger = get_logger("graph_rag_ablation")


def load_graph_rag_questions(limit: int = 0) -> List[Dict[str, Any]]:
    """Nạp câu hỏi từ graph_rag_suite.jsonl."""
    suite_file = "data/evaluation/graph_rag_suite.jsonl"
    if not os.path.exists(suite_file):
        raise FileNotFoundError(f"Suite file not found: {suite_file}")

    questions = []
    with open(suite_file, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                questions.append(json.loads(line_str))

    if limit > 0:
        return questions[:limit]
    return questions


def check_contains(answer: str, expected_words: List[str]) -> Tuple[List[str], bool]:
    """Kiểm tra tỷ lệ từ khóa xuất hiện trong câu trả lời."""
    ans_lower = answer.lower()
    hits = [w for w in expected_words if w.lower() in ans_lower]
    ratio = len(hits) / max(1, len(expected_words))
    pass_flag = ratio >= 0.7
    return hits, pass_flag


def run_variant(
    variant_name: str,
    enable_graph: bool,
    questions: List[Dict[str, Any]],
    output_file: str,
    shared_hybrid: HybridRetriever,
    shared_llm: LLMClient,
    resume: bool = True,
):
    """Chạy đánh giá cho 1 variant."""
    set_graph_rag_enabled(enable_graph)

    done_ids = set()
    if resume and os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        rec = json.loads(line_str)
                        done_ids.add(rec["q_id"])
                    except Exception:
                        pass

    todo = [q for q in questions if q["q_id"] not in done_ids]
    print(f"\n=======================================================")
    print(f"[{variant_name}] Tổng câu: {len(questions)} | Đã làm: {len(done_ids)} | Cần chạy: {len(todo)}")
    print(f"=======================================================")

    if not todo:
        print(f"[{variant_name}] Đã hoàn thành toàn bộ.")
        return

    # Khởi tạo pipeline cấu hình c6 (Full)
    r = AblationRetriever(shared_hybrid, default_mode="hybrid_filter", auto_load=False)
    pipeline = RAGPipeline(
        llm_client=shared_llm,
        retriever=r,
        router_enabled=True,
        use_reranker=True,
        parser_mode="auto",
        disable_cache=True,
    )

    with open(output_file, "a", encoding="utf-8") as fp:
        for idx, item in enumerate(todo, 1):
            q_id = item["q_id"]
            query = item["query"]
            g_class = item.get("graph_class", "unknown")
            exp_contains = item.get("expected_answer_contains", [])
            gold_ans = item.get("gold_answer", "")

            t0 = time.time()
            try:
                res = pipeline.answer(query, session_id=f"graph_{q_id}")
                lat_ms = res.get("latency_ms", (time.time() - t0) * 1000.0)
                ans = res.get("answer", "")
                route = res.get("route", "")

                hits, pass_flag = check_contains(ans, exp_contains)
                graph_hit = (route == "structured_lookup") and not res.get("possible_fallback", False)

                record = {
                    "q_id": q_id,
                    "variant": variant_name,
                    "graph_class": g_class,
                    "query": query,
                    "route": route,
                    "answer": ans,
                    "gold_answer": gold_ans,
                    "latency_ms": round(lat_ms, 2),
                    "expected_answer_contains": exp_contains,
                    "contains_hits": hits,
                    "contains_pass": pass_flag,
                    "graph_hit": graph_hit,
                    "success": True,
                }
            except Exception as e:
                logger.error(f"Error on {q_id}: {e}")
                record = {
                    "q_id": q_id,
                    "variant": variant_name,
                    "graph_class": g_class,
                    "query": query,
                    "route": "error",
                    "answer": f"Error: {e}",
                    "gold_answer": gold_ans,
                    "latency_ms": round((time.time() - t0) * 1000.0, 2),
                    "expected_answer_contains": exp_contains,
                    "contains_hits": [],
                    "contains_pass": False,
                    "graph_hit": False,
                    "success": False,
                }

            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
            fp.flush()
            print(f"[{variant_name} {idx}/{len(todo)}] {q_id} ({g_class}) -> route: {record['route']} | pass: {record['contains_pass']}")


def print_summary(out_with: str, out_without: str):
    """In bảng so sánh per-class pass rate giữa 2 variant."""
    def load_recs(path):
        recs = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        recs.append(json.loads(line.strip()))
        return recs

    recs_with = load_recs(out_with)
    recs_without = load_recs(out_without)

    classes = sorted(list(set([r["graph_class"] for r in recs_with + recs_without])))

    print("\n" + "="*80)
    print("KẾT QUẢ ĐỐI SÁNH THỰC NGHIỆM GRAPH RAG (WITH vs WITHOUT)")
    print("="*80)
    print(f"{'Graph Class':<20} | {'WITH_GRAPH Pass':<18} | {'WITHOUT_GRAPH Pass':<18} | {'Delta':<10}")
    print("-" * 80)

    for c in classes:
        w_sub = [r for r in recs_with if r["graph_class"] == c]
        wo_sub = [r for r in recs_without if r["graph_class"] == c]

        w_pass = sum(1 for r in w_sub if r["contains_pass"]) / max(1, len(w_sub)) * 100
        wo_pass = sum(1 for r in wo_sub if r["contains_pass"]) / max(1, len(wo_sub)) * 100
        delta = w_pass - wo_pass

        print(f"{c:<20} | {w_pass:>6.1f}% ({len(w_sub):>2} q)   | {wo_pass:>6.1f}% ({len(wo_sub):>2} q)     | {delta:>+6.1f}%")

    tot_w = sum(1 for r in recs_with if r["contains_pass"]) / max(1, len(recs_with)) * 100 if recs_with else 0
    tot_wo = sum(1 for r in recs_without if r["contains_pass"]) / max(1, len(recs_without)) * 100 if recs_without else 0
    print("-" * 80)
    print(f"{'OVERALL':<20} | {tot_w:>6.1f}% ({len(recs_with):>2} q)   | {tot_wo:>6.1f}% ({len(recs_without):>2} q)     | {tot_w - tot_wo:>+6.1f}%")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description="Graph RAG Ablation Runner")
    parser.add_argument("--limit", type=int, default=0, help="Số câu hỏi muốn chạy (0=all)")
    parser.add_argument("--no-resume", action="store_true", help="Chạy lại từ đầu, bỏ qua file cũ")
    args = parser.parse_args()

    os.makedirs("experiments/graph_rag", exist_ok=True)
    out_with = "experiments/graph_rag/with_graph.jsonl"
    out_without = "experiments/graph_rag/without_graph.jsonl"

    questions = load_graph_rag_questions(args.limit)
    print(f"Loaded {len(questions)} questions from graph_rag_suite.jsonl")

    shared_llm = LLMClient()
    shared_hybrid = HybridRetriever(auto_load=True)
    shared_hybrid.ensure_loaded()

    # 1. Chạy WITH_GRAPH
    print("\n>>> BẮT ĐẦU CHẠY VARIANT 1: WITH_GRAPH (Knowledge Graph BẬT)")
    run_variant("WITH_GRAPH", True, questions, out_with, shared_hybrid, shared_llm, resume=not args.no_resume)

    gc.collect()

    # 2. Chạy WITHOUT_GRAPH
    print("\n>>> BẮT ĐẦU CHẠY VARIANT 2: WITHOUT_GRAPH (Knowledge Graph TẮT)")
    run_variant("WITHOUT_GRAPH", False, questions, out_without, shared_hybrid, shared_llm, resume=not args.no_resume)

    # Đảm bảo reset flag về True cho hệ thống
    set_graph_rag_enabled(True)

    # In kết quả
    print_summary(out_with, out_without)


if __name__ == "__main__":
    from typing import Tuple
    main()

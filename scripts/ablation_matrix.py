"""Runner chạy thực nghiệm Ablation Study Matrix (6 Cấu hình Pipeline).
Cấu hình:
- c1_bm25: BM25 baseline, không router, không reranker
- c2_dense: Dense FAISS baseline, không router, không reranker
- c3_hybrid: Hybrid (BM25 + FAISS) RRF, không filter, không router, không reranker
- c4_hybrid_rrf_filter: Hybrid RRF + Metadata Filter, không router, không reranker
- c5_full_noparser: Full (Router + Reranker + CKB lookup bằng Regex, KHÔNG Semantic Parser LLM)
- c6_full: Full + Semantic Parsing Routing (LLM Structured Parser + 10-level Router + CKB + Cross-Encoder)
"""

import argparse
import gc
import glob
import json
import os
import sys
import time
from typing import Any, Dict, List

from FPTUniQA.pipeline.ablation_retriever import AblationRetriever
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.generation.llm import LLMClient
from FPTUniQA.utils.logger import get_logger

logger = get_logger("ablation_matrix")

ALL_CONFIGS = [
    "c1_bm25",
    "c2_dense",
    "c3_hybrid",
    "c3_hybrid_sequential",
    "c3p_hybrid_parallel",
    "c4_hybrid_rrf_filter",
    "c4_hybrid_rrf_soft",
    "c5_full_noparser",
    "c6_full",
]


def load_benchmark_questions(limit: int = 0) -> List[Dict[str, Any]]:
    """Nạp câu hỏi từ benchmark v2, chia đều theo 10 batch nếu có limit."""
    all_by_batch: Dict[str, List[Dict[str, Any]]] = {}
    for f in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
        b_name = os.path.basename(f).replace(".jsonl", "")
        items = []
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                line_str = line.strip()
                if line_str:
                    items.append(json.loads(line_str))
        all_by_batch[b_name] = items

    if limit <= 0 or limit >= 500:
        flat = []
        for b_name in sorted(all_by_batch.keys()):
            flat.extend(all_by_batch[b_name])
        return flat

    # Chia đều limit cho 10 batch
    per_batch = max(1, limit // len(all_by_batch))
    sampled = []
    for b_name in sorted(all_by_batch.keys()):
        sampled.extend(all_by_batch[b_name][:per_batch])

    return sampled[:limit]


def create_pipeline(cfg_name: str, shared_hybrid: HybridRetriever, shared_llm: LLMClient) -> RAGPipeline:
    """Khởi tạo pipeline ứng với cấu hình thực nghiệm."""
    if cfg_name == "c1_bm25":
        r = AblationRetriever(shared_hybrid, default_mode="bm25", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=False,
            use_reranker=False,
            parser_mode="regex",
            disable_cache=True,
        )
    elif cfg_name == "c2_dense":
        r = AblationRetriever(shared_hybrid, default_mode="dense", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=False,
            use_reranker=False,
            parser_mode="regex",
            disable_cache=True,
        )
    elif cfg_name in ("c3_hybrid", "c3_hybrid_sequential"):
        r = AblationRetriever(shared_hybrid, default_mode="c3_hybrid_sequential", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=False,
            use_reranker=False,
            parser_mode="regex",
            disable_cache=True,
        )
    elif cfg_name in ("c3p_hybrid", "c3p_hybrid_parallel"):
        r = AblationRetriever(shared_hybrid, default_mode="c3p_hybrid_parallel", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=False,
            use_reranker=False,
            parser_mode="regex",
            disable_cache=True,
        )
    elif cfg_name in ("c4_hybrid_rrf_filter", "c4_hard"):
        r = AblationRetriever(shared_hybrid, default_mode="c4_hybrid_rrf_filter", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=False,
            use_reranker=False,
            parser_mode="regex",
            disable_cache=True,
        )
    elif cfg_name in ("c4_hybrid_rrf_soft", "c4_soft"):
        r = AblationRetriever(shared_hybrid, default_mode="c4_hybrid_rrf_soft", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=False,
            use_reranker=False,
            parser_mode="regex",
            disable_cache=True,
        )
    elif cfg_name == "c5_full_noparser":
        r = AblationRetriever(shared_hybrid, default_mode="hybrid_filter", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=True,
            use_reranker=True,
            parser_mode="regex",  # Bắt buộc Regex, KHÔNG dùng LLM Semantic Parser
            disable_cache=True,
        )
    elif cfg_name == "c6_full":
        r = AblationRetriever(shared_hybrid, default_mode="hybrid_filter", auto_load=False)
        return RAGPipeline(
            llm_client=shared_llm,
            retriever=r,
            router_enabled=True,
            use_reranker=True,
            parser_mode="auto",  # LLM Semantic Parser đầy đủ
            disable_cache=True,
        )
    else:
        raise ValueError(f"Unknown config: {cfg_name}")


def run_configuration(
    cfg_name: str,
    questions: List[Dict[str, Any]],
    output_dir: str,
    shared_hybrid: HybridRetriever,
    shared_llm: LLMClient,
    resume: bool = True,
):
    """Chạy thực nghiệm cho 1 cấu hình và append kết quả ra file JSONL."""
    out_file = os.path.join(output_dir, f"{cfg_name}.jsonl")
    done_ids = set()
    if resume and os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        record = json.loads(line_str)
                        done_ids.add(record["q_id"])
                    except Exception:
                        pass

    todo_questions = [q for q in questions if q["q_id"] not in done_ids]
    print(f"\n=======================================================")
    print(f"[{cfg_name}] Tổng câu: {len(questions)} | Đã làm: {len(done_ids)} | Cần chạy: {len(todo_questions)}")
    print(f"=======================================================")

    if not todo_questions:
        print(f"[{cfg_name}] Đã hoàn thành toàn bộ, bỏ qua.")
        return

    pipeline = create_pipeline(cfg_name, shared_hybrid, shared_llm)

    with open(out_file, "a", encoding="utf-8") as fp:
        for idx, item in enumerate(todo_questions, 1):
            q_id = item["q_id"]
            query = item["query"]
            sess_id = item.get("session_id", f"sess_{q_id}")
            t_idx = item.get("turn_index", 1)

            t0 = time.time()
            try:
                res = pipeline.answer(query, session_id=sess_id)
                lat_ms = res.get("latency_ms", (time.time() - t0) * 1000.0)
                parser_lat_ms = res.get("parser_latency_ms", 0.0)
                ans = res.get("answer", "")
                chunks = res.get("retrieved_chunks", [])
                top5_docs = [str(c.get("doc_id", "")) for c in chunks[:5]]
                parsed = res.get("parsed_query", {})
                route = res.get("route", "")
                success = bool(ans and len(ans.strip()) > 0)
                citations = [c.get("doc_id") for c in res.get("citations", [])]
                possible_hallucination = res.get("possible_hallucination", False)
                ungrounded_numbers = res.get("ungrounded_numbers", [])
                if route in ["structured_lookup", "ood", "clarification"]:
                    retrieved_context = ""
                else:
                    retrieved_context = " ".join(str(c.get("text", "")) for c in res.get("retrieved_chunks", [])).strip()[:2000]
            except Exception as e:
                logger.error(f"[{cfg_name}] Lỗi tại {q_id}: {e}")
                lat_ms = (time.time() - t0) * 1000.0
                parser_lat_ms = 0.0
                ans = f"ERROR: {e}"
                top5_docs = []
                parsed = {}
                route = "error"
                success = False
                citations = []
                possible_hallucination = False
                ungrounded_numbers = []
                retrieved_context = ""

            record = {
                "q_id": q_id,
                "config": cfg_name,
                "batch": item.get("batch", ""),
                "category": item.get("category", ""),
                "query": query,
                "session_id": sess_id,
                "turn_index": t_idx,
                "expected_route": item.get("expected_route", ""),
                "route": route,
                "answer": ans,
                "top5_doc_ids": top5_docs,
                "citations": citations,
                "possible_hallucination": possible_hallucination,
                "ungrounded_numbers": ungrounded_numbers,
                "retrieved_context": retrieved_context,
                "parsed_query": parsed,
                "fallback_used": parsed.get("fallback_used", False),
                "latency_ms": round(lat_ms, 2),
                "parser_latency_ms": round(parser_lat_ms, 2),
                "success": success,
            }

            fp.write(json.dumps(record, ensure_ascii=False) + "\n")
            fp.flush()

            # Dọn session để tránh rò rỉ bộ nhớ
            if t_idx >= 2 or not item.get("is_continuation", False):
                pipeline.session_manager.clear(sess_id)

            if idx % 10 == 0 or idx == len(todo_questions):
                print(f"[{cfg_name}] Hoàn thành {idx}/{len(todo_questions)} (lat: {lat_ms:.0f}ms)")
                gc.collect()

    pipeline.session_manager.clear()
    gc.collect()


def main():
    parser = argparse.ArgumentParser(description="Ablation Matrix Runner for FPTUniQA")
    parser.add_argument("--configs", "--config", type=str, default="", help="Comma-separated configs (e.g. c1_bm25,c6_full)")
    parser.add_argument("--output-dir", "--output_dir", type=str, default="experiments/ablation", help="Output directory")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of questions to evaluate (0 for all 500)")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume previously processed questions")
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    args = parser.parse_args()

    selected_configs = [c.strip() for c in args.configs.split(",") if c.strip()] if args.configs else ALL_CONFIGS
    invalid = [c for c in selected_configs if c not in ALL_CONFIGS]
    if invalid:
        print(f"Lỗi: Các cấu hình không hợp lệ: {invalid}. Chọn trong {ALL_CONFIGS}")
        sys.exit(1)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print(f"Đang nạp bộ câu hỏi Benchmark v2 (limit={args.limit})...")
    questions = load_benchmark_questions(limit=args.limit)
    print(f"Tổng số câu hỏi được chọn: {len(questions)}")

    print("Đang khởi tạo tài nguyên dùng chung (HybridRetriever & LLMClient)...")
    shared_hybrid = HybridRetriever(auto_load=True)
    shared_llm = LLMClient()

    for cfg in selected_configs:
        run_configuration(
            cfg_name=cfg,
            questions=questions,
            output_dir=output_dir,
            shared_hybrid=shared_hybrid,
            shared_llm=shared_llm,
            resume=args.resume,
        )

    print("\n[OK] Toàn bộ các cấu hình đã được chạy xong!")


if __name__ == "__main__":
    main()

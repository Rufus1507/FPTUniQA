"""
Runner Chạy lại Toàn bộ Ablation 8 Cấu hình Sạch từ đầu cho Báo cáo v4.
Đảm bảo:
1. Đúng 100 câu hỏi Benchmark v2 duy nhất (assert).
2. Ghi 1 file JSONL sạch cho mỗi cấu hình vào experiments/ablation_clean/.
3. Assert đúng 100 q_id duy nhất cho mỗi cấu hình sau khi chạy xong.
4. Ghi nhận thời gian, commit hash và git status.
"""

import argparse
import gc
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

from FPTUniQA.generation.llm import LLMClient
from FPTUniQA.pipeline.ablation_retriever import AblationRetriever
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.utils.logger import get_logger

logger = get_logger("run_clean_ablation")

CONFIG_SPECS = [
    ("c1_bm25", "bm25", False, False, "regex", False),
    ("c2_dense", "dense", False, False, "regex", False),
    ("c3_hybrid", "c3_hybrid_sequential", False, False, "regex", False),
    ("c3p_hybrid_parallel", "c3p_hybrid_parallel", False, False, "regex", False),
    ("c4_hybrid_rrf_soft", "c4_hybrid_rrf_soft", False, False, "regex", False),
    ("c4_hybrid_rrf_filter", "c4_hybrid_rrf_filter", False, False, "regex", False),
    ("c5_full_noparser", "hybrid_filter", True, True, "regex", True),
    ("c6_full", "hybrid_filter", True, True, "auto", True),
]

def load_canonical_100() -> List[Dict[str, Any]]:
    """Nạp chính xác 100 câu hỏi Benchmark v2 (10 câu đầu từ batch_01 đến batch_10)."""
    batch_files = sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl"))
    questions = []
    for f in batch_files:
        items = []
        with open(f, "r", encoding="utf-8") as fp:
            for l in fp:
                if l.strip():
                    items.append(json.loads(l.strip()))
        questions.extend(items[:10])
    
    assert len(questions) == 100, f"Expected 100 questions, got {len(questions)}"
    qids = [q["q_id"] for q in questions]
    assert len(set(qids)) == 100, f"Duplicate q_ids found: {len(qids)} vs {len(set(qids))} unique"
    return questions

def create_pipeline(retriever_mode: str, router_enabled: bool, use_reranker: bool, parser_mode: str, shared_hybrid: HybridRetriever, shared_llm: LLMClient) -> RAGPipeline:
    r = AblationRetriever(shared_hybrid, default_mode=retriever_mode, auto_load=False)
    return RAGPipeline(
        llm_client=shared_llm,
        retriever=r,
        router_enabled=router_enabled,
        use_reranker=use_reranker,
        parser_mode=parser_mode,
        disable_cache=True,
    )

def run_single_config(cfg_name: str, retriever_mode: str, router_enabled: bool, use_reranker: bool, parser_mode: str,
                      questions: List[Dict[str, Any]], output_dir: str, shared_hybrid: HybridRetriever, shared_llm: LLMClient):
    out_file = os.path.join(output_dir, f"{cfg_name}.jsonl")
    print(f"\n=======================================================")
    print(f"[{cfg_name}] Bắt đầu thực nghiệm sạch: 100 câu hỏi")
    print(f"Cấu hình: retriever={retriever_mode}, router={router_enabled}, rerank={use_reranker}, parser={parser_mode}")
    print(f"=======================================================")
    
    pipeline = create_pipeline(retriever_mode, router_enabled, use_reranker, parser_mode, shared_hybrid, shared_llm)
    records = []
    
    t_start_cfg = time.time()
    for idx, item in enumerate(questions, 1):
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
        records.append(record)
        
        if t_idx >= 2 or not item.get("is_continuation", False):
            pipeline.session_manager.clear(sess_id)
            
        if idx % 20 == 0 or idx == len(questions):
            print(f"[{cfg_name}] Hoàn thành {idx}/100 (lat: {lat_ms:.0f}ms)")
            gc.collect()
            
    # Ghi sạch ra file out_file (mode 'w')
    with open(out_file, "w", encoding="utf-8") as fp:
        for rec in records:
            fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    # Assert kiểm tra chất lượng file xuất ra
    with open(out_file, "r", encoding="utf-8") as fp:
        read_lines = [json.loads(l) for l in fp if l.strip()]
    assert len(read_lines) == 100, f"[{cfg_name}] Lỗi! Đọc lại thấy {len(read_lines)} dòng, không phải 100!"
    read_qids = [r["q_id"] for r in read_lines]
    assert len(set(read_qids)) == 100, f"[{cfg_name}] Lỗi! Có q_id bị trùng lặp: {len(set(read_qids))} unique!"
    
    total_time = time.time() - t_start_cfg
    print(f"[{cfg_name}] [ASSERT PASSED] Ghi thành công đúng 100 bản ghi duy nhất vào {out_file} (Thời gian: {total_time:.1f}s)")
    pipeline.session_manager.clear()
    gc.collect()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", type=str, default="", help="Comma-separated config names to run")
    parser.add_argument("--output-dir", type=str, default="experiments/ablation_clean")
    args = parser.parse_args()
    
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Báo cáo Git & Môi trường
    commit_hash = subprocess.check_output("git rev-parse HEAD", shell=True, text=True).strip()
    status_out = subprocess.check_output("git status -s", shell=True, text=True).strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 60)
    print("FPTUniQA CLEAN ABLATION RUNNER V4")
    print(f"Timestamp: {now_str}")
    print(f"Commit Hash: {commit_hash}")
    print(f"Output Directory: {out_dir}")
    print("=" * 60)
    
    questions = load_canonical_100()
    print(f"Đã nạp thành công 100 câu hỏi Benchmark v2 duy nhất.")
    
    print("Khởi tạo shared HybridRetriever và LLMClient...")
    shared_hybrid = HybridRetriever(auto_load=True)
    shared_llm = LLMClient()
    
    selected = [c.strip() for c in args.configs.split(",") if c.strip()] if args.configs else [c[0] for c in CONFIG_SPECS]
    
    for cfg_name, ret_mode, router_on, rerank_on, p_mode, _ in CONFIG_SPECS:
        if cfg_name in selected:
            run_single_config(cfg_name, ret_mode, router_on, rerank_on, p_mode, questions, out_dir, shared_hybrid, shared_llm)
            
    print("\n[HOÀN TẤT] Toàn bộ các cấu hình đã được chạy sạch và assert thành công!")

if __name__ == "__main__":
    main()

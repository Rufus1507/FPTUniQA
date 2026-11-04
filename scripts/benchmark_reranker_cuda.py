"""Script kiểm thử và đo kiểm hiệu năng thực tế của BAAI/bge-reranker-v2-m3 trên CUDA/GPU so với bge-reranker-base."""

import time
import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

def run_reranker_benchmark():
    print("=" * 70)
    print("KIỂM THỬ VÀ ĐO KIỂM CROSS-ENCODER RERANKER TRÊN CUDA")
    print("=" * 70)

    import torch
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name: {torch.cuda.get_device_name(0)}")
        print(f"Device Count: {torch.cuda.device_count()}")
        device = "cuda"
    else:
        print("CẢNH BÁO: CUDA không khả dụng, chạy trên CPU.")
        device = "cpu"

    # Lấy mẫu tài liệu thật từ BM25/FAISS index hoặc corpus.jsonl
    corpus_path = Path("data/processed/corpus.jsonl")
    if not corpus_path.exists():
        print("Không tìm thấy corpus.jsonl!")
        return

    documents = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 20:
                break
            documents.append(json.loads(line))

    print(f"Đã nạp {len(documents)} tài liệu mẫu để kiểm thử rerank.")

    test_queries = [
        "Sinh viên vắng quá 20% số buổi học thì có được thi kết thúc môn không?",
        "Muốn học môn SWP391 thì điều kiện tiên quyết là gì?",
        "Sinh viên bị điểm F thì phải học lại hay được thi lại?",
        "Học phí ngành Kỹ thuật phần mềm tại Cần Thơ là bao nhiêu?",
    ]

    from sentence_transformers import CrossEncoder

    models_to_test = [
        ("BAAI/bge-reranker-base", device),
        ("BAAI/bge-reranker-v2-m3", device),
    ]

    results_summary = {}

    for model_name, dev in models_to_test:
        print("\n" + "-" * 60)
        print(f"Đang nạp mô hình: {model_name} trên {dev}...")
        t_load_start = time.time()
        try:
            model = CrossEncoder(model_name, device=dev)
            t_load = time.time() - t_load_start
            print(f"Nạp mô hình thành công trong {t_load:.2f}s!")
        except Exception as e:
            print(f"LỖI nạp mô hình {model_name}: {e}")
            continue

        latencies = []
        scores_by_query = {}

        # Warmup
        print("Đang chạy warm-up 1 lượt...")
        _ = model.predict([("warmup query", "warmup text doc")])

        print("Bắt đầu đo đạc thời gian suy luận trên các câu hỏi thực tế:")
        for q in test_queries:
            pairs = [(q, doc.get("text", doc.get("content", ""))) for doc in documents]
            t0 = time.time()
            scores = model.predict(pairs)
            dt = (time.time() - t0) * 1000.0  # ms
            latencies.append(dt)
            # Top-1 doc
            best_idx = int(scores.argmax())
            best_score = float(scores[best_idx])
            best_doc_id = documents[best_idx].get("doc_id", documents[best_idx].get("chunk_id", "unknown"))
            scores_by_query[q] = {
                "latency_ms": dt,
                "best_doc_id": best_doc_id,
                "best_score": best_score,
            }
            print(f"  • Query: '{q[:40]}...' -> {dt:.2f} ms (Top-1: {best_doc_id}, Score: {best_score:.4f})")

        median_lat = sorted(latencies)[len(latencies)//2]
        avg_lat = sum(latencies) / len(latencies)
        print(f"\n=> TỔNG KẾT {model_name} ({dev}):")
        print(f"   - Độ trễ trung bình: {avg_lat:.2f} ms")
        print(f"   - Độ trễ Median: {median_lat:.2f} ms")
        print(f"   - Độ trễ Min/Max: {min(latencies):.2f} ms / {max(latencies):.2f} ms")

        results_summary[model_name] = {
            "load_time_s": t_load,
            "avg_latency_ms": avg_lat,
            "median_latency_ms": median_lat,
            "queries": scores_by_query,
        }

    # Xuất kết quả so sánh
    out_file = Path("experiments/reranker_comparison_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã lưu kết quả so sánh vào {out_file}")

if __name__ == "__main__":
    run_reranker_benchmark()

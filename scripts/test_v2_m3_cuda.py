"""Kiểm tra hiệu năng thực tế của BAAI/bge-reranker-v2-m3 trên CUDA với max_length=512."""

import time
import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

import torch
print(f"PyTorch Version: {torch.__version__}", flush=True)
print(f"CUDA Available: {torch.cuda.is_available()}", flush=True)
if not torch.cuda.is_available():
    print("CUDA không khả dụng! Dừng kiểm tra.", flush=True)
    sys.exit(1)

print(f"Device Name: {torch.cuda.get_device_name(0)}", flush=True)

# Lấy 20 đoạn trích thật từ corpus.jsonl
corpus_path = Path("data/processed/corpus.jsonl")
documents = []
with open(corpus_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if idx >= 20:
            break
        documents.append(json.loads(line))

print(f"Đã nạp {len(documents)} tài liệu mẫu.", flush=True)

test_queries = [
    "Sinh viên vắng quá 20% số buổi học thì có được thi kết thúc môn không?",
    "Muốn học môn SWP391 thì điều kiện tiên quyết là gì?",
    "Sinh viên bị điểm F thì phải học lại hay được thi lại?",
    "Học phí ngành Kỹ thuật phần mềm tại Cần Thơ là bao nhiêu?",
]

from sentence_transformers import CrossEncoder

model_name = "BAAI/bge-reranker-v2-m3"
print(f"\nĐang nạp mô hình {model_name} với max_length=512 trên CUDA...", flush=True)
t0 = time.time()
# Nạp CrossEncoder với max_length=512 để khống chế VRAM và ma trận Attention
model = CrossEncoder(model_name, max_length=512, device="cuda")
t_load = time.time() - t0
print(f"Nạp thành công mô hình trong {t_load:.2f}s!", flush=True)

# Warm-up 1 câu
print("Đang chạy warm-up...", flush=True)
_ = model.predict([("warmup", "doan van ban khoi dong")], batch_size=16)
print("Warm-up hoàn tất! Bắt đầu đo kiểm độ trễ...", flush=True)

latencies = []
for idx, q in enumerate(test_queries, 1):
    pairs = [[q, doc.get("text", doc.get("content", ""))[:1500]] for doc in documents]
    torch.cuda.synchronize()
    t_start = time.time()
    scores = model.predict(pairs, batch_size=16)
    torch.cuda.synchronize()
    dt = (time.time() - t_start) * 1000.0  # ms
    latencies.append(dt)
    best_idx = int(scores.argmax())
    best_score = float(scores[best_idx])
    best_doc_id = documents[best_idx].get("doc_id", documents[best_idx].get("chunk_id", "unknown"))
    print(f"Câu {idx}: '{q[:40]}...' -> {dt:.2f} ms (Top-1: {best_doc_id}, Score: {best_score:.4f})", flush=True)

median_lat = sorted(latencies)[len(latencies)//2]
avg_lat = sum(latencies) / len(latencies)
print("\n" + "=" * 60, flush=True)
print(f"KẾT QUẢ HIỆU NĂNG BAAI/bge-reranker-v2-m3 TRÊN CUDA (RTX 3060):", flush=True)
print(f"  • Độ trễ trung bình cho 20 candidates: {avg_lat:.2f} ms", flush=True)
print(f"  • Độ trễ Median: {median_lat:.2f} ms", flush=True)
print(f"  • Độ trễ Min / Max: {min(latencies):.2f} ms / {max(latencies):.2f} ms", flush=True)
print("=" * 60, flush=True)

"""Kiểm tra một câu hỏi học vụ quy chế đi qua toàn trình Text-RAG với Reranker bge-reranker-v2-m3 trên CUDA."""

import sys
import time
sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline

print("=" * 60)
print("KIỂM THỬ TRUY VẤN TEXT-RAG VỚI bge-reranker-v2-m3 TRÊN CUDA")
print("=" * 60)

pipeline = RAGPipeline(use_mock_fallback=False, rerank=True)

query = "Sinh viên vắng quá 20% buổi học thì có được thi kết thúc môn không?"
print(f"Câu hỏi kiểm thử: '{query}'")

t0 = time.time()
res = pipeline.answer(query, session_id="test_cuda_rerank")
dt = (time.time() - t0) * 1000.0

print(f"\nKết quả trả về trong {dt:.2f} ms:")
print(f"  • Tuyến định tuyến (route): {res.get('route')}")
print(f"  • Rerank được kích hoạt: {res.get('metadata', {}).get('rerank_used', True)}")
print(f"  • Số lượng trích dẫn (citations): {len(res.get('citations', []))}")
for i, c in enumerate(res.get("citations", []), 1):
    doc_id = c.get("doc_id") if isinstance(c, dict) else getattr(c, "doc_id", "N/A")
    print(f"    - Nguồn {i}: {doc_id}")
print(f"  • Câu trả lời:\n{res.get('answer')}")

assert res.get("route") == "rag_pipeline", f"LỖI: Route phải là rag_pipeline, thực tế: {res.get('route')}"
assert len(res.get("citations", [])) > 0, "LỖI: Phải có ít nhất 1 citation trích dẫn từ quy chế!"
print("\n>>> KIỂM THỬ TEXT-RAG VỚI RERANKER CUDA THÀNH CÔNG RỰC RỠ! <<<")

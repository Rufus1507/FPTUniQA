import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

test_cases = [
    "Muốn học môn SWP391 thì cần học qua những môn nào trước?",
    "Nếu bị rớt môn PRF192 thì có bị ảnh hưởng gì đến các kỳ sau không?",
    "So sánh chương trình đào tạo giữa ngành SE và AI",
    "Điều kiện để sinh viên được đi thực tập OJT là gì?",
    "Học phí ngành Kỹ thuật phần mềm ở Cần Thơ năm 2026 là bao nhiêu?",
]

print("=== KIỂM THỬ TÍCH HỢP GRAPH RAG VÀO RAG PIPELINE ===")
for q in test_cases:
    t0 = time.time()
    res = pipeline.answer(q)
    lat = (time.time() - t0) * 1000
    print(f"\n[?] Câu hỏi: '{q}'")
    print(f"[*] Route: {res['route']} | Latency: {lat:.2f} ms")
    print(f"[*] Trích dẫn: {res['citations']}")
    print(f"[*] Câu trả lời:\n{res['answer']}")
    print("-" * 60)

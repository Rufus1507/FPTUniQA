"""Script kiểm thử và audit toàn diện HybridRetriever trên 3,931 chunks dữ liệu thực tế."""

import time
import json
import sys
from pathlib import Path

# Đảm bảo utf-8 cho console Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from FPTUniQA.retrieval.retriever import HybridRetriever
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline

def run_audit():
    print("=" * 60)
    print("BƯỚC 1: KIỂM TRA TỰ ĐỘNG NẠP CHỈ MỤC (AUTO-LOAD)")
    print("=" * 60)
    t0 = time.time()
    retriever = HybridRetriever(auto_load=True)
    load_latency = (time.time() - t0) * 1000.0

    bm25_count = len(retriever.bm25_retriever.documents)
    dense_count = len(retriever.dense_retriever.documents)
    faiss_ntotal = retriever.dense_retriever._faiss_index.ntotal if retriever.dense_retriever._faiss_index else 0

    print(f"[*] Thời gian auto-load: {load_latency:.2f} ms")
    print(f"[*] Số tài liệu trong BM25 Index: {bm25_count}")
    print(f"[*] Số tài liệu trong FAISS documents: {dense_count}")
    print(f"[*] Số vector trong FAISS Index: {faiss_ntotal}")

    assert bm25_count == 3931, f"Kỳ vọng 3931 documents BM25, thực tế: {bm25_count}"
    assert dense_count == 3931, f"Kỳ vọng 3931 documents FAISS, thực tế: {dense_count}"
    assert faiss_ntotal == 3931, f"Kỳ vọng 3931 vectors FAISS, thực tế: {faiss_ntotal}"
    print("[✓] Auto-load cả 2 chỉ mục thành công tuyệt đối (3,931 / 3,931 chunks)!")

    print("\n" + "=" * 60)
    print("BƯỚC 2: KIỂM THỬ TRUY XUẤT CHUẨN CONTRACT 2 & HIỆU NĂNG LATENCY")
    print("=" * 60)

    test_queries = [
        "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
        "Điều kiện xét học bổng khuyến khích học tập?",
        "Học phí chuyên ngành Thiết kế vi mạch bán dẫn?",
        "Quy chế cảnh báo học vụ và buộc thôi học"
    ]

    for idx, query in enumerate(test_queries, 1):
        t_start = time.time()
        results = retriever.retrieve_contract2(query, top_k=3)
        latency_ms = (time.time() - t_start) * 1000.0

        print(f"\n[Test Query {idx}]: \"{query}\"")
        print(f"   -> Latency: {latency_ms:.2f} ms | Kết quả trả về: {len(results)} chunks")
        assert len(results) > 0, f"Không tìm thấy kết quả cho query: {query}"

        for r_idx, item in enumerate(results, 1):
            print(f"   [{r_idx}] doc_id: {item.get('doc_id')}")
            print(f"       strategy: {item.get('retrieval_strategy')} | score: {item.get('score'):.6f}")
            print(f"       title: {item.get('title')}")
            print(f"       category: {item.get('category')}")
            print(f"       source: {item.get('source')}")
            print(f"       snippet: {item.get('content')[:120].strip()}...")

            # Kiểm tra nghiêm ngặt tính toàn vẹn của Contract 2 qua Pydantic Model
            from contracts import DocumentChunk
            chunk = DocumentChunk(**item)
            assert 0.0 <= chunk.score <= 1.0, f"Score ngoài khoảng [0.0, 1.0]: {chunk.score}"
            assert chunk.retrieval_strategy in ("bm25", "dense", "hybrid", "mock")

    print("\n" + "=" * 60)
    print("BƯỚC 3: KIỂM THỬ METADATA PRE-FILTERING (WILDCARD & ALIAS)")
    print("=" * 60)
    filter_query = "Chương trình đào tạo Thiết kế vi mạch"
    filtered_results = retriever.retrieve_contract2(
        filter_query,
        top_k=3,
        metadata_filter={"doc_type": "curriculum"}
    )
    print(f"[*] Query có filter doc_type='curriculum': {len(filtered_results)} kết quả")
    for r in filtered_results:
        meta = r.get("metadata", {})
        doc_type = meta.get("doc_type") or r.get("category")
        print(f"   - doc_id: {r.get('doc_id')} | doc_type: {doc_type} | title: {r.get('title')}")
        assert doc_type == "curriculum", f"Lọc sai doc_type: {doc_type}"

    # Kiểm tra lọc campus với wildcard 'all'
    campus_results = retriever.retrieve_contract2(
        "học phí",
        top_k=5,
        metadata_filter={"campus": "ha_noi"}
    )
    print(f"[*] Query có filter campus='ha_noi': {len(campus_results)} kết quả")
    for r in campus_results:
        meta = r.get("metadata", {})
        campus_val = meta.get("campus")
        assert campus_val in ("ha_noi", "all"), f"Lọc sai campus: {campus_val}"

    print("\n" + "=" * 60)
    print("BƯỚC 4: KIỂM THỬ EDGE CASES TRUY VẤN RỖNG & ĐẶC BIỆT")
    print("=" * 60)
    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []
    assert retriever.retrieve(None) == []
    assert retriever.retrieve_contract2("") == []
    assert retriever.bm25_retriever.retrieve("") == []
    assert retriever.dense_retriever.retrieve("") == []
    print("[✓] Toàn bộ edge case truy vấn rỗng/whitespace/None trả về [] chính xác!")

    print("\n" + "=" * 60)
    print("BƯỚC 5: KIỂM THỬ TÍCH HỢP TOÀN DIỆN VỚI RAGPIPELINE")
    print("=" * 60)
    pipeline = RAGPipeline()
    assert pipeline.retriever is not None, "Pipeline chưa tích hợp HybridRetriever!"
    assert len(pipeline.retriever.bm25_retriever.documents) == 3931, "Pipeline BM25 chưa load dữ liệu thực!"
    assert pipeline.retriever.dense_retriever._faiss_index.ntotal == 3931, "Pipeline FAISS chưa load dữ liệu thực!"
    print("[✓] RAGPipeline đã tự động nạp HybridRetriever với kho tri thức 3,931 chunks thực tế!")

    rag_res = pipeline.answer("Quy chế cảnh báo học vụ như thế nào?")
    print(f"[*] Route được chọn: {rag_res.get('route')}")
    print(f"[*] Số chunks thực tế truy xuất: {len(rag_res.get('retrieved_chunks', []))}")
    assert len(rag_res.get("retrieved_chunks", [])) > 0, "Pipeline không lấy được chunk thực tế nào!"
    print(f"[*] Câu trả lời mẫu:\n{rag_res.get('answer')[:200]}...")

    print("\n" + "=" * 60)
    print("BƯỚC 6: KIỂM THỬ CROSS-ENCODER RERANKER & TWO-STAGE RETRIEVAL")
    print("=" * 60)
    from FPTUniQA.reranking.cross_encoder import CrossEncoderReranker

    reranker = CrossEncoderReranker()
    test_docs = [
        {"id": "doc_noise", "title": "Bóng đá", "text": "CLB thể thao sinh viên giao lưu bóng đá."},
        {"id": "doc_target", "title": "Học bổng", "text": "Quy định học bổng tài năng và khuyến khích học tập."},
    ]
    rerank_out = reranker.rerank("học bổng cho sinh viên", test_docs, top_n=2)
    print(f"[*] Kết quả rerank: {[(d['id'], s) for d, s in rerank_out]}")
    assert len(rerank_out) == 2
    assert rerank_out[0][0]["id"] == "doc_target"
    for _, s in rerank_out:
        assert 0.0 <= s <= 1.0, f"Score reranker ngoài [0.0, 1.0]: {s}"

    # Kiểm tra tính đơn điệu của hàm chuẩn hóa điểm
    norm_mono = CrossEncoderReranker._normalize_scores([-2.5, -0.01, 0.01, 2.5])
    print(f"[*] Kiểm tra đơn điệu [-2.5, -0.01, 0.01, 2.5] -> {norm_mono}")
    assert norm_mono[0] < norm_mono[1] < norm_mono[2] < norm_mono[3]

    # Kiểm tra hỗ trợ 'content' fallback và lọc None
    resilient_out = reranker.rerank(
        "quy chế",
        [None, {}, {"id": "doc_content", "title": "Quy chế", "content": "Quy chế đào tạo"}],
        top_n=2,
    )
    assert len(resilient_out) == 1
    assert resilient_out[0][0]["id"] == "doc_content"

    # Kiểm tra score thresholding
    threshold_out = reranker.rerank("học bổng", test_docs, top_n=2, score_threshold=0.5)
    print(f"[*] Kết quả sau khi thresholding >= 0.5: {[(d['id'], s) for d, s in threshold_out]}")
    for _, s in threshold_out:
        assert s >= 0.5, f"Score nhỏ hơn threshold 0.5: {s}"

    # Kiểm tra retrieve_contract2 với rerank=True từ retriever thật
    reranked_chunks = retriever.retrieve_contract2("học bổng FPT", top_k=3, rerank=True)
    print(f"[*] retrieve_contract2 (rerank=True) trả về {len(reranked_chunks)} chunks:")
    assert len(reranked_chunks) > 0
    for chunk_dict in reranked_chunks:
        from contracts import DocumentChunk
        dc = DocumentChunk(**chunk_dict)
        print(f"   - doc_id: {dc.doc_id} | score: {dc.score:.4f} | strategy: {dc.retrieval_strategy} | title: {dc.title}")
        assert 0.0 <= dc.score <= 1.0
        assert dc.retrieval_strategy in ("bm25", "dense", "hybrid", "mock")

    # Kiểm tra RAGPipeline xử lý gracefully khi không tìm thấy tài liệu (KHÔNG inject mock doc)
    class EmptyRetriever:
        def retrieve_contract2(self, *args, **kwargs):
            return []

    pipeline_empty = RAGPipeline(retriever=EmptyRetriever(), use_mock_fallback=False)
    empty_res = pipeline_empty.answer("Quy định về cảnh báo học vụ XYZ12345 như thế nào?")
    print(f"[*] Phản hồi khi retriever rỗng (use_mock_fallback=False):\n   \"{empty_res.get('answer')}\"")
    assert "không tìm thấy tài liệu phù hợp" in empty_res.get("answer", "")
    assert len(empty_res.get("retrieved_chunks", [])) == 0
    print("[✓] RAGPipeline xử lý gracefully khi không có tài liệu và KHÔNG inject mock docs!")

    print("\n" + "=" * 60)
    print("TỔNG KẾT: TẤT CẢ CÁC BƯỚC AUDIT ĐỀU THÀNH CÔNG 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_audit()

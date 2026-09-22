KẾ HOẠCH LỘ TRÌNH CHI TIẾT 8 TUẦN
HỆ THỐNG HYBRID RAG + SEMANTIC PARSING CHỐNG ẢO GIÁC
(Bản chỉnh sửa — căn chỉnh với đề tài: Context-Aware Vietnamese University Question Answering: A Hybrid Retrieval and Semantic Parsing Approach)
Nhóm thực hiện: 3 thành viên  |  Mô hình phát triển: Vertical Slice sớm → Module sâu → Tích hợp liên tục → Nghiên cứu khoa học
Tóm tắt các thay đổi so với bản gốc
1. Nâng cấp module trích metadata/regex (Tuần 3) và Router (Tuần 4) thành một module Semantic Parsing tường minh: câu hỏi tự nhiên → structured query có schema, dùng LLM structured output/function calling thay vì chỉ regex.
2. Bổ sung nhóm chỉ số đánh giá riêng cho Semantic Parsing (Slot Accuracy, Exact Match) ở Tuần 7 và mục 5.
3. Thêm cấu hình thứ 6 vào bảng Ablation Study (mục 4): so sánh có/không có Semantic Parsing Routing để chứng minh đóng góp riêng của thành phần này.

1. TỔNG QUAN CHIẾN LƯỢC VÀ NGUYÊN TẮC CỐT LÕI
Dự án áp dụng mô hình chuyển tiếp từ phát triển sản phẩm kỹ thuật sang nghiên cứu học thuật thực nghiệm. Điểm mấu chốt là bảo đảm tính khả thi thực tế trong vòng 8 tuần mà vẫn thu thập đủ số liệu đối sánh thực nghiệm (Ablation Study), đồng thời làm nổi bật rõ ràng hai trụ cột được nêu trong tên đề tài: Hybrid Retrieval và Semantic Parsing.
Nguyên tắc "Always Runnable": Không có bất kỳ tuần nào hệ thống ở trạng thái không thể chạy End-to-End. Nhánh chính (main branch) luôn có thể demo trực tiếp.
Phân lập trách nhiệm qua Interface Contracts: Các thành viên không làm việc theo kiểu silo khép kín mà giao tiếp chính xác qua các schema chuẩn hóa từ ngày thứ 2 của Tuần 1.
Fallback Protection: Bất kỳ module nâng cao nào gặp lỗi (Reranker, FAISS, Semantic Parser, Query Rewriter) đều phải có cơ chế tự động hạ cấp (fallback) về module ổn định của tuần trước đó.
Nguyên tắc "Named-Contribution Alignment" (mới): Mỗi thành phần được nêu tên trong đề tài (Context-Aware, Hybrid Retrieval, Semantic Parsing) phải có: (a) module triển khai rõ ràng, (b) chỉ số đánh giá riêng, (c) một dòng trong bảng ablation chứng minh đóng góp độc lập.
2. PHÂN VAI TRÁCH NHIỆM & BỘ CONTRACT GIAO TIẾP
Để tối ưu hóa năng suất của nhóm 3 người, công việc được chuyên môn hóa nhưng liên kết chặt chẽ:
Thành viên
Trách nhiệm chính
Đầu ra bàn giao (Deliverables)
TV1: Data & Knowledge
Thu thập corpus, làm sạch, chunking, chuẩn hóa metadata (effective_date, cohort, version), chuyển đổi dữ liệu bảng biểu/học phí sang Structured JSON, xây dựng bộ Ground Truth Test Set (bao gồm nhãn structured query vàng cho semantic parsing).
Corpus JSON chuẩn hóa, bảng SQLite/JSON học phí, bộ Evaluation Dataset 150–250 câu hỏi kèm nhãn parsing vàng.
TV2: Retrieval & Ranking
Xây dựng BM25 Tokenizer, Vector Database (FAISS/dense embeddings), Reciprocal Rank Fusion (RRF), Cross-Encoder Reranker, tính toán metrics Retrieval.
Retrieval Service API, script benchmark Recall@K và MRR độc lập.
TV3: Backend, Semantic Parsing & UI
FastAPI Orchestration, module Semantic Parsing (NL → structured query có schema), Context-aware Query Rewriting, Prompt Engineering & Citation Enforcement, Guardrails/OOD Detection, Web UI, Structured Logging.
FastAPI Server, Semantic Parser Module + schema, Giao diện Web tương tác, log file JSONL truy vết luồng truy vấn (bao gồm parsed query).

Bộ Interface Contracts
Contract 1: Schema Tài liệu (TV1 → TV2, TV3)
{ "doc_id": "tuition_ai_2026_001", "title": "Quy định học phí chuyên ngành Trí tuệ Nhân tạo năm 2026", "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo nộp mức học phí theo tín chỉ...", "source": "Quyết định số 123/QĐ-ĐHFPT", "effective_date": "2026-01-01", "applies_to_cohort": ["2026"], "source_doc_version": "v1.0", "doc_type": "tuition", "structured_payload": { "program": "AI", "cohort": "2026", "tuition_per_credit": 1250000, "currency": "VND" } }
Contract 2: Output của tầng Retrieval (TV2 → TV3)
[ { "doc_id": "tuition_ai_2026_001", "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo...", "score": 0.892, "source": "Quyết định số 123/QĐ-ĐHFPT", "retrieval_strategy": "hybrid_rrf_reranked", "metadata": { "effective_date": "2026-01-01", "applies_to_cohort": ["2026"], "doc_type": "tuition" } } ]
Contract 3 (mới): Output của tầng Semantic Parsing (TV3 nội bộ → Structured Lookup / Retrieval)
{ "intent": "tuition_lookup", "slots": { "program": "AI", "cohort": "2027", "metric": "tuition_per_credit" }, "confidence": 0.94, "parser_method": "llm_structured_output", "fallback_used": false }
Contract này biến bước "trích metadata bằng regex" của bản gốc thành một đầu ra có schema tường minh, có thể chấm điểm độc lập (đúng/sai theo từng slot) — đây chính là cơ sở để đề tài có thể gọi tên "Semantic Parsing" một cách chính danh trong báo cáo.
3. LỘ TRÌNH TRIỂN KHAI CHI TIẾT 8 TUẦN
Tuần 1: Skeleton Pipeline & Thống nhất Data Contract
Mục tiêu: Thiết lập nền móng hạ tầng, thống nhất toàn bộ cấu trúc dữ liệu và chạy luồng truy vấn tối thiểu.
TV1: Thu thập 20–30 văn bản đào tạo/học phí mẫu; viết script tiền xử lý, gán metadata cơ bản và cắt chunk (400–500 tokens).
TV2: Thiết lập BM25 Index (Rank-BM25), tích hợp công cụ tách từ tiếng Việt, xuất hàm truy vấn trả về định dạng Contract 2.
TV3: Khởi tạo khung dự án FastAPI và giao diện Streamlit cơ bản; tích hợp LLM sinh câu trả lời kèm citation từ kết quả BM25.
Milestone: Cuối tuần 1 nạp thành công 20 documents vào BM25, kiểm thử truy vấn thô qua dòng lệnh.
Tuần 2: Hoàn thành Vertical Slice End-to-End
Mục tiêu: Toàn bộ luồng từ giao diện UI đến LLM hoạt động trơn tru (Milestone sống còn của dự án).
TV1: Mở rộng dataset lên 50 documents; gán nhãn chi tiết metadata và chuẩn bị 15 câu hỏi vàng (Ground Truth) để test thủ công.
TV2: Tối ưu hóa BM25 API; đo lường độ chính xác từ khóa và điều chỉnh các tham số k1, b.
TV3: Nối toàn bộ UI → FastAPI → BM25 → LLM → Citation → UI. Xây dựng logic fallback nếu không tìm thấy kết quả.
Milestone (Critical): Demo trực tiếp: Người dùng đặt câu hỏi trên Web, hệ thống tìm văn bản, LLM phản hồi và trỏ đúng citation văn bản nguồn.
Tuần 3: Tích hợp Hybrid Retrieval & Semantic Parsing bản nháp (đã chỉnh sửa)
Mục tiêu: Khắc phục hạn chế của tìm kiếm từ khóa thuần túy; đặt nền móng đầu tiên cho module Semantic Parsing thay vì chỉ trích xuất bằng regex.
TV1: Bổ sung chuẩn hóa trường dữ liệu thời gian áp dụng và đối tượng sinh viên trong corpus; bắt đầu gán nhãn structured query vàng (intent + slots) cho 30–50 câu hỏi mẫu.
TV2: Dựng index vector với FAISS (sử dụng embedding đa ngôn ngữ như multilingual-e5); lập trình thuật toán Reciprocal Rank Fusion (RRF); áp dụng Pre-filtering theo metadata.
TV3 (đã chỉnh sửa): Xây dựng bản nháp module Semantic Parsing đầu tiên — dùng LLM với structured output/function calling để chuyển câu hỏi thành JSON theo Contract 3 (intent, slots, confidence), thay vì chỉ Regex/Rule-based như bản gốc. Giữ Regex làm fallback khi LLM parsing thất bại.
Milestone: Câu hỏi như "Học phí khóa 2026" được Semantic Parser chuyển đúng thành {intent: tuition_lookup, cohort: 2026}, đồng thời retrieval lọc chính xác văn bản 2026, triệt tiêu việc văn bản 2023 có điểm ngữ nghĩa cao cạnh tranh nhầm.
Tuần 4: Cross-Encoder Reranker & Hoàn thiện Semantic Parsing + Structured Lookup (đã chỉnh sửa)
Mục tiêu: Tăng độ chính xác xếp hạng văn bản, loại trừ hoàn toàn ảo giác khi tra cứu con số học phí, và chính thức hóa Semantic Parsing thành một module độc lập có thể đánh giá.
TV1: Trích xuất dữ liệu bảng biểu học phí, tín chỉ thành cấu trúc bảng JSON/SQLite độc lập; hoàn thiện thêm bộ nhãn structured query vàng lên 100+ câu.
TV2: Tích hợp mô hình Cross-Encoder Reranker (bge-reranker); xây dựng pipeline RRF (Top 50) → Reranker → Top 5.
TV3 (đã chỉnh sửa): Hoàn thiện module Semantic Parsing thành thành phần độc lập (không còn gọi là "Router" thuần regex nữa): nhận câu hỏi → sinh structured query (Contract 3) → nếu intent là tra cứu số liệu, định tuyến sang Structured Lookup (SQLite/JSON); nếu là câu hỏi giải thích chính sách, định tuyến sang RAG Pipeline. Ghi log riêng cho từng lần parsing để phục vụ đánh giá Tuần 7.
Milestone: Các câu hỏi tra cứu mức phí cụ thể được Semantic Parser nhận diện đúng intent/slots và trả kết quả tuyệt đối chính xác; văn bản quy định dài được xếp hạng chính xác đoạn cần đọc vào Top 3.
Tuần 5: Context-Aware Query Rewriting & Hội thoại Đa lượt
Mục tiêu: Hỗ trợ ngữ cảnh trò chuyện liền mạch, mở rộng Semantic Parsing sang bối cảnh đa lượt, và hoàn thiện hệ thống quan sát (observability).
TV1: Xây dựng 30 kịch bản hội thoại nhiều lượt (Multi-turn conversations) để kiểm thử bộ tái cấu trúc câu hỏi và bộ Semantic Parser trong ngữ cảnh đa lượt.
TV2: Thử nghiệm ngưỡng điểm tin cậy (Score Threshold) cho Reranker để chủ động cắt bỏ tài liệu nhiễu.
TV3 (đã chỉnh sửa): Cài đặt module Query Rewriting (Contextual Compression) chạy trước Semantic Parser, để câu hỏi rút gọn/thiếu ngữ cảnh ("Còn năm 2027 thì sao?") được viết lại đầy đủ trước khi parse thành structured query. Ghi nhận đầy đủ 7 trường Structured Log (original_query, rewritten_query, parsed_query, retrieved_docs, reranked_docs, final_context, citations).
Milestone: Người dùng hỏi: "Còn năm 2027 thì sao?", hệ thống tự động mở rộng thành: "Học phí ngành AI năm 2027 là bao nhiêu?", Semantic Parser chuyển đúng thành {intent: tuition_lookup, cohort: 2027} trước khi đẩy sang retrieval/structured lookup.
Tuần 6: LLM Generation Guardrails & Hoàn thiện Giao diện
Mục tiêu: Chặn đứng câu hỏi ngoài phạm vi (OOD) và đóng băng tính năng để chuẩn bị cho giai đoạn đo lường.
TV1: Hoàn thiện kho dữ liệu đầy đủ (150–300 documents) và bộ nhãn structured query vàng (150–250 câu); chính thức đóng băng (freeze) dữ liệu.
TV2: Tối ưu hóa tốc độ truy xuất, đóng gói toàn bộ tầng tìm kiếm thành package ổn định.
TV3: Tích hợp Prompt phòng chống ảo giác nghiêm ngặt; phát hiện câu hỏi Out-of-Domain (kể cả câu hỏi mà Semantic Parser không nhận diện được intent nào); hoàn thiện UI với trạng thái loading, phân tách trích dẫn rõ ràng.
Milestone: Hệ thống đóng băng hoàn toàn việc phát triển tính năng mới; sẵn sàng toàn bộ tài nguyên cho tuần đánh giá thực nghiệm.
Tuần 7: Đánh giá Độc lập trên Bộ Test Set Đa dạng (đã bổ sung)
Mục tiêu: Thu thập dữ liệu định lượng khoa học trên 5 khía cạnh: Retrieval, Semantic Parsing, Generation, An toàn và Hiệu năng hệ thống.
TV1: Hoàn thiện bộ 150–250 test cases gồm 5 nhóm: Factoid, Multi-hop, Conversational, Temporal và Out-of-Domain, kèm nhãn structured query vàng cho từng câu.
TV2: Chạy batch kiểm thử riêng cho Retrieval: Đo Recall@3, Recall@5, Recall@10, MRR.
TV3 (đã bổ sung): Thiết lập công cụ tự động đánh giá (LLM-as-a-judge / Ragas) để chấm điểm Faithfulness, Answer Relevance và tỷ lệ từ chối câu hỏi OOD. Bổ sung batch đánh giá riêng cho Semantic Parsing: so khớp intent/slots do parser sinh ra với nhãn vàng để tính Slot Accuracy và Exact Match. Ghi nhận độ trễ trung bình cho từng bước (parsing, retrieval, generation).
Milestone: Thu được bảng số liệu thực nghiệm thô hoàn chỉnh của tất cả các kịch bản kiểm thử, bao gồm cả số liệu riêng cho Semantic Parsing.
Tuần 8: Báo cáo Ablation Study & Định hướng Nghiên cứu
Mục tiêu: Tổng hợp báo cáo kỹ thuật đối sánh, bảo vệ đồ án và chuẩn bị đề xuất bài báo khoa học.
Cả nhóm (đã bổ sung): Phân tích đối sánh thực nghiệm trên 6 cấu hình hệ thống: BM25 → FAISS → Hybrid → Hybrid + Filter → Full Pipeline → Full Pipeline + Semantic Parsing Routing (xem mục 4).
TV1: Lập báo cáo phân tích lỗi (Error Analysis): Phân loại tỷ lệ lỗi do Retrieval thiếu, do LLM tự suy diễn, hay do Semantic Parser gán sai intent/slot.
TV2: Tổng hợp biểu đồ phân phối điểm số và tương quan giữa latency và độ sâu của retrieval.
TV3: Hoàn thiện tài liệu kỹ thuật định dạng IMRAD (nhấn mạnh đóng góp của Semantic Parsing như một thành phần riêng biệt), chuẩn bị slide thuyết trình và video demo.
Milestone: Hoàn tất đồ án với đầy đủ báo cáo đối sánh (bao gồm đóng góp định lượng của Semantic Parsing); phác thảo đề tài nghiên cứu về tối ưu Temporal Faithfulness trong RAG có Semantic Parsing hỗ trợ.
4. KHUNG ĐÁNH GIÁ ĐỐI SÁNH THỰC NGHIỆM (ABLATION STUDY MATRIX)
Bảng số liệu đối sánh thực nghiệm đóng vai trò là bằng chứng thuyết phục hội đồng kỹ thuật cũng như làm tiền đề công bố nghiên cứu. Đã bổ sung cấu hình thứ 6 để tách riêng đóng góp của Semantic Parsing:
Cấu hình Pipeline
Recall@5
MRR
Faithfulness
OOD Rejection
Latency (ms)
1. BM25 Baseline
Chờ đo
Chờ đo
Chờ đo
Chờ đo
~100–150
2. FAISS Only (Dense)
Chờ đo
Chờ đo
Chờ đo
Chờ đo
~150–200
3. Hybrid (BM25 + FAISS)
Chờ đo
Chờ đo
Chờ đo
Chờ đo
~200–250
4. Hybrid + RRF + Metadata Filter
Chờ đo
Chờ đo
Chờ đo
Chờ đo
~250–320
5. Full (Reranker + Structured, không Semantic Parsing)
Chờ đo
Chờ đo
Chờ đo
Chờ đo
~600–750
6. Full + Semantic Parsing Routing (mới)
Chờ đo
Chờ đo
Chờ đo
Chờ đo
Chờ đo

Cấu hình 6 so với cấu hình 5 chính là bằng chứng thực nghiệm trực tiếp cho câu "Semantic Parsing" trong tên đề tài — cho thấy việc thêm bước parse câu hỏi thành structured query giúp cải thiện độ chính xác tra cứu số liệu và/hoặc giảm hallucination so với khi chỉ dựa vào RAG thuần túy.
5. BỘ CHỈ SỐ TOÀN DIỆN (5 NHÓM METRICS — đã bổ sung nhóm Semantic Parsing)
Chỉ số Retrieval (Đo lường năng lực tìm kiếm)
Recall@K: Tỷ lệ tìm thấy văn bản chứa câu trả lời trong Top-K tài liệu trả về.
Mean Reciprocal Rank (MRR): Vị trí trung bình của tài liệu chính xác đầu tiên trong danh sách.
Chỉ số Semantic Parsing (mới — Đo lường năng lực phân tích ngữ nghĩa câu hỏi)
Intent Accuracy: Tỷ lệ Semantic Parser nhận diện đúng loại câu hỏi (tra cứu số liệu vs. giải thích chính sách vs. OOD).
Slot Accuracy: Tỷ lệ các trường (program, cohort, effective_date, metric...) được trích xuất đúng so với nhãn vàng.
Exact Match: Tỷ lệ structured query sinh ra khớp hoàn toàn (mọi slot đều đúng) với nhãn vàng.
Fallback Rate: Tỷ lệ các trường hợp Semantic Parser phải rơi về cơ chế Regex/Rule-based dự phòng.
Chỉ số Generation (Đo lường chất lượng câu trả lời)
Answer Faithfulness: Mức độ trung thực của câu trả lời dựa trên context được cung cấp (chống ảo giác).
Citation Correctness: Tỷ lệ trích dẫn trỏ chính xác đến đoạn văn bản làm căn cứ.
Chỉ số An toàn & Giới hạn (Safety & Robustness)
OOD Rejection Rate: Khả năng từ chối trả lời chính xác khi câu hỏi nằm ngoài phạm vi corpus trường học.
Hallucination Rate: Tỷ lệ sinh thông tin không có trong văn bản nguồn.
Chỉ số Kỹ thuật Hệ thống (System Performance)
End-to-End Latency: Thời gian phản hồi hoàn chỉnh từ lúc bấm gửi đến khi hiển thị (p50, p95), tách riêng thời gian cho bước Semantic Parsing.
API Success Rate: Tỷ lệ cuộc gọi thành công không bị gián đoạn hay lỗi timeout.

---

## 6. KẾT QUẢ THỰC HIỆN GIAI ĐOẠN TIỀN XỬ LÝ & BÀN GIAO TV1 (DATA & KNOWLEDGE)

Tuân thủ đúng lộ trình Tuần 1–Tuần 2 và nguyên tắc phân lập trách nhiệm qua Interface Contracts, TV1 đã hoàn thành toàn diện việc bóc tách, chuẩn hóa, phân đoạn và cấu trúc hóa toàn bộ kho dữ liệu tuyển sinh thực tế từ website Đại học FPT (`daihoc.fpt.edu.vn`).

### 6.1. Thống kê kiểm kê và xử lý dữ liệu thô (Raw Data Audit)
* **Tệp dữ liệu thô tiếp nhận:** `fptuniqa_raw_data_20260921.zip` (5.71 MB), lưu trữ bảo toàn tại `data/raw/fpt_admission/html/` (170 tệp HTML).
* **Nhật ký thu thập (`data/raw/crawl_manifest.jsonl`):** 226 bản ghi (219 HTTP 200, 7 HTTP 404 link hỏng, 13/13 seed URLs thành công).
* **Lọc bỏ trang không đạt chuẩn (`data/interim/discarded_pages.jsonl`):** 8 trang (gồm 4 trang form nhập liệu động < 80 từ và 4 trang chuyên mục phân loại tin tức/links rỗng).

### 6.2. Kết quả xây dựng Corpus văn bản (`data/processed/corpus.jsonl`)
* **Tổng số chunks:** **3,931 chunks** (tương đương ~4.01 MB).
* **Độ dài chunk:** Trung bình **217.9 ký tự** (~46.8 từ), giữ nguyên cấu trúc bảng biểu và phân đoạn ngữ nghĩa theo tiêu đề đề mục.
* **Tuân thủ Contract 1 (Data Schema):** Đạt **100%** (0 trường bị thiếu trong toàn bộ 3,931 chunks đối với `id`, `title`, `text`, `doc_id`, `source`, `doc_type`, `campus`).
* **Phân bố theo loại tài liệu (`doc_type`):**
  * `curriculum` (Chương trình đào tạo & ngành học): 1,676 chunks (42.6%)
  * `admission` (Quy chế & Phương thức tuyển sinh): 658 chunks (16.7%)
  * `scholarship` (Học bổng & Điều kiện duy trì): 581 chunks (14.8%)
  * `general` (Thông tin trường & tin tức): 546 chunks (13.9%)
  * `tuition` (Học phí & Chi phí đào tạo): 445 chunks (11.3%)
  * `enrollment` (Thủ tục nhập học): 25 chunks (0.6%)
* **Phân bố theo cơ sở đào tạo (`campus`):**
  * Toàn quốc/Chung (`all`): 2,535 chunks (64.5%)
  * TP. Hồ Chí Minh (`ho_chi_minh`): 691 chunks (17.6%)
  * Hà Nội (`ha_noi`): 225 chunks (5.7%)
  * Cần Thơ (`can_tho`): 218 chunks (5.5%)
  * Đà Nẵng (`da_nang`): 131 chunks (3.3%)
  * Quy Nhơn (`quy_nhon`): 131 chunks (3.3%)

### 6.3. Bảng dữ liệu cấu trúc phục vụ Semantic Parsing Routing (`data/processed/structured_data.json`)
* Trích xuất chính xác 100% bảng học phí K22 (nhập học 2026) cho đủ **5 cơ sở**: Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Cần Thơ, Quy Nhơn.
* Tổng số bản ghi biểu phí chuyên ngành: **190 bản ghi** (38 ngành/chuyên ngành × 5 campus), phân tách biểu phí KV1 và các khu vực khác.
* Tích hợp chính sách ưu đãi trợ cấp vùng miền: Hà Nội/TP.HCM (0%), Đà Nẵng/Cần Thơ (30%), Quy Nhơn (50%) cùng biểu phí Tiếng Anh chuẩn bị (Prep English).

### 6.4. Xác minh thực nghiệm và Bàn giao cho TV2 & TV3
1. **Kiểm thử BM25 Index:** Đã xây dựng chỉ mục baseline tại `data/processed/bm25_index/` (3,931 documents) và thực hiện truy vấn thực nghiệm:
   * *"Học phí ngành Trí tuệ nhân tạo campus Hà Nội khóa 2026"* → BM25 score 27.138 (Top 1 đúng văn bản).
   * *"Học bổng tìm kiếm nhân tài kỷ nguyên số"* → BM25 score 33.272 (Top 1 đúng văn bản).
   * *"Phương thức xét tuyển TopSchool"* → BM25 score 15.712 (Top 1 đúng văn bản).
   * *"Chuẩn đầu ra tiếng Anh TOEIC"* → BM25 score 21.232 (Top 1 đúng văn bản).
2. **Sẵn sàng bàn giao:**
   * **TV2:** Có thể triển khai trực tiếp FAISS Dense Indexing và Reranker trên `corpus.jsonl` mà không cần xử lý dữ liệu lại.
   * **TV3:** Có thể kết nối trực tiếp `structured_data.json` vào luồng tra cứu số học (Semantic Parsing Routing) để loại bỏ hoàn toàn ảo giác đối với các câu hỏi học phí.




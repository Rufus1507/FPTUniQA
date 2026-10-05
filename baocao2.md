2. ĐỀ XUẤT KIẾN TRÚC HỆ THỐNG
Hệ thống Hybrid RAG + Semantic Parsing chống ảo giác cho hỏi đáp học vụ
Mục này trình bày chi tiết kiến trúc hệ thống được đề xuất, bao gồm ba nội dung theo đúng yêu cầu của môn học: (1) mô tả kiến trúc tổng thể theo từng tầng xử lý, (2) mô tả luồng dữ liệu (dataflow) xuyên suốt từ khi người dùng đặt câu hỏi đến khi nhận được câu trả lời, và (3) tính năng cụ thể của từng thành phần kiến trúc.
2.1. Mô tả kiến trúc
Kiến trúc hệ thống được thiết kế theo mô hình phân tầng (layered architecture) gồm 7 tầng xử lý, tách bạch rõ trách nhiệm giữa việc thu thập dữ liệu, hiểu ngữ nghĩa câu hỏi, truy xuất thông tin và sinh câu trả lời. Việc phân tầng này giúp mỗi thành phần có thể phát triển, kiểm thử và đánh giá độc lập (theo nguyên tắc Named-Contribution Alignment), đồng thời cho phép cơ chế fallback khi một module nâng cao gặp lỗi.
Tầng kiến trúc
Thành phần chính
Vai trò tổng quát
1. Ingestion Layer
Document Converter (Microsoft MarkItDown), Data Collector, Chunker, Metadata Tagger, Table Extractor
Thu thập văn bản quy chế/học phí đa định dạng (PDF, DOCX, XLSX), chuyển đổi và chuẩn hóa sang Markdown có cấu trúc nhờ MarkItDown, cắt chunk 400–500 tokens, gán metadata (effective_date, cohort, doc_type), tách dữ liệu bảng biểu sang SQLite/JSON.
2. Context Layer
Context-Aware Query Rewriter
Phân giải câu hỏi tỉnh lược/đồng tham chiếu dựa trên 3–5 lượt hội thoại gần nhất trước khi đưa vào các tầng xử lý phía sau.
3. Parsing/Routing Layer
Semantic Parser (Intent + Slot Filling), Regex Fallback, Router (Intent Classification)
Chuyển câu hỏi tự nhiên thành structured query (intent, slots, confidence); khi Semantic Parser lỗi/độ tin cậy thấp, hạ cấp về Regex Fallback. Cả hai cùng đổ kết quả vào Router — thành phần duy nhất ra quyết định định tuyến sang 1 trong 3 nhánh: Structured Lookup, Hybrid Retrieval, hoặc OOD Guardrail.
4. Retrieval Layer
Metadata Pre-filter, BM25 Index, FAISS Dense Index, RRF Fusion, Cross-Encoder Reranker
Lọc cứng theo cohort/effective_date trước để thu hẹp tập tài liệu ứng viên, sau đó truy xuất song song theo cả từ khóa (BM25) và ngữ nghĩa (FAISS), hợp nhất bằng RRF, xếp hạng lại bằng reranker.
5. Structured Lookup Layer
SQLite/JSON Query Engine
Tra cứu trực tiếp số liệu học phí/tín chỉ theo slot đã parse, đảm bảo độ chính xác tuyệt đối cho câu hỏi định lượng.
6. Generation Layer
LLM Answer Generator, Citation Enforcer, OOD Guardrail
Sinh câu trả lời tự nhiên kèm trích dẫn nguồn từ context đã truy xuất/tra cứu; từ chối trả lời an toàn khi câu hỏi ngoài phạm vi (OOD).
7. Presentation Layer
FastAPI Backend, Web UI (Streamlit)
Giao tiếp với người dùng cuối, hiển thị câu trả lời, trạng thái loading và trích dẫn; ghi log JSONL toàn bộ luồng xử lý.


Sơ đồ khối tổng quát
Pipeline xử lý dữ liệu offline (chuẩn bị dữ liệu):
[Văn bản gốc: PDF, DOCX, XLSX]
  -> [Ingestion: Microsoft MarkItDown -> Markdown có cấu trúc]
    -> [Chunker & Table Extractor -> SQLite / FAISS / BM25]

Pipeline xử lý truy vấn online (mỗi lượt hỏi-đáp):
[Web UI]
  -> [FastAPI Orchestrator]
    -> [Context-Aware Query Rewriter]
      -> [Semantic Parser]  --(loi/conf thap)-->  [Regex Fallback]
                |                                        |
                +-------------------+-------------------+
                                    v
                          [Router: Intent Classification]
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
   intent = lookup           intent = policy              intent = OOD
        v                           v                           v
[Structured Lookup:        [Hybrid Retrieval]           [OOD Guardrail:
 SQLite/JSON]                    |                        tu choi an toan]
                          [Metadata Pre-filter]
                                    |
                         +----------+----------+
                         v                     v
                   [BM25 Index]          [FAISS Index]
                         +----------+----------+
                                    v
                             [RRF Fusion]
                                    v
                        [Cross-Encoder Reranker]
        |                           |                           |
        +---------------------------+---------------------------+
                                    v
                  [Generation Layer: LLM + Citation Enforcer]
                                    v
                      +-------------+-------------+
                      v                           v
        [Structured Logging: JSONL]   [Web UI hien thi cau tra loi]

Ba nguyên tắc thiết kế xuyên suốt kiến trúc:
Always Runnable: tại mọi thời điểm phát triển, nhánh chính (main) luôn chạy được End-to-End, không có tầng nào ở trạng thái "gãy" hoàn toàn.
Fallback Protection: mọi module nâng cao (Semantic Parser, Reranker, FAISS) đều có phương án dự phòng (Regex, BM25-only) khi lỗi xảy ra; kết quả từ Regex Fallback vẫn đi qua đúng Router như Semantic Parser, không có đường tắt riêng.
Interface Contracts: các tầng giao tiếp với nhau qua schema JSON chuẩn hóa (xem mục 2.2), không phụ thuộc trực tiếp vào cách hiện thực nội bộ của nhau.

2.2. Mô tả dataflow (luồng dữ liệu)
Luồng dữ liệu của hệ thống được chuẩn hóa thành các bước tuần tự sau, tính từ thời điểm chuẩn bị dữ liệu offline, qua khi người dùng gửi câu hỏi trên giao diện Web, đến khi nhận được câu trả lời cuối cùng:
Bước
Mô tả xử lý
Input → Output
Tiền xử lý (Offline)
Microsoft MarkItDown đọc các tệp định dạng hỗn hợp (PDF quy chế, biểu mẫu DOCX, bảng học phí XLSX), chuyển đổi thành Markdown bảo toàn bảng và tiêu đề. Chunker cắt chunk và Table Extractor đưa dữ liệu vào CSDL
Raw Files → Clean Markdown Chunks & Structured Tables
Bước 0
Người dùng nhập câu hỏi trên Web UI
Web UI → FastAPI Orchestrator
Bước 1
Context-Aware Query Rewriter kiểm tra lịch sử hội thoại, viết lại câu hỏi tỉnh lược thành câu hỏi đầy đủ ngữ nghĩa
original_query + history → rewritten_query
Bước 2
Semantic Parser chuyển rewritten_query thành structured query (Contract 3: intent, slots, confidence) bằng LLM structured output; nếu confidence thấp/LLM lỗi, hạ cấp (fallback) về Regex Fallback
rewritten_query → {intent, slots, confidence, parser_method, fallback_used}
Bước 2.5
Router (Intent Classification) nhận kết quả từ Semantic Parser hoặc Regex Fallback (bất kể nguồn nào), quyết định 1 trong 3 nhánh xử lý dựa trên trường intent
{intent, slots, ...} → điều hướng Path 1 / Path 2 / Path 3
Bước 3a (Path 1)
Nếu intent = tra cứu số liệu (vd. tuition_lookup): Router định tuyến sang Structured Lookup, truy vấn trực tiếp SQLite/JSON theo slots
structured query → kết quả số liệu chính xác 100%
Bước 3b (Path 2)
Nếu intent = giải thích chính sách: Router định tuyến sang Hybrid Retrieval — lọc cứng theo metadata (cohort/effective_date) trước, sau đó BM25 + FAISS chạy song song, hợp nhất bằng RRF, xếp hạng lại bằng Cross-Encoder Reranker (Top 50 → Top 5)
structured query → Top-5 đoạn văn bản liên quan nhất (Contract 2)
Bước 3c (Path 3)
Nếu intent = OOD (cả Semantic Parser lẫn Regex Fallback đều không xác định được intent hợp lệ): Router định tuyến sang OOD Guardrail, trả về từ chối an toàn
structured query → thông báo từ chối an toàn
Bước 4
Generation Layer nhận context (kết quả bước 3a/3b/3c), sinh câu trả lời kèm citation; Guardrail kiểm tra OOD và Faithfulness trước khi trả về
context + câu hỏi → câu trả lời + citation
Bước 5
Kết quả trả về Web UI hiển thị cho người dùng; toàn bộ 7 trường (original_query, rewritten_query, parsed_query, retrieved_docs, reranked_docs, final_context, citations) được ghi vào Structured Log (JSONL)
câu trả lời → người dùng; đồng thời ghi log phục vụ đánh giá


Ví dụ minh họa luồng dữ liệu thực tế
Giả sử người dùng đã hỏi trước đó "Học phí ngành AI năm nay bao nhiêu?" và tiếp tục hỏi "Còn năm 2027 thì sao?":
Query Rewriter nhận câu hỏi tỉnh lược "Còn năm 2027 thì sao?" cùng lịch sử hội thoại, viết lại thành: "Học phí ngành AI năm 2027 là bao nhiêu?"
Semantic Parser chuyển câu hỏi đã viết lại thành structured query theo Contract 3.
Router nhận structured query, thấy intent = tuition_lookup (tra cứu số liệu) nên định tuyến sang Structured Lookup thay vì Hybrid Retrieval, truy vấn trực tiếp CSDL SQLite (đã được trích xuất từ bảng học phí chuẩn hóa qua MarkItDown) theo slots {program: AI, cohort: 2027}.
Generation Layer nhận kết quả tra cứu, sinh câu trả lời kèm trích dẫn nguồn quyết định học phí tương ứng.
Toàn bộ 7 trường của lượt hỏi-đáp (original_query, rewritten_query, parsed_query, retrieved_docs, reranked_docs, final_context, citations) được ghi vào Structured Log.
Hợp đồng giao tiếp dữ liệu giữa các tầng (Interface Contracts)
Contract 1 — Schema tài liệu (Ingestion Layer → Retrieval Layer, Parsing Layer):
{
  "doc_id": "tuition_ai_2026_001",
  "title": "Quy định học phí chuyên ngành Trí tuệ Nhân tạo năm 2026",
  "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo nộp mức học phí theo tín chỉ...",
  "source": "Quyết định số 123/QĐ-ĐHFPT",
  "effective_date": "2026-01-01",
  "applies_to_cohort": ["2026"],
  "doc_type": "tuition",
  "structured_payload": {
    "program": "AI", "cohort": "2026",
    "tuition_per_credit": 1250000, "currency": "VND"
  }
}

Contract 2 — Output của tầng Retrieval (Retrieval Layer → Generation Layer):
[{
  "doc_id": "tuition_ai_2026_001",
  "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo...",
  "score": 0.892,
  "retrieval_strategy": "hybrid_rrf_reranked",
  "metadata": { "effective_date": "2026-01-01", "applies_to_cohort": ["2026"], "doc_type": "tuition" }
}]

Contract 3 — Output của tầng Semantic Parsing / Regex Fallback (→ Router → Structured Lookup / Retrieval):
{
  "intent": "tuition_lookup",
  "slots": { "program": "AI", "cohort": "2027", "metric": "tuition_per_credit" },
  "confidence": 0.94,
  "parser_method": "llm_structured_output",
  "fallback_used": false
}

Việc chuẩn hóa dataflow bằng ba hợp đồng JSON tường minh cho phép từng thành phần được kiểm thử độc lập (unit test theo schema) và cho phép nhóm phát triển song song mà không xung đột giao diện. Đặc biệt, vì Semantic Parser và Regex Fallback cùng trả về đúng schema của Contract 3, Router có thể xử lý cả hai nguồn đầu vào theo cùng một logic duy nhất.

2.3. Tính năng của từng thành phần kiến trúc
Bảng dưới đây tổng hợp chức năng cụ thể, mô tả tính năng và công nghệ sử dụng của từng thành phần trong kiến trúc, được tổng hợp từ toàn bộ các module đã trình bày ở mục 2.1 và 2.2:
Thành phần
Chức năng chính
Mô tả tính năng
Công nghệ sử dụng
Document Ingestion & Parsing
Đọc & chuẩn hóa tài liệu đa định dạng
Chuyển đổi toàn diện các tệp PDF, Word (.docx), Excel (.xlsx) sang văn bản Markdown sạch, giữ nguyên cấu trúc bảng biểu và tiêu đề
Microsoft MarkItDown
Query Rewriter
Context-Aware Rewriting
Phân giải tỉnh lược & đồng tham chiếu trong hội thoại đa lượt (3–5 lượt gần nhất)
LLM prompt-based rewriting
Semantic Parser
NL → Structured Query
Sinh intent + slots có schema (Contract 3), tính confidence, tự hạ cấp về Regex khi thất bại
LLM structured output / function calling
Regex Fallback
Phương án dự phòng
Trích xuất intent/slots bằng luật khi Semantic Parser lỗi hoặc confidence thấp; kết quả vẫn được đưa vào Router như bình thường
Regex / rule-based extraction
Router (Intent Classification)
Định tuyến theo intent
Thành phần duy nhất ra quyết định rẽ nhánh Path 1/2/3 dựa trên intent nhận từ Semantic Parser hoặc Regex Fallback, tránh mọi đường tắt bỏ qua bước phân loại
Rule-based routing trên trường intent
Metadata Pre-filter
Lọc cứng siêu dữ liệu
Loại bỏ tài liệu sai cohort/hết hiệu lực TRƯỚC khi truy xuất, giảm chi phí tính toán cho cả BM25 lẫn FAISS và tránh lấy nhầm văn bản cũ
Rule-based filter trên effective_date, cohort
BM25 Index
Keyword Retrieval
Tìm kiếm theo từ khóa chính xác (mã ngành, tên quy chế); tham số k1, b được tinh chỉnh
Rank-BM25 + tokenizer tiếng Việt
FAISS Index
Dense/Semantic Retrieval
Tìm kiếm theo độ tương đồng ngữ nghĩa véc-tơ, hỗ trợ diễn đạt khác nhau của cùng một ý
FAISS + multilingual-e5 embedding
RRF Fusion
Kết hợp kết quả
Hợp nhất danh sách kết quả từ BM25 và FAISS (đã lọc metadata) theo Reciprocal Rank Fusion, tăng độ phủ (recall)
Thuật toán RRF
Cross-Encoder Reranker
Xếp hạng lại
Chấm điểm lại Top 50 kết quả để đưa đoạn văn bản chính xác nhất vào Top 5
bge-reranker
Structured Lookup
Tra cứu số liệu
Truy vấn trực tiếp số liệu học phí/tín chỉ từ CSDL có cấu trúc, loại bỏ hoàn toàn ảo giác số liệu
SQLite/JSON query engine
Generation & Guardrail
Sinh câu trả lời an toàn
Sinh câu trả lời kèm trích dẫn nguồn; phát hiện & từ chối câu hỏi ngoài phạm vi (OOD); chống ảo giác bằng prompt nghiêm ngặt
LLM + prompt engineering + citation enforcement
Structured Logging
Quan sát & đánh giá
Ghi nhận đầy đủ 7 trường của một lượt hỏi-đáp phục vụ phân tích lỗi và đánh giá thực nghiệm
JSONL logger


Nhờ việc phân tách rõ chức năng của từng thành phần, hệ thống có thể đánh giá đóng góp độc lập của mỗi module thông qua ma trận Ablation Study (so sánh 6 cấu hình pipeline từ BM25 Baseline đến Full Pipeline + Semantic Parsing Routing), đồng thời cho phép xác định chính xác nguyên nhân lỗi (do Ingestion/Parser, do Retrieval, do Semantic Parser, hay do Generation) trong quá trình phân tích lỗi ở giai đoạn đánh giá cuối kỳ.



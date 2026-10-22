PHẦN 2: ĐỀ XUẤT KIẾN TRÚC HỆ THỐNG
Hệ thống Hybrid RAG + Semantic Parsing Chống Ảo Giác cho Hỏi Đáp Học Vụ
2.1. Mô tả kiến trúc tổng thể
2.1.1. Mô hình phân tầng
Kiến trúc hệ thống được thiết kế theo mô hình phân tầng (layered architecture) gồm 7 tầng xử lý, tách bạch rõ trách nhiệm giữa việc thu thập dữ liệu, hiểu ngữ nghĩa câu hỏi, truy xuất thông tin và sinh câu trả lời. Việc phân tầng này giúp mỗi thành phần có thể phát triển, kiểm thử và đánh giá độc lập (theo nguyên tắc Named-Contribution Alignment), đồng thời cho phép cơ chế fallback khi một module nâng cao gặp lỗi.
2.1.2. Bảng tổng hợp 7 tầng kiến trúc
Tầng
Thành phần chính
Vai trò tổng quát
1. Ingestion Layer
Document Converter (Microsoft MarkItDown), Data Collector, Chunker, Metadata Tagger, Table Extractor
Thu thập văn bản quy chế/học phí đa định dạng (PDF, DOCX, XLSX), chuyển đổi và chuẩn hóa sang Markdown có cấu trúc nhờ MarkItDown, cắt chunk 400–500 tokens, gán metadata (effective_date, cohort, doc_type), tách dữ liệu bảng biểu sang SQLite/JSON
2. Context Layer
Context-Aware Query Rewriter
Phân giải câu hỏi tỉnh lược/đồng tham chiếu dựa trên 3–5 lượt hội thoại gần nhất trước khi đưa vào các tầng xử lý phía sau
3. Parsing/Routing Layer
Semantic Parser (Intent + Slot Filling), Regex Fallback, Router (Intent Classification)
Chuyển câu hỏi tự nhiên thành structured query (intent, slots, confidence); khi Semantic Parser lỗi/độ tin cậy thấp, hạ cấp về Regex Fallback. Cả hai cùng đổ kết quả vào Router — thành phần duy nhất ra quyết định định tuyến sang 1 trong 3 nhánh
4. Retrieval Layer
Metadata Pre-filter, BM25 Index, FAISS Dense Index, RRF Fusion, Cross-Encoder Reranker
Lọc cứng theo cohort/effective_date trước để thu hẹp tập tài liệu ứng viên, sau đó truy xuất song song theo cả từ khóa (BM25) và ngữ nghĩa (FAISS), hợp nhất bằng RRF, xếp hạng lại bằng reranker
5. Structured Lookup Layer
SQLite/JSON Query Engine
Tra cứu trực tiếp số liệu học phí/tín chỉ theo slot đã parse, đảm bảo độ chính xác tuyệt đối cho câu hỏi định lượng
6. Generation Layer
LLM Answer Generator, Citation Enforcer, OOD Guardrail
Sinh câu trả lời tự nhiên kèm trích dẫn nguồn từ context đã truy xuất/tra cứu; từ chối trả lời an toàn khi câu hỏi ngoài phạm vi (OOD)
7. Presentation Layer
FastAPI Backend, Web UI (Streamlit)
Giao tiếp với người dùng cuối, hiển thị câu trả lời, trạng thái loading và trích dẫn; ghi log JSONL toàn bộ luồng xử lý

2.1.3. Sơ đồ khối tổng quát
Pipeline xử lý dữ liệu offline (chuẩn bị dữ liệu):
Pipeline xử lý truy vấn online (mỗi lượt hỏi-đáp):

2.1.4. Ba nguyên tắc thiết kế xuyên suốt
Nguyên tắc
Mô tả
Ví dụ áp dụng
Always Runnable
Tại mọi thời điểm phát triển, nhánh chính (main) luôn chạy được End-to-End, không có tầng nào ở trạng thái "gãy" hoàn toàn
Regex Fallback đảm bảo hệ thống vẫn hoạt động khi LLM gặp sự cố
Fallback Protection
Mọi module nâng cao đều có phương án dự phòng; kết quả từ Fallback đi qua đúng Router như module chính, không có đường tắt riêng
Semantic Parser → Router ← Regex Fallback (cùng contract)
Interface Contracts
Các tầng giao tiếp qua schema JSON chuẩn hóa, không phụ thuộc vào cách hiện thực nội bộ
Contract 1, 2, 3 định nghĩa rõ input/output mỗi tầng

2.2. Mô tả luồng dữ liệu (Dataflow)
2.2.1. Luồng xử lý tổng quát
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
Router nhận kết quả từ Semantic Parser hoặc Regex Fallback (bất kể nguồn nào), quyết định 1 trong 3 nhánh xử lý dựa trên trường intent
{intent, slots, ...} → Path 1 / Path 2 / Path 3
Bước 3a (Path 1)
Nếu intent = tra cứu số liệu (vd. tuition_lookup): Router định tuyến sang Structured Lookup, truy vấn trực tiếp SQLite/JSON theo slots
structured query → kết quả số liệu chính xác 100%
Bước 3b (Path 2)
Nếu intent = giải thích chính sách: Router định tuyến sang Hybrid Retrieval — lọc cứng theo metadata (cohort/effective_date) trước, sau đó BM25 + FAISS chạy song song, hợp nhất bằng RRF, xếp hạng lại bằng Cross-Encoder Reranker (Top 50 → Top 5)
structured query → Top-5 đoạn văn bản liên quan nhất
Bước 3c (Path 3)
Nếu intent = OOD: Router định tuyến sang OOD Guardrail, trả về từ chối an toàn
structured query → thông báo từ chối an toàn
Bước 4
Generation Layer nhận context (kết quả bước 3a/3b/3c), sinh câu trả lời kèm citation; Guardrail kiểm tra OOD và Faithfulness trước khi trả về
context + câu hỏi → câu trả lời + citation
Bước 5
Kết quả trả về Web UI; toàn bộ 7 trường được ghi vào Structured Log (JSONL)
câu trả lời → người dùng; đồng thời ghi log

2.2.2. Ví dụ minh họa luồng dữ liệu thực tế
Giả định: Người dùng đã hỏi trước đó "Học phí ngành AI năm nay bao nhiêu?" và tiếp tục hỏi "Còn năm 2027 thì sao?"
Giai đoạn
Xử lý
Chi tiết
Query Rewriting
Bước 1
Query Rewriter nhận câu hỏi tỉnh lược "Còn năm 2027 thì sao?" cùng lịch sử hội thoại, viết lại thành: "Học phí ngành AI năm 2027 là bao nhiêu?"
Semantic Parsing
Bước 2
Parser chuyển thành: {intent: "tuition_lookup", slots: {program: "AI", cohort: "2027"}}
Routing
Bước 2.5
Router thấy intent = tuition_lookup → định tuyến sang Path 1
Structured Lookup
Bước 3a
Truy vấn SQLite/JSON theo slots {program: AI, cohort: 2027} → lấy kết quả chính xác
Generation
Bước 4
Sinh câu trả lời: "Theo Quyết định số XXX, học phí ngành AI khóa 2027 là X VNĐ/tín chỉ..."
Logging
Bước 5
Ghi 7 trường: original_query, rewritten_query, parsed_query, retrieved_docs, reranked_docs, final_context, citations

2.2.3. Hợp đồng giao tiếp dữ liệu giữa các tầng (Interface Contracts)
Việc chuẩn hóa dataflow bằng ba hợp đồng JSON tường minh cho phép từng thành phần được kiểm thử độc lập (unit test theo schema) và cho phép nhóm phát triển song song mà không xung đột giao diện.
Contract 1 — Schema tài liệu (Ingestion Layer → Retrieval Layer, Parsing Layer):
{
  "doc_id": "tuition_ai_2026_001",
  "title": "Quy định học phí chuyên ngành Trí tuệ Nhân tạo năm 2026",
  "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo nộp mức học phí theo tín chỉ...",
  "source": "Quết định số 123/QĐ-ĐHFPT",
  "effective_date": "2026-01-01",
  "applies_to_cohort": ["2026"],
  "doc_type": "tuition",
  "structured_payload": {
    "program": "AI",
    "cohort": "2026",
    "tuition_per_credit": 1250000,
    "currency": "VND"
  }
}
Contract 2 — Output của tầng Retrieval (Retrieval Layer → Generation Layer):
[
  {
    "doc_id": "tuition_ai_2026_001",
    "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo...",
    "score": 0.892,
    "retrieval_strategy": "hybrid_rrf_reranked",
    "metadata": {
      "effective_date": "2026-01-01",
      "applies_to_cohort": ["2026"],
      "doc_type": "tuition"
    }
  }
]
Contract 3 — Output của tầng Semantic Parsing / Regex Fallback (→ Router → Structured Lookup / Retrieval):
{
  "intent": "tuition_lookup",
  "slots": {
    "program": "AI",
    "cohort": "2027",
    "metric": "tuition_per_credit"
  },
  "confidence": 0.94,
  "parser_method": "llm_structured_output",
  "fallback_used": false
}
2.3. Tính năng của từng thành phần kiến trúc
2.3.1. Bảng tổng hợp chức năng chi tiết
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
Router
Định tuyến theo intent
Thành phần DUY NHẤT ra quyết định rẽ nhánh Path 1/2/3 dựa trên intent nhận từ Semantic Parser hoặc Regex Fallback, tránh mọi đường tắt
Rule-based routing trên trường intent
Metadata Pre-filter
Lọc cứng siêu dữ liệu
Loại bỏ tài liệu sai cohort/hết hiệu lực TRƯỚC khi truy xuất, giảm chi phí tính toán
Rule-based filter trên effective_date, cohort
BM25 Index
Keyword Retrieval
Tìm kiếm theo từ khóa chính xác (mã ngành, tên quy chế)
Rank-BM25 + tokenizer tiếng Việt
FAISS Index
Dense/Semantic Retrieval
Tìm kiếm theo độ tương đồng ngữ nghĩa véc-tơ, hỗ trợ diễn đạt khác nhau
FAISS + multilingual-e5 embedding
RRF Fusion
Kết hợp kết quả
Hợp nhất danh sách kết quả từ BM25 và FAISS theo Reciprocal Rank Fusion
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
Sinh câu trả lời kèm trích dẫn nguồn; phát hiện & từ chối OOD; chống ảo giác bằng prompt nghiêm ngặt
LLM + prompt engineering + citation enforcement
Structured Logging
Quan sát & đánh giá
Ghi nhận đầy đủ 7 trường của một lượt hỏi-đáp phục vụ phân tích lỗi
JSONL logger

2.3.2. Ma trận Ablation Study
Hệ thống cho phép đánh giá đóng góp độc lập của mỗi module thông qua ma trận so sánh 6 cấu hình pipeline:
Cấu hình
BM25
FAISS
Metadata Filter
RRF
Reranker
Semantic Parsing
Mục tiêu đánh giá
A1: Naive RAG
✓
-
-
-
-
-
Baseline từ khóa
A2: Dense-only
-
✓
-
-
-
-
Baseline ngữ nghĩa
A3: Hybrid BM25+FAISS
✓
✓
-
-
-
-
Giá trị của hybrid
A4: + RRF + Reranker
✓
✓
-
✓
✓
-
Giá trị của reranking
A5: + Metadata Filter
✓
✓
✓
✓
✓
-
Giá trị của cohort filter
A6: Full Pipeline
✓
✓
✓
✓
✓
✓
Toàn bộ hệ thống

2.4. Giải thích chi tiết Microsoft MarkItDown
2.4.1. Tổng quan về Microsoft MarkItDown
Microsoft MarkItDown là công cụ mã nguồn mở của Microsoft được phát triển để chuyển đổi các định dạng tài liệu phổ biến (PDF, DOCX, XLSX, PPTX, v.v.) sang định dạng Markdown có cấu trúc. Trong hệ thống đề xuất, MarkItDown đóng vai trò là thành phần cốt lõi của Ingestion Layer, đảm bảo rằng dữ liệu từ nhiều nguồn định dạng khác nhau được chuẩn hóa thành một định dạng thống nhất trước khi đi vào các tầng xử lý phía sau.
Đặc điểm nổi bật của MarkItDown:
Đặc điểm
Mô tả
Lợi ích cho hệ thống
Hỗ trợ đa định dạng
PDF, DOCX, XLSX, PPTX, EPUB, Images (OCR)
Xử lý mọi loại tài liệu quy chế của trường đại học
Bảo toàn cấu trúc bảng
Giữ nguyên cấu trúc dòng - cột trong bảng biểu
Quan trọng cho dữ liệu học phí, điểm chuẩn
Giữ tiêu đề và phân cấp
Nhận diện Heading (H1-H6), list, quote
Duy trì cấu trúc văn bản quy chế
OCR tích hợp
Trích xuất văn bản từ ảnh scan, PDF ảnh
Xử lý tài liệu scan cũ
Miễn phí, mã nguồn mở
MIT License
Triển khai nội bộ không tốn chi phí
Đầu ra JSON/Markdown
Hỗ trợ output thô hoặc có cấu trúc
Dễ dàng tích hợp vào pipeline

2.4.2. Vai trò của MarkItDown trong kiến trúc hệ thống
Trong kiến trúc 7 tầng đề xuất, Microsoft MarkItDown là điểm đầu vào duy nhất cho dữ liệu tài liệu:

2.4.3. Quy trình xử lý chi tiết theo loại tài liệu
2.4.3.1. Xử lý tài liệu PDF (Quyết định, Thông báo)

2.4.3.2. Xử lý tài liệu DOCX (Quy chế đào tạo, Hướng dẫn)

2.4.3.3. Xử lý tài liệu XLSX (Bảng học phí, Điểm chuẩn, Mã ngành)
Đây là loại tài liệu quan trọng nhất và cũng phức tạp nhất trong hệ thống hỏi đáp học vụ:

2.4.4. So sánh MarkItDown với các công cụ thay thế
Tiêu chí
MarkItDown
pdfplumber
python-docx
pandas
Unstructured.io
Hỗ trợ đa định dạng
✅ PDF, DOCX, XLSX, PPTX
Chỉ PDF
Chỉ DOCX
Chỉ XLSX
✅ Đa dạng
Bảo toàn bảng
✅ Tốt
⚠️ Khá
❌ Không
✅ Tốt
✅ Tốt
OCR tích hợp
✅ Có
⚠️ Cần plugin
❌ Không
❌ Không
✅ Có
Đầu ra Markdown
✅ Native
⚠️ Cần convert
⚠️ Cần convert
⚠️ Cần convert
✅ Có
Mã nguồn mở
✅ MIT
✅ MIT
✅ MIT
✅ BSD
✅ Apache
Dễ cài đặt
✅ pip install
✅
✅
✅
⚠️ Phức tạp
Chi phí
Miễn phí
Miễn phí
Miễn phí
Miễn phí
⚠️ Cloud có phí

2.4.5. Cấu hình MarkItDown cho hệ thống hỏi đáp học vụ
# markitdown_config.yaml
markitdown:
  input_formats:
    - pdf
    - docx
    - xlsx
    - pptx
  
  pdf_options:
    extract_images: true
    ocr_enabled: true
    ocr_languages: ["vie", "eng"]
    preserve_layout: true
  
  docx_options:
    extract_styles: true
    preserve_headings: true
    preserve_tables: true
  
  xlsx_options:
    extract_all_sheets: true
    detect_header_row: true
    preserve_number_format: true
  
  output:
    format: "markdown"
    include_front_matter: true
    table_format: "markdown"
2.4.6. Luồng dữ liệu từ MarkItDown đến các tầng tiếp theo

2.4.7. Tích hợp MarkItDown vào pipeline CI/CD
# ingestion_pipeline.py
from markitdown import MarkItDown
import json
from pathlib import Path

class DocumentIngestionPipeline:
    def __init__(self, config):
        self.markitdown = MarkItDown()
        self.config = config
        self.chunker = Chunker(max_tokens=500, overlap=50)
        self.metadata_tagger = MetadataTagger()
        self.table_extractor = TableExtractor()
    
    def process_document(self, file_path: Path):
        """Xử lý một tài liệu đơn lẻ"""
        
        # 1. Convert bằng MarkItDown
        result = self.markitdown.convert(str(file_path))
        markdown_content = result.text_content
        
        # 2. Phát hiện loại tài liệu
        doc_type = self._detect_doc_type(file_path, result)
        
        if doc_type == "tabular":
            # 2a. Trích xuất bảng biểu
            tables = self.table_extractor.extract(result)
            structured_data = self._normalize_tables(tables)
            return {"type": "tabular", "data": structured_data}
        else:
            # 2b. Chunk và tag metadata
            chunks = self.chunker.chunk(markdown_content)
            metadata = self.metadata_tagger.tag(result, file_path)
            
            return {
                "type": "text",
                "chunks": chunks,
                "metadata": metadata
            }
    
    def batch_process(self, input_dir: Path, output_dir: Path):
        """Xử lý hàng loạt tài liệu"""
        for file_path in input_dir.glob("**/*"):
            if file_path.suffix.lower() in ['.pdf', '.docx', '.xlsx', '.pptx']:
                result = self.process_document(file_path)
                self._save_result(result, output_dir / file_path.stem)
2.5. Kết luận phần kiến trúc
Phần kiến trúc hệ thống trình bày ở trên đã xác lập một framework hoàn chỉnh với các đặc điểm:
Tính module hóa: 7 tầng xử lý tách biệt, có thể phát triển và kiểm thử độc lập
Cơ chế Fallback Protection: Đảm bảo hệ thống luôn hoạt động ngay cả khi module nâng cao gặp lỗi
Chuẩn hóa giao diện: 3 Interface Contracts (JSON Schema) đảm bảo tính nhất quán dữ liệu
Xử lý đa dạng dữ liệu: MarkItDown đóng vai trò gateway thống nhất cho mọi định dạng đầu vào
Đánh giá phân rã: Ma trận Ablation 6 cấu hình cho phép đo lường đóng góp từng module
Hệ thống được thiết kế theo nguyên tắc Always Runnable, đảm bảo rằng tại mọi thời điểm phát triển, nhánh chính luôn chạy được End-to-End từ Query Input đến Answer Output.
Báo cáo này là phần 2 của đề tài: "Hệ thống Hybrid RAG + Semantic Parsing chống ảo giác cho hỏi đáp học vụ tiếng Việt nhận biết ngữ cảnh"



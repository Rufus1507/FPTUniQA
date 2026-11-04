# BÁO CÁO THIẾT KẾ KIẾN TRÚC VÀ ĐẶC TẢ KỸ THUẬT DÒNG CHẢY HỆ THỐNG
## (SYSTEM ARCHITECTURE & PIPELINE TECHNICAL SPECIFICATION REPORT)
**Hệ thống:** FPTUniQA — Hệ thống Hỏi đáp Quy chế Đào tạo và Biểu phí Đại học FPT  
**Phiên bản:** 2.0 (Kiến trúc Edge Hybrid RAG + Semantic Routing + Academic Knowledge Graph)  
**Thời gian hoàn thiện:** Tháng 11/2026  
**Môi trường thực thi:** Local Edge AI (Ollama `qwen2.5:3b-instruct`, `intfloat/multilingual-e5-base`, Python 3.10, On-premise 16GB RAM)

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG TOÀN PHẦN (END-TO-END ARCHITECTURE)

FPTUniQA là hệ thống hỏi đáp học vụ tự chủ (on-premise), được thiết kế để giải quyết bài toán giao thoa giữa dữ liệu văn bản quy chế mở (Unstructured Text) và dữ liệu học phí / lộ trình đào tạo có cấu trúc chặt chẽ (Structured Data & Knowledge Graph). 

Khác với các hệ thống RAG phẳng truyền thống (như URAG hay R2GQA) vốn ép mọi câu hỏi phải chạy qua mô hình ngôn ngữ lớn dẫn đến ảo giác số học và độ trễ cao, FPTUniQA triển khai kiến trúc **Đa tầng thích ứng (Multi-Tier Adaptive Pipeline)** phân luồng thông minh ngay từ đầu vào.

### 1.1. Sơ đồ Dòng Chảy Dữ Liệu Tổng Thể

```
[Người dùng gửi câu hỏi / User Message]
                   │
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 0: SAFETY PRE-GATE & NEAR-OOD (< 5ms)                             │
│ - Quét Lexicon từ điển tổ chức ngoài (data/dictionary/external_orgs)    │
│ - Regex phát hiện Prompt Injection, Gian lận thi PE/EOS, Du học        │
│ └─► [NẾU VI PHẠM] ──► Từ chối an toàn ngay lập tức (Bảo vệ LLM)        │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ (An toàn)
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1: SESSION MEMORY & QUERY REWRITING                               │
│ - SessionManager: Cửa sổ trượt (Sliding Window 5 lượt, TTL 3600s)      │
│ - Chuẩn hóa Teencode: ktx -> ký túc xá, hl -> Hòa Lạc, củ -> triệu VNĐ  │
│ - Self-Containedness Gate: Kiểm tra câu hỏi có tự chứa đủ ngữ cảnh?   │
│ - Topic Switch Detection: Phát hiện chuyển chủ đề để ngắt ngữ cảnh cũ  │
│ - Rewriter Engine: Rule Fast-Path -> Local LLM Rewriter -> Fallback    │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ Câu hỏi độc lập đầy đủ ngữ cảnh (Standalone Query)
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2: SEMANTIC PARSER & NORMALIZATION ENGINE                         │
│ - Fast-Path Regex Parser: Bắt câu hỏi số liệu cơ bản (< 2ms)          │
│ - Small LLM Parser: Ollama Qwen2.5:3B xuất Constrained JSON (Max 320t) │
│ - EntityNormalizer: Longest Match First, NFKC N1, Accent-Insensitive   │
│ └─► Xuất đối tượng chuẩn Contract 3: ParsedQuery(intent, slots, conf)   │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 3: INTENT ROUTER & PHÂN CẤP PHỨC TẠP (LEVELS 1 - 10)              │
│ - Kiểm tra ngưỡng tin cậy: confidence < 0.5 ──► Route 'uncertain'      │
│ - Intent == OOD ──► Route 'ood' (Từ chối lịch sự, Level 10)           │
│ - Thiếu slot cốt lõi (chỉ có ngành, thiếu khóa) ──► 'clarification'   │
│ - Đủ slot biểu phí / Điểm F / Phí KTX ──► 'structured_lookup' (SSOT)   │
│ - Tra cứu quy chế, OJT, tốt nghiệp ──► 'rag_pipeline' (Hybrid Search) │
└─────────┬──────────────────────────┬─────────────────────────┬─────────┘
          │                          │                         │
 [clarification / ood]      [structured_lookup]          [rag_pipeline]
          │                          │                         │
          ▼                          ▼                         ▼
   (Hỏi làm rõ /            ┌──────────────────┐      ┌─────────────────────────┐
    Từ chối mẫu)            │ TẦNG 6A: CKB     │      │ TẦNG 4: HYBRID          │
                            │ DETERMINISTIC    │      │ RETRIEVAL (BM25 + FAISS)│
                            │ SSOT RENDERER    │      │ - BM25 (ViTokenizer)    │
                            │ (0% Hallucination│      │ - FAISS (e5-base 768d)  │
                            │  100% Faith)     │      │ - RRF Fusion (k=60)     │
                            └────────┬─────────┘      │ - Soft Metadata Filter  │
                                     │                └────────────┬────────────┘
                                     │                             │ Top-k Chunks
                                     │                             ▼
                                     │                ┌─────────────────────────┐
                                     │                │ TẦNG 5: ACADEMIC        │
                                     │                │ KNOWLEDGE GRAPH         │
                                     │                │ - Topo-sort chuỗi môn   │
                                     │                │ - Lộ trình OJT K17-K22  │
                                     │                │ - So sánh khung CTĐT    │
                                     │                └────────────┬────────────┘
                                     │                             │ Bơm Context Graph
                                     │                             ▼
                                     │                ┌─────────────────────────┐
                                     │                │ TẦNG 6B: TEXT RAG       │
                                     │                │ LLM GENERATION          │
                                     │                │ - Qwen2.5:3B on-premise │
                                     │                │ - System Prompt cấm bịa │
                                     │                └────────────┬────────────┘
                                     │                             │
                                     ▼                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 7: GUARDRAILS, TRÍCH XUẤT CĂN CỨ & PHÁP LÝ (OUTPUT VALIDATION)    │
│ - Quét ảo giác số liệu: ungrounded_numbers detector                   │
│ - Trích xuất Citation: Điều khoản, Quyết định ban hành, Khóa áp dụng   │
│ - Tự động đính kèm cảnh báo: "Xác nhận với Phòng Đào tạo trên FAP"     │
│ - Lưu vết SessionManager (turn_index, timestamps, route_chosen)       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
                   [Phản hồi hoàn chỉnh tới Người dùng]
```

---

## 2. CHI TIẾT CÁC TẦNG VÀ CƠ CHẾ KỸ THUẬT TRONG PIPELINE

### Tầng 0: Safety Pre-gate & Near-OOD Filter
- **Tệp nguồn:** [`src/FPTUniQA/query/safety_gate.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/safety_gate.py) và từ điển [`data/dictionary/external_orgs.json`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/data/dictionary/external_orgs.json).
- **Mục tiêu:** Chặn trước các câu hỏi độc hại, tấn công và câu hỏi ngoài miền cận biên (Near-OOD) với độ trễ cực thấp (< 5ms), tuyệt đối không để các câu hỏi này đi vào mô hình ngôn ngữ lớn (tiết kiệm 100% thời gian xử lý LLM).
- **Cơ chế hoạt động:**
  1. *Quét từ điển tổ chức ngoài:* Đối chiếu với danh sách các trường đại học khác (Bách Khoa, Kinh tế Quốc dân, Quốc gia Hà Nội, Harvard, MIT...) và học bổng ngoài. Nếu người dùng hỏi quy chế của trường khác, hệ thống chặn ngay và thông báo: *"Hệ thống chỉ hỗ trợ giải đáp thông tin quy chế và biểu phí của Đại học FPT"*.
  2. *Bộ lọc vi phạm học vụ & gian lận:* Sử dụng biểu thức chính quy nhận diện hành vi gian lận thi PE/EOS, thi hộ, làm giả chứng chỉ tiếng Anh (IELTS/TOEIC/VSTEP), mua bán đồ án tốt nghiệp.
  3. *Chống tấn công Prompt Injection:* Phát hiện các mẫu câu cố tình bẻ khóa chỉ dẫn hệ thống (`ignore previous instructions`, `reveal system prompt`, `system token override`).

### Tầng 1: Session Memory & Conversational Query Rewriting
- **Tệp nguồn:** [`src/FPTUniQA/query/rewriting.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/rewriting.py) và `SessionManager` tại [`src/FPTUniQA/pipeline/rag_pipeline.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/pipeline/rag_pipeline.py#L25-L86).
- **Mục tiêu:** Tiếp nhận câu hỏi hiện tại và lịch sử hội thoại, giải quyết hiện tượng đồng tham chiếu (coreference) và tỉnh lược (ellipsis), chuyển đổi câu hỏi phụ thuộc thành một câu hỏi duy nhất, độc lập ngữ cảnh (Self-Contained Standalone Query).
- **Các cơ chế phòng vệ và tối ưu:**
  - *Circuit Breaker:* Bộ ngắt mạch bảo vệ `_rewriter_breaker` (ngưỡng lỗi 2 lần liên tiếp, tự động ngắt trong 30 giây để chuyển sang bộ luật fallback).
  - *Chuẩn hóa Teencode:* Hàm `_normalize_teencode()` chuyển nhanh các từ lóng: `ktx` $\to$ `ký túc xá`, `hl` $\to$ `Hòa Lạc`, `ct` $\to$ `Cần Thơ`, `qn` $\to$ `Quy Nhơn`, `củ` $\to$ `triệu đồng`, `đatn/kltn` $\to$ `đồ án tốt nghiệp`.
  - *Self-Containedness Gate:* Nếu câu hỏi đã tự chứa đủ thông tin (như có mã môn cụ thể, hoặc đủ cả Khóa + Ngành + Cơ sở), hệ thống khóa kế thừa, giữ nguyên câu hỏi gốc để chống ô nhiễm ngữ cảnh cũ (Context Decontamination).
  - *Topic Switch Detection:* Nếu người dùng chuyển đổi đề tài, hệ thống phát hiện và cắt đứt kế thừa.
  - *Ba mức viết lại:*
    1. Fast-Path theo luật kết hợp `EntityNormalizer` (0ms, 100% chính xác).
    2. Gọi mô hình LLM cục bộ (Rewriter Prompt với nhiệt độ thấp 0.1).
    3. Fallback sang bộ luật quy tắc nếu LLM gặp sự cố.

### Tầng 2: Semantic Parser & Normalization Engine
- **Tệp nguồn:** [`src/FPTUniQA/query/semantic_parser.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/semantic_parser.py) và [`src/FPTUniQA/normalization/engine.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/normalization/engine.py).
- **Mục tiêu:** Chuyển đổi câu hỏi ngôn ngữ tự nhiên thành đối tượng dữ liệu có cấu trúc chuẩn hóa `ParsedQuery` (Contract 3).
- **Cấu trúc Contract 3:**
  ```python
  class ParsedQuery(BaseModel):
      original_query: str
      normalized_query: str
      intent: str        # tuition_lookup | policy_lookup | course_lookup | graduation_lookup | OOD
      slots: Dict[str, Any] # program, cohort, campus, course_code, topic, target...
      confidence: float  # 0.0 -> 1.0
  ```
- **Cơ chế tối ưu hóa tốc độ (Fast-Path Parser):**
  - Trước khi gọi LLM, hàm `try_rule_fast_parse()` quét các mẫu câu hỏi số liệu/biểu phí rõ ràng. Nếu câu hỏi khớp mẫu, parser hoàn tất trong **< 2ms**, giúp giảm 27.9% độ trễ trung bình của toàn pipeline (từ 2,827ms xuống 2,038ms).
- **LLM Parser với Constrained JSON:**
  - Nếu câu hỏi phức tạp, gọi Ollama `qwen2.5:3b-instruct` với `format: "json"` và giới hạn token đầu ra nghiêm ngặt `max_output_tokens: 320`.
- **Động cơ chuẩn hóa thực thể học vụ (`EntityNormalizer`):**
  - Nạp 6 bộ từ điển miền: `majors.json`, `courses.json`, `cohorts.json`, `campuses.json`, `academic_terms.json`, `abbreviations.json`.
  - Thuật toán **Longest Match First**: Sắp xếp alias theo độ dài giảm dần, ưu tiên cụm từ dài trước để tránh xung đột từ ghép (ví dụ nhận diện "Kỹ thuật phần mềm" trước "phần mềm").
  - Chuẩn hóa Unicode **NFKC N1** và xử lý **Không dấu** (`remove_accents`): Giúp người dùng gõ không dấu vẫn nhận diện chính xác 100% thực thể.

### Tầng 3: Intent Router & Hierarchy Levels (Levels 1 - 10)
- **Tệp nguồn:** [`src/FPTUniQA/query/router.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/router.py).
- **Mục tiêu:** Điều phối luồng xử lý câu hỏi sang đúng nhánh tính toán tối ưu và gán nhãn cấp độ phức tạp truy vấn từ Level 1 đến Level 10.
- **Bảng ma trận định tuyến (Routing Logic Matrix):**

| Tuyến đường (Route) | Điều kiện kích hoạt | Cơ chế xử lý tiếp theo | Cấp độ (Level) |
|---|---|---|:---:|
| `ood` | `intent == "OOD"` hoặc chứa `OOD_KEYWORDS` | Trả về thông báo từ chối lịch sự theo chuẩn mực sư phạm | Level 10 |
| `uncertain` | `confidence < 0.5` | Phản hồi yêu cầu người dùng diễn đạt rõ ràng hơn | Level 10 |
| `clarification` | `intent == "tuition_lookup"` nhưng thiếu slot cốt lõi (chỉ có ngành, thiếu khóa tuyển sinh hoặc cơ sở) | Sinh câu hỏi làm rõ có định hướng (ví dụ: *"Bạn muốn tra cứu ngành AI cho khóa nào?"*) | Level 4 |
| `structured_lookup` | Đủ Khóa + Ngành + Cơ sở; câu hỏi lệ phí chung; chính sách điểm F | Truy xuất trực tiếp bảng cấu trúc SSOT (CKB Engine), không qua LLM sinh | Level 1, 3 |
| `rag_pipeline` | Câu hỏi quy chế học vụ, điều kiện OJT, tốt nghiệp, đồ án | Kích hoạt bộ truy xuất lai ghép (Hybrid Retrieval) và Knowledge Graph | Level 2, 5, 6, 7, 8, 9 |

### Tầng 4: Hybrid Retrieval Engine (BM25 + FAISS + RRF + Soft Metadata Filter)
- **Tệp nguồn:** [`src/FPTUniQA/retrieval/`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/retrieval/).
- **Mục tiêu:** Truy xuất các đoạn văn bản quy chế chính xác nhất từ kho tài liệu học vụ.
- **Thành phần cốt lõi:**
  1. *Dense Vector Search (FAISS):* Mô hình `intfloat/multilingual-e5-base` (768 chiều), mã hóa câu hỏi với tiền tố `query: ` và tài liệu với `passage: `.
  2. *Sparse Keyword Search (BM25Okapi):* Tích hợp bộ tách từ tiếng Việt `pyvi.ViTokenizer`, đồng thời bảo toàn các cụm từ ghép chuyên môn (`ACADEMIC_COMPOUND_TERMS` như `môn_tiên_quyết`, `thực_tập_doanh_nghiệp`).
  3. *Reciprocal Rank Fusion (RRF, $k=60$):* Dung hợp điểm số từ Dense và Sparse theo công thức:
     $$RRF(d) = \frac{1}{60 + r_{dense}(d)} + \frac{1}{60 + r_{sparse}(d)}$$
  4. *Soft-filter Metadata:* Phân loại tài liệu theo Khóa (`cohort`) và Cơ sở (`campus`). Cấu chế Soft-filter ưu tiên trích xuất tài liệu trùng khớp khóa của sinh viên, nhưng giữ lại các tài liệu quy chế chung toàn trường (`cohort=None`), kèm cơ chế Graceful Fallback (nếu bộ lọc làm rỗng kết quả, tự động truy xuất lại không áp dụng bộ lọc).
  5. *Song song hóa ThreadPoolExecutor:* Chạy đồng thời BM25 và FAISS trên 2 luồng độc lập, giảm 42.8% thời gian truy xuất.

### Tầng 5: Academic Knowledge Graph (Graph RAG Engine)
- **Tệp nguồn:** [`src/FPTUniQA/graph/knowledge_graph.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/graph/knowledge_graph.py).
- **Mục tiêu:** Giải quyết các câu hỏi suy luận đa chặng (Multi-hop Reasoning) mà các hệ thống RAG phẳng hoàn toàn thất bại.
- **Năng lực chuyên biệt:**
  - *Topological Sort trên Cây Tiên quyết:* Duyệt đệ quy toàn bộ chuỗi môn học phụ thuộc (ví dụ muốn học `SWP391` phải qua `SWE201C/PRJ301` $\to$ qua `PRO192` $\to$ qua `PRF192`).
  - *Phân tầng Điều kiện OJT theo Khóa (Cohort-Aware):* Phân biệt rõ quy định 80 tín chỉ (K17–K18) và 90–100 tín chỉ (K19–K22).
  - *So sánh Khung Chương trình Đào tạo Liên ngành:* Trích xuất các môn cơ sở khối ngành chung và các môn chuyên ngành phân nhánh giữa KTPM, AI và ATTT.
  - *Context Injection:* Kết quả truy vấn từ đồ thị tri thức được định dạng chuẩn và bơm trực tiếp vào prompt ngữ cảnh của mô hình LLM.

### Tầng 6: Generation & Deterministic SSOT Engine
Hệ thống sử dụng hai cơ chế phát sinh lời giải đối lập tùy thuộc vào tính chất câu hỏi:
1. **Nhánh Deterministic CKB Engine (Cho dữ liệu số học):**
   - Áp dụng cho học phí, lệ phí bảng điểm, quy định điểm F.
   - Dữ liệu được trích xuất trực tiếp từ tệp JSON cấu trúc Single Source of Truth (SSOT).
   - Câu trả lời được render qua template định sẵn. **Tuyệt đối không để LLM tự diễn đạt lại số liệu**, bảo đảm **Faithfulness 100% và Hallucination 0.00%**.
2. **Nhánh Text RAG LLM Generator (Cho câu hỏi quy chế mở):**
   - Sử dụng mô hình cục bộ `qwen2.5:3b-instruct` kết hợp System Prompt kiểm soát chặt chẽ:
     *"Chỉ trả lời dựa trên ngữ cảnh được cung cấp. Nếu ngữ cảnh không có thông tin, hãy trả lời 'Tôi không tìm thấy tài liệu phù hợp'. Tuyệt đối không tự suy đoán số liệu."*

### Tầng 7: Guardrails, Hallucination Detector & Legal Disclaimer
- **Tệp nguồn:** [`src/FPTUniQA/generation/guardrails.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/generation/guardrails.py) và [`citation.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/generation/citation.py).
- **Mục tiêu:** Kiểm tra và bảo đảm tính hợp lệ pháp lý của câu trả lời trước khi gửi tới sinh viên.
- **Các bước xác thực:**
  1. *Ungrounded Numbers Detector:* Trích xuất toàn bộ các thực thể số học trong câu trả lời sinh ra. Nếu xuất hiện bất kỳ con số nào không có mặt trong đoạn văn bản ngữ cảnh, hệ thống đánh cờ cảnh báo `possible_hallucination = True`.
  2. *Trích dẫn nguồn căn cứ (Citations):* Tự động đính kèm mã văn bản (doc_id), tên quyết định ban hành và khóa áp dụng.
  3. *Cảnh báo Pháp lý Học vụ:* Mọi câu hỏi có hệ quả học vụ (học phí, điều kiện tốt nghiệp, cảnh báo) đều được bổ sung dòng khuyến nghị:
     *"Lưu ý: Sinh viên cần đối chiếu số tín chỉ tích lũy chính xác theo Khóa tuyển sinh trên hệ thống FAP và xác nhận với Phòng Đào tạo trước khi đăng ký."*

---

## 3. CƠ CHẾ XỬ LÝ HỘI THOẠI ĐA NGỮ CẢNH (MULTI-TURN CONTEXT)

Hệ thống quản lý ngữ cảnh hội thoại đa lượt qua 4 nguyên tắc kỹ thuật cốt lõi:

### 3.1. Kế thừa Thực thể Ngược (Reverse Turn Traversal)
Khi người dùng đặt câu hỏi tiếp nối, hệ thống duyệt lịch sử trò chuyện theo chiều ngược lại từ lượt gần nhất trở về trước (`reversed(history)`). Thực thể nào xuất hiện ở lượt gần nhất sẽ được ưu tiên cao nhất:
- Nếu lượt 1 người dùng hỏi ngành AI, lượt 2 đổi sang ngành ATTT, hệ thống sẽ chốt ngành ATTT cho lượt 3.

### 3.2. Giải quyết Đồng tham chiếu (Coreference Resolution)
Hệ thống sử dụng các mẫu đối sánh ngữ nghĩa và mô hình Rewriter để phân giải các đại từ chỉ định:
- *"môn này"*, *"môn đó"*, *"học phần này"* $\to$ Thay bằng mã môn học được lưu trong lịch sử: `Môn {hist_course}`.
- *"ngành này"*, *"ngành đó"* $\to$ Thay bằng tên ngành: `ngành {hist_program}`.
- *"ở đó"*, *"tại đó"*, *"cơ sở đó"* $\to$ Thay bằng phân hiệu: `tại phân hiệu {hist_campus}`.

### 3.3. Giải quyết Tỉnh lược (Ellipsis Resolution)
Khi người dùng chỉ đưa ra một phần thông tin:
- Câu hỏi: *"Thế còn K21?"* hoặc *"Ở Cần Thơ thì sao?"*.
- Hệ thống nhận diện đây là câu hỏi tỉnh lược (Continuation Query), tự động giữ nguyên chủ đề học vụ và tên ngành của lượt trước, chỉ hoán đổi slot khóa hoặc cơ sở mới vào.

### 3.4. Xử lý Đính chính và Phủ định (Correction & Negation Handling)
Khi người dùng đính chính lại thông tin:
- Ví dụ: *"Không, mình muốn hỏi khóa K21 cơ"* hoặc *"Mình nhầm, mình hỏi ngành An toàn thông tin"*.
- Hệ thống phát hiện cặp từ phủ định (`không`, `nhầm`, `ý mình là`) kết hợp với thực thể mới, lập tức ghi đè thực thể mới lên thực thể cũ trong ngữ cảnh câu hỏi trước đó.

### 3.5. Xử lý Phản hồi Làm rõ (Clarification Response)
Nếu ở lượt trước hệ thống hỏi làm rõ: *"Vui lòng cho biết bạn muốn tra cứu học phí ngành KTPM cho khóa nào?"*, và người dùng chỉ trả lời cụt lủn: *"Khóa 2026"* $\to$ Hệ thống nhận diện trạng thái `is_prev_clarification`, lập tức tổng hợp thành câu hỏi hoàn chỉnh: *"Học phí K2026 ngành Kỹ thuật phần mềm là bao nhiêu?"*.

---

## 4. CƠ CHẾ CẮT, THU HẸP VÀ LÀM SẠCH NGỮ CẢNH (CONTEXT TRIMMING)

Để hệ thống hoạt động ổn định trên phần cứng biên (Local PC, RAM 16GB) mà không bị tràn bộ nhớ hay suy giảm độ chính xác do nhiễu ngữ cảnh (Context Bleeding), các cơ chế kiểm soát cửa sổ được thiết lập:

### 4.1. Cửa Sổ Trượt (Sliding Window Trimming)
- Trong prompt gọi LLM Rewriter, hệ thống chỉ lấy tối đa **5 lượt gần nhất** (`recent_history = history[-5:]`). Các lượt hội thoại quá xa trong quá khứ bị loại bỏ khỏi ngữ cảnh prompt.

### 4.2. Cắt Ngắn Câu Trả Lời Trợ Lý (Assistant Truncation)
- Để tránh làm phình token context window của mô hình 3B, câu trả lời của trợ lý trong lịch sử được cắt ngắn tối đa **150 ký tự** (`short_a = a[:150] + "..."`). Điều này giúp LLM Rewriter nắm bắt được chủ đề trao đổi mà không tốn token cho các đoạn văn bản dài.

### 4.3. Giới Hạn Phiên (Session Max Turns Decay)
- Trong `SessionManager`, mỗi phiên hội thoại được giới hạn tối đa **10 lượt hỏi - đáp** (`max_turns = 10`). Khi lượt thứ 11 xuất hiện, lượt thứ 1 cũ nhất sẽ tự động bị giải phóng khỏi bộ nhớ RAM:
  ```python
  if len(self._sessions[session_id]) > self.max_turns:
      self._sessions[session_id] = self._sessions[session_id][-self.max_turns:]
  ```

### 4.4. Cơ Chế Tự Hủy Theo Thời Gian (Session Time-To-Live - TTL)
- Mỗi session được gắn kèm nhãn thời gian `timestamp`. Nếu khoảng cách giữa hai câu hỏi liên tiếp vượt quá **3,600 giây (60 phút)**, toàn bộ lịch sử phiên sẽ tự động bị xóa sổ (`clear(session_id)`). Phiên mới sẽ bắt đầu như một người dùng hoàn toàn mới.

### 4.5. Cơ Chế Khử Ô Nhiễm Ngữ Cảnh Tức Thì (Context Decontamination)
Hệ thống kích hoạt hai chốt chặn độc lập để ngắt kế thừa ngay lập tức:
1. **Chốt chặn Câu hỏi Tự Chứa (Self-Containedness Gate):** Nếu câu hỏi mới của sinh viên chứa đủ các thành phần độc lập (ví dụ có mã môn rõ ràng, hoặc câu hỏi thủ tục chung dài $\ge 8$ từ), hệ thống xác định người dùng không tham chiếu lượt trước và **tuyệt đối không ghép ngữ cảnh cũ**.
2. **Chốt chặn Chuyển Đổi Chủ Đề (Topic Switch Gate):** Hàm `detect_topic_switch()` phân loại chủ đề câu hỏi vào 8 nhóm: `discipline_warning`, `tuition`, `graduation`, `ojt_internship`, `exam_appeal`, `exam_regulations`, `scholarship`, `ood`. Nếu chủ đề câu mới khác hoàn toàn chủ đề câu cũ (ví dụ đang hỏi học phí chuyển sang hỏi quy chế cấm thi), hệ thống kích hoạt ngắt mạch và xử lý câu mới độc lập.

---

## 5. CƠ CHẾ XỬ LÝ TỪ ĐỒNG NGHĨA, VIẾT TẮT, TEENCODE VÀ THỰC THỂ

| Lớp Xử lý | Phạm vi & Tệp Nguồn | Kỹ thuật Thực thi Cụ thể |
|---|---|---|
| **1. Teencode & Từ lóng Sinh viên** | `_TEENCODE_MAP` trong `rewriting.py` | Biên dịch trước danh sách Regex Tuple. Thay thế từ lóng tức thời (0ms): `ktx` $\to$ ký túc xá, `hl` $\to$ Hòa Lạc, `bn` $\to$ bao nhiêu, `củ` $\to$ triệu đồng, `đc/dc` $\to$ được, `đatn/kltn` $\to$ đồ án tốt nghiệp. |
| **2. Cụm Từ Chuyên ngành Học vụ** | `ACADEMIC_COMPOUND_TERMS` trong `bm25.py` | Ghép nối gạch dưới các thuật ngữ cố định trước khi đưa vào BM25 (`môn_tiên_quyết`, `thực_tập_doanh_nghiệp`, `điểm_f`, `cảnh_báo_học_vụ`, `đồ_án_tốt_nghiệp`) để ngăn bộ tách từ phân rã thành các từ đơn mất nghĩa. |
| **3. Chuẩn hóa Thực thể Đa biến thể** | `EntityNormalizer` trong `normalization/engine.py` | Nạp 6 tệp từ điển miền JSON. Thuật toán **Longest Match First** ưu tiên so khớp cụm từ dài trước cụm từ ngắn. |
| **4. Đối sánh Không dấu (Diacritic-Insensitive)** | `remove_accents()` và chuẩn `NFKC N1` | Chuyển đổi ký tự Unicode tổ hợp về dạng tương thích chuẩn, hỗ trợ sinh viên gõ tiếng Việt không dấu (ví dụ: `hoc phi cntt o can tho` $\to$ nhận diện đúng ngành CNTT và phân hiệu Cần Thơ). |
| **5. Viết tắt Ngành & Khóa học** | `_post_process_rewritten()` | Chuẩn hóa regex biểu thức chính quy: `khoa 2026` $\to$ `K26`, `khoa 21` $\to$ `K21`, `cntt` $\to$ `CNTT`, `ktpm` $\to$ `KTPM`, `attt` $\to$ `ATTT`, `qtkd` $\to$ `QTKD`. |

---

## 6. CƠ CHẾ NHẬN DIỆN VÀ PHÒNG VỆ NGOÀI MIỀN (OOD LAYER)

Hệ thống triển khai mô hình **Phòng thủ Chiều sâu 3 Lớp (Three-Defense-Line)** đối với các truy vấn ngoài miền:

```
[Câu hỏi đến] ──► [Lớp 1: Safety Pre-gate] (<5ms)
                         │ (Nếu chứa tên trường khác / từ cấm) ──► TỪ CHỐI NGAY
                         ▼
                  [Lớp 2: Semantic Parser]
                         │ (Phân loại intent == "OOD")         ──► TỪ CHỐI AN TOÀN
                         ▼
                  [Lớp 3: Router & Confidence Guard]
                         │ (Quét OOD_KEYWORDS hoặc conf < 0.5) ──► TỪ CHỐI / LÀM RÕ
                         ▼
                  [Tiến vào luồng RAG nội bộ FPT]
```

- **Phân biệt OOD Cơ bản vs Cận miền (Near-OOD):**
  - *OOD Cơ bản:* Các câu hỏi về thời tiết, thể thao, nấu ăn, lập trình tổng quát $\to$ Được nhận diện dễ dàng qua `OOD_KEYWORDS` và phân luồng Semantic Parser (Đạt tỷ lệ từ chối **100.00%**).
  - *Cận miền (Near-OOD):* Các câu hỏi hỏi về quy chế/học phí nhưng trỏ tới các trường đại học khác (Bách Khoa Hà Nội, ĐH Quốc Gia, NEU, du học Nhật Bản...) $\to$ Được phòng thủ bởi `external_orgs.json` tại Pre-gate (Đạt tỷ lệ từ chối **90.00%** trên bộ kiểm thử 20 câu).
- **Phản hồi Chuẩn mực Sư phạm:** Hệ thống từ chối lịch sự, giải thích rõ phạm vi và hướng dẫn sinh viên kênh thông tin chính thức:
  *"Xin lỗi, câu hỏi của bạn nằm ngoài phạm vi tư vấn quy chế, tuyển sinh và đào tạo của Đại học FPT."*

---

## 7. CƠ CHẾ LƯU BỘ NHỚ CỦA HỆ THỐNG (MEMORY ARCHITECTURE)

Hệ thống có được trang bị cơ chế lưu bộ nhớ không? **Có, và được phân tầng thành 3 cấp độ bộ nhớ chuyên biệt:**

### 7.1. Bộ Nhớ Phiên Ngắn Hạn (Short-Term Working Memory)
- **Đại diện:** Lớp `SessionManager` trong `src/FPTUniQA/pipeline/rag_pipeline.py`.
- **Cơ chế:** Lưu trữ trực tiếp trên RAM dưới dạng cấu trúc bảng băm đa cấp:
  ```python
  self._sessions: Dict[str, List[Dict[str, Any]]] # session_id -> List các turn
  self._timestamps: Dict[str, float]              # session_id -> thời điểm gọi cuối
  ```
- **Thông tin lưu trữ trong mỗi lượt:** `turn_index`, `query` gốc, `rewritten_query`, `answer`, `parsed_query` (intent & slots), `route_chosen`, `topic_switch_detected`.
- **Đặc tính:** Vận hành nhanh (<0.1ms), có cơ chế tự dọn dẹp (Decay max 10 turns và TTL 3600s).

### 7.2. Bộ Nhớ Đệm Tính Toán & Dữ Liệu (Query & Model Caching)
- **Cache Biểu phí & Tín chỉ:** Biến toàn cục `_FEES_CONFIG_CACHE`, `_STRUCTURED_DATA_CACHE`, `_STRUCTURED_CREDITS_CACHE` nạp dữ liệu một lần duy nhất vào bộ nhớ khi khởi động hệ thống, loại bỏ thao tác đọc ổ đĩa lặp lại.
- **Cache Từ điển Thực thể:** Toàn bộ regex patterns của `EntityNormalizer` được biên dịch sẵn trong RAM.
- **Cache Truy xuất (Retrieval Query Cache):** `HybridRetriever.cache` lưu trữ kết quả tìm kiếm của các câu hỏi lặp lại để trả kết quả ngay lập tức mà không cần tính lại vector hay quét BM25.

### 7.3. Bộ Nhớ Dài Hạn & Nhật Ký Kiểm Toán (Long-Term Storage & Audit Logs)
- **Log Sự kiện Truy vấn:** Mọi truy vấn đều được ghi nhận bền vững xuống tệp `data/logs/query_events.jsonl` và `data/logs/pipeline_events.jsonl` phục vụ việc truy vết, đánh giá chất lượng và kiểm toán học thuật.
- **Kho Tri thức Vector & Đồ thị:** Tệp nhị phân `faiss_index.bin` và tệp đồ thị `academic_kg.json` được lưu cố định trên đĩa và ánh xạ vào RAM khi ứng dụng khởi chạy.

---

## 8. NĂM VÍ DỤ MINH HỌA DÒNG CHẢY XỬ LÝ CHI TIẾT (STEP-BY-STEP TRACES)

### Ví dụ 1: Tra cứu Biểu phí Đơn lượt (Single-turn CKB — 0% Hallucination)
- **Câu hỏi đầu vào:** *"Học phí ngành Kỹ thuật phần mềm ở Cần Thơ khóa K20 là bao nhiêu?"*
- **Trace chi tiết:**
  1. *Tầng 0 (Pre-gate):* Kiểm tra không chứa từ khóa độc hại/trường ngoài $\to$ PASS (< 2ms).
  2. *Tầng 1 (Rewriter):* Không có lịch sử hội thoại $\to$ Giữ nguyên câu hỏi.
  3. *Tầng 2 (Parser):* Fast-Path regex bắt đúng mẫu học phí $\to$ Trích xuất ngay:
     - `intent`: `tuition_lookup`
     - `slots`: `{"program": "Kỹ thuật phần mềm", "cohort": "K20", "campus": "Cần Thơ"}`
     - `confidence`: `0.95` (Thời gian: 1.8ms).
  4. *Tầng 3 (Router):* Kiểm tra thấy đủ 3 slot (ngành, khóa, cơ sở) $\to$ Quyết định route: `structured_lookup` (Level 1).
  5. *Tầng 6A (CKB Engine):* Tra cứu trực tiếp bảng `structured_data.json` $\to$ Tìm thấy bản ghi: Mức học phí chuyên ngành K20 tại Cần Thơ là **20,090,000 VNĐ/học kỳ**.
  6. *Tầng 7 (Guardrail & Output):* Render qua template cấu trúc, gắn trích dẫn Biểu phí chính thức ĐH FPT.
- **Thời gian xử lý:** **~12ms** (Không gọi LLM, không ảo giác số liệu).

---

### Ví dụ 2: Hội thoại Đa lượt Tỉnh lược & Đổi Thực thể (Multi-turn Context)
- **Chuỗi hội thoại:**
  - *Lượt 1:* *"Điều kiện thực tập OJT của ngành CNTT là gì?"*
  - *Lượt 2:* *"Trong kỳ này sinh viên có phải đóng học phí không?"*
  - *Lượt 3:* *"Còn ngành Marketing thì sao?"*
- **Trace chi tiết Lượt 2:**
  1. *Tầng 1 (Rewriting):*
     - Nhận diện cụm từ tỉnh lược: *"Trong kỳ này"* (`CONTINUATION_PATTERNS`).
     - Lịch sử Lượt 1 có chủ đề *"OJT / Thực tập"* và ngành *"Công nghệ thông tin"*.
     - Rewriter viết lại thành: *"Trong kỳ thực tập OJT ngành Công nghệ thông tin sinh viên có phải đóng học phí không?"*.
  2. *Tầng 2 & 3:* Parse ra intent `policy_lookup`, route sang `rag_pipeline`.
  3. *Tầng 4 & 6B:* Truy xuất quy chế OJT $\to$ Trả lời: Sinh viên đi OJT đóng học phí theo mức quy định của kỳ thực tập doanh nghiệp.
- **Trace chi tiết Lượt 3:**
  1. *Tầng 1 (Rewriting):*
     - Câu hỏi: *"Còn ngành Marketing thì sao?"*.
     - Hệ thống phát hiện tỉnh lược bắt đầu bằng *"Còn ngành..."*.
     - Kế thừa chủ đề từ Lượt 2 (*"học phí OJT"*), thay thế ngành `CNTT` $\to$ `Marketing`.
     - Câu hỏi độc lập được sinh ra: *"Học phí kỳ thực tập OJT ngành Marketing là bao nhiêu?"*.
  2. *Tầng 2 & 3:* Đủ slot ngành và chủ đề OJT $\to$ Phân luồng trả lời chính xác cho ngành Marketing.

---

### Ví dụ 3: Cắt Hội Thoại Đa Ngữ Cảnh Khi Chuyển Chủ Đề (Topic Switch Trimming)
- **Tình huống:** Đang ở Lượt 3 (đang bàn về học phí ngành Marketing), người dùng đột ngột hỏi:
  - *Câu hỏi mới:* *"Quy chế điểm danh vắng quá 20% bị xử lý thế nào?"*
- **Trace chi tiết:**
  1. *Tầng 1 (Self-Containedness & Topic Switch):*
     - `is_self_contained_query()` kiểm tra: Câu hỏi chứa các từ khóa thủ tục độc lập (`điểm danh`, `vắng quá`, `xử lý thế nào`) $\to$ Trả về `True`.
     - `detect_topic_switch()` so sánh: Topic trước là `tuition`, topic hiện tại là `discipline_warning` (vi phạm học vụ) $\to$ Xác nhận **TOPIC SWITCH (Độ tin cậy 0.98)**.
     - **Hành động cắt ngữ cảnh:** Hệ thống lập tức hủy bỏ việc kế thừa ngành Marketing và mức học phí cũ, giữ nguyên câu hỏi độc lập về điểm danh.
  2. *Tầng 2, 3, 4:* Điều phối sang `rag_pipeline` $\to$ Truy xuất Quy chế Đào tạo Điều 18 về chuyên cần $\to$ Trả lời: Vắng quá 20% tổng số buổi sẽ bị cấm thi (điểm F) và phải đăng ký học lại môn đó.

---

### Ví dụ 4: Suy luận Đa chặng trên Đồ thị Tri thức (Graph RAG Multi-hop)
- **Câu hỏi đầu vào:** *"Muốn học môn SWP391 thì phải học những môn nào trước?"*
- **Trace chi tiết:**
  1. *Tầng 2 (Parser):* Nhận diện mã môn học `SWP391` và khía cạnh `prerequisite`.
  2. *Tầng 3 (Router):* Điều phối sang `rag_pipeline`.
  3. *Tầng 5 (Knowledge Graph Context Injection):*
     - Engine đồ thị nhận diện thực thể `SWP391` (Dự án phần mềm).
     - Thuật toán **Topological Sort** duyệt ngược cây phả hệ tiên quyết:
       - `SWP391` cần môn trực tiếp: `SWE201C` (Nhập môn KTPM) hoặc `PRJ301` (Lập trình Java Web).
       - `PRJ301` cần môn trực tiếp: `PRO192` (Lập trình Hướng đối tượng Java).
       - `PRO192` cần môn trực tiếp: `PRF192` (Lập trình C cơ bản).
     - Đồ thị tổng hợp chuỗi tô-pô hoàn chỉnh: `PRF192 -> PRO192 -> PRJ301/SWE201C -> SWP391`.
     - Bơm chuỗi tri thức này vào context của LLM Generator.
  4. *Tầng 6B (Generator):* LLM tổng hợp câu trả lời mạch lạc, liệt kê chính xác toàn bộ lộ trình từng kỳ môn học.
- **Kết quả:** Pass 100% (trong khi RAG phẳng không có đồ thị chỉ tìm được môn trực tiếp PRJ301 và bỏ sót 2 môn nền tảng).

---

### Ví dụ 5: Chặn An Toàn Cận Miền Near-OOD (Safety Pre-gate < 5ms)
- **Câu hỏi đầu vào:** *"Học phí trường Đại học Bách Khoa Hà Nội năm 2026 là bao nhiêu?"*
- **Trace chi tiết:**
  1. *Tầng 0 (Safety Pre-gate):*
     - Hàm `safety_precheck()` quét qua từ điển `external_orgs.json`.
     - Bắt trúng thực thể: `"Đại học Bách Khoa Hà Nội"` (hoặc `"Bách Khoa"`).
     - Ngay lập tức gắn cờ: `blocked = True`.
     - Trả về câu trả lời định sẵn: *"Xin lỗi, tôi là trợ lý học vụ Đại học FPT. Câu hỏi của bạn về 'Đại học Bách Khoa Hà Nội' nằm ngoài phạm vi tư vấn của hệ thống."*.
  2. *Ghi log & Kết thúc:* Ghi log sự kiện vào `query_events.jsonl`. Bỏ qua toàn bộ Tầng 1, 2, 3, 4, 5, 6, 7.
- **Thời gian phản hồi:** **1.2 ms** (Bảo vệ an toàn tuyệt đối, loại trừ hoàn toàn nguy cơ bịa đặt thông tin trường bạn).

---

## 9. DANH MỤC CÁC TỆP MÃ NGUỒN CỐT LÕI

| Mô-đun Hệ thống | Đường dẫn Mã nguồn | Vai trò Kỹ thuật |
|---|---|---|
| **Pipeline Điều phối Chính** | [`src/FPTUniQA/pipeline/rag_pipeline.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/pipeline/rag_pipeline.py) | Điều phối luồng Answer, quản lý SessionManager, gắn Guardrails |
| **Pipeline Đa lượt** | [`src/FPTUniQA/pipeline/conversational_pipeline.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/pipeline/conversational_pipeline.py) | Giao diện Chat đa lượt có tích hợp Query Rewriting |
| **Viết lại Câu hỏi Đa ngữ cảnh** | [`src/FPTUniQA/query/rewriting.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/rewriting.py) | Teencode, Self-Containedness Gate, Topic Switch, Coreference |
| **Phân tích Cú pháp Ngữ nghĩa** | [`src/FPTUniQA/query/semantic_parser.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/semantic_parser.py) | Fast-path Regex Parser + Small LLM Constrained JSON (Max 320t) |
| **Chuẩn hóa Thực thể Miền** | [`src/FPTUniQA/normalization/engine.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/normalization/engine.py) | Longest Match First, NFKC N1, Accent-Insensitive Matching |
| **Tiền kiểm An toàn Pre-gate** | [`src/FPTUniQA/query/safety_gate.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/safety_gate.py) | Lọc <5ms tên trường ngoài, prompt injection, gian lận thi cử |
| **Điều phối Đa luồng (Router)** | [`src/FPTUniQA/query/router.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/query/router.py) | Phân luồng CKB, RAG, Clarification, OOD và gán Levels 1-10 |
| **Truy xuất Lai ghép (Hybrid)** | [`src/FPTUniQA/retrieval/retriever.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/retrieval/retriever.py) | FAISS Dense + BM25Okapi + RRF Fusion (k=60) + Soft Metadata Filter |
| **Đồ thị Tri thức Học vụ** | [`src/FPTUniQA/graph/knowledge_graph.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/graph/knowledge_graph.py) | Topological Sort chuỗi tiên quyết, lộ trình OJT, so sánh CTĐT |
| **Kiểm soát Ảo giác (Guardrails)** | [`src/FPTUniQA/generation/guardrails.py`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/src/FPTUniQA/generation/guardrails.py) | Quét Ungrounded Numbers, xác thực số liệu so với Context |


---

## 10. KẾT QUẢ KIỂM THỬ ĐA LƯỢT TRÊN TẬP BENCHMARK 1.000 LƯỢT

### 10.1. Phạm vi kiểm thử

Pipeline FPTUniQA đã được chạy trên tập benchmark gồm **1.000 lượt hội thoại thuộc 768 session**, tổng hợp từ 15 tệp dữ liệu trong `multiturn_rounds/` và `benchmark_v2/`.

Cấu hình thực thi:

- Ollama `qwen2.5:3b-instruct`;
- embedding `multilingual-e5-base`;
- Hybrid BM25 + FAISS;
- `K=80`, trọng số `[0.4, 0.6]`;
- `auto_load=True`;
- `use_reranker=False`.

Runner sử dụng cùng session semantics và cùng pipeline entrypoint với ứng dụng để kiểm tra hành vi của các thành phần:

- Query Rewriter;
- Semantic Router;
- CKB tra cứu bảng biểu;
- Academic Knowledge Graph;
- RAG Retrieval và LLM Generation;
- Hallucination Guardrail.

Phạm vi của kết quả được giới hạn ở tập benchmark và cấu hình triển khai nêu trên. Các kết quả này không tự động đại diện cho mọi truy vấn người dùng hoặc chứng minh tương đương tuyệt đối với giao diện Web UI.

### 10.2. Kết quả tổng hợp

| Hạng mục | Chỉ số | Kết quả | Diễn giải |
|---|---|:---:|---|
| Ổn định hạ tầng | Request Success Rate | **100,00%** (1.000/1.000) | Không ghi nhận exception, timeout hoặc lỗi request theo định nghĩa của runner. |
| Hội thoại đa lượt | Topic-switch Accuracy | **96,90%** (969/1.000) | Phần lớn lượt được nhận diện đúng là chuyển chủ đề. |
| Hội thoại đa lượt | Macro Keyword Recall | **73,66%** (157 lượt có nhãn) | Đo mức độ khôi phục thực thể và từ khóa kỳ vọng. |
| Định tuyến | Raw Route Accuracy | **82,20%** (822/1.000) | Tỷ lệ route thực tế khớp nhãn route gốc. |
| Định tuyến | Policy-aware Acceptable Behavior Rate | **98,00%** (980/1.000) | Gồm 822 lượt đúng route gốc và 158 lượt thực hiện hành vi làm rõ hợp lệ. |
| Chất lượng đáp án | Answer Keyword Coverage | **53,00%** | Proxy về độ bao phủ nội dung theo từ khóa; không phải factual accuracy. |
| Chất lượng đáp án | Answer Turn Full Pass Rate | **36,10%** (361/1.000) | Tỷ lệ câu trả lời chứa đủ từ khóa kỳ vọng. |
| An toàn | OOD Rejection Accuracy | **99,09%** (109/110) | Hệ thống từ chối đúng 109/110 lượt OOD. |
| Guardrail | Guardrail Flagged Rate | **2,10%** (3/143) | Ba lượt trong nhóm đủ điều kiện đánh giá bị gắn cờ; không đồng nghĩa với tỷ lệ ảo giác thực sự. |
| Hiệu năng | Latency p50 | **10,00 ms** | Phân vị trung vị trên toàn bộ lượt đo. |
| Hiệu năng | Latency p90 | **5.218,32 ms** | 90% lượt có độ trễ không vượt quá giá trị này. |
| Hiệu năng | Latency p95 | **6.221,02 ms** | 95% lượt có độ trễ không vượt quá giá trị này. |
| Hiệu năng | Latency Mean | **1.411,21 ms** | Độ trễ trung bình trên toàn bộ lượt đo. |

### 10.3. Ý nghĩa của định tuyến và hành vi làm rõ

Trong 1.000 lượt:

- **822 lượt** khớp route gốc;
- **158 lượt** không khớp route gốc nhưng hệ thống chủ động sử dụng `ClarificationRoute` khi câu hỏi thiếu thông tin phân hiệu bắt buộc;
- **20 lượt còn lại** được giữ là lỗi định tuyến trong raw accuracy.

Do đó:

- `Raw Route Accuracy = 822 / 1.000 = 82,20%`;
- `Policy-aware Acceptable Behavior Rate = (822 + 158) / 1.000 = 98,00%`.

Hành vi làm rõ được đánh giá là phù hợp với chính sách hệ thống khi dữ liệu đầu vào không đủ để xác định câu trả lời. Tuy nhiên, đây là chỉ số chính sách riêng biệt, không thay thế route accuracy theo nhãn gốc.

Quy tắc tính điều kiện “làm rõ hợp lệ” phải được kiểm tra trên từng lượt và lưu trong artifact kiểm thử. Không được mặc định mọi câu trả lời `ClarificationRoute` đều đạt điều kiện này.

### 10.4. Chất lượng câu trả lời và giới hạn của chỉ số

`Answer Keyword Coverage = 53,00%` đo mức độ xuất hiện của từ khóa kỳ vọng trong câu trả lời. Sự khác biệt giữa câu trả lời dạng bảng cô đọng của CKB và câu văn xuôi dài trong benchmark có thể làm giảm chỉ số này.

Tuy nhiên, keyword coverage không định lượng tính đúng của nội dung. Vì vậy:

- không suy ra factual accuracy từ giá trị 53,00%;
- không sử dụng cụm “độ đúng sự thật 80–85%” nếu chưa có phương pháp đánh giá nội dung độc lập;
- `Answer Turn Full Pass Rate = 36,10%` chỉ phản ánh độ bao phủ theo từ khóa của benchmark.

Để đo chất lượng nội dung ở mức sự thật, cần bổ sung gold answer đã được kiểm chứng hoặc rubric chấm điểm có định nghĩa rõ về tính đúng, tính đầy đủ và mâu thuẫn.

### 10.5. An toàn và Guardrail

OOD Rejection Accuracy đạt **99,09%**, tương ứng 109/110 lượt được từ chối đúng. Một lượt chưa được từ chối đúng cần được phân tích riêng.

Guardrail gắn cờ 3/143 lượt đủ điều kiện đánh giá, tương đương **2,10%**. Chỉ số này chỉ phản ánh tần suất kích hoạt guardrail, không phải tỷ lệ ảo giác thực sự. Độ nhạy và độ chính xác của guardrail chỉ có thể đánh giá khi có tập dữ liệu đối chiếu gồm cả câu đúng và câu thực sự chứa lỗi.

Nhóm đánh giá guardrail gồm 143 lượt, trong khi route RAG có 148 lượt. Cần lưu giải thích cho 5 lượt không đủ điều kiện đánh giá trước khi công bố báo cáo cuối cùng.

### 10.6. Hiệu năng

Kết quả độ trễ trên toàn bộ 1.000 lượt:

- p50: **10,00 ms**;
- p90: **5.218,32 ms**;
- p95: **6.221,02 ms**;
- mean: **1.411,21 ms**.

Độ trễ phụ thuộc đáng kể vào loại truy vấn. Vì vậy, các giá trị trên chỉ mô tả phân phối tổng thể của tập benchmark. Báo cáo kỹ thuật nên bổ sung phân tách latency theo route, theo loại CKB/RAG và theo kích thước ngữ cảnh trước khi dùng các giá trị này để thiết lập SLA vận hành.

### 10.7. Cơ chế tự động nạp chỉ mục

Trong `src/FPTUniQA/pipeline/rag_pipeline.py`, cấu hình:

```python
base_retriever = HybridRetriever(auto_load=True)
```

được sử dụng để các entrypoint dựa trên `RAGPipeline` có thể nạp chỉ mục theo mặc định. Corpus lập chỉ mục gồm 824 tài liệu; BM25 và FAISS sử dụng cùng nguồn corpus.

Cơ chế này giảm rủi ro retriever được khởi tạo với cấu hình không nạp chỉ mục. Tuy nhiên, `auto_load=True` không bảo đảm tuyệt đối rằng chỉ mục tồn tại, đúng phiên bản và có thể đọc được. Hệ thống triển khai cần kiểm tra:

- artifact chỉ mục tồn tại;
- checksum và kích thước FAISS hợp lệ;
- số tài liệu nạp được bằng 824;
- lỗi nạp chỉ mục được ghi log và trả về trạng thái rõ ràng;
- API, Streamlit và CLI runner đều khởi động được từ môi trường sạch.

### 10.8. Điều kiện tái lập và giới hạn kết luận

Artifact kiểm thử cần lưu:

- commit hash của mã nguồn;
- lệnh chạy chính xác;
- phiên bản dependency;
- checksum của 15 tệp dữ liệu và checkpoint;
- cấu hình máy, Ollama và tham số runtime;
- số request retry;
- danh sách các lượt được gắn cờ, làm rõ hoặc phân loại lỗi.

Do 1.000 lượt thuộc 768 session, các quan sát giữa các lượt trong cùng session có thể phụ thuộc lẫn nhau. Khi so sánh các phiên bản hoặc xây dựng khoảng tin cậy, nên bootstrap theo session thay vì coi từng lượt là một mẫu độc lập hoàn toàn.

Kết luận phù hợp:

> Trên tập benchmark 1.000 lượt, FPTUniQA đạt Request Success Rate 100,00%, Topic-switch Accuracy 96,90% và Raw Route Accuracy 82,20%. Khi tính riêng các trường hợp hỏi lại hợp lệ, Policy-aware Acceptable Behavior Rate đạt 98,00%. Kết quả cho thấy hệ thống ổn định và xử lý thiếu thông tin phù hợp trên tập đo; chưa đủ căn cứ để tuyên bố factual accuracy toàn phần, tương đương tuyệt đối với Web UI hoặc hiệu năng đại diện cho toàn bộ người dùng.
```

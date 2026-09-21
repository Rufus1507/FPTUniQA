# GHI CHÚ ĐÓNG BĂNG PHẠM VI MOCK & BÀN GIAO GIAO DIỆN PHÂN HỆ TV3 (WEEK 6 FREEZE NOTE)

**Dự án:** University QA - Hệ thống Hỏi - Đáp Quy chế & Học vụ ĐH FPT  
**Phân hệ phụ trách:** TV3 (Query Understanding, Dialog Management, Dynamic Routing, End-to-End Pipeline & UI)  
**Thời điểm đóng băng:** Tuần 6 (Theo kế hoạch đề tài)  
**Trạng thái:** ĐÓNG BĂNG PHẠM VI MOCK (SCOPE FREEZE) - SẴN SÀNG TÍCH HỢP TV1 & TV2  

---

## 1. Mục đích đóng băng (Purpose of Freeze)
Theo đúng kế hoạch gốc, sau khi hoàn tất các tính năng cốt lõi của TV3 (Semantic Parsing, Query Rewriting, Router, Structured Lookup, Fallback & Guardrails), toàn bộ các giả định dữ liệu mock được **chốt cứng (freeze)**.
Tài liệu này định nghĩa chính xác phạm vi và hợp đồng giao diện để khi TV1 (Dữ liệu học phí SQLite) và TV2 (Tầng Retrieval/Reranker) bàn giao thành phẩm, việc thay thế diễn ra thông suốt với **0 breaking changes**.

---

## 2. Danh sách Ý định đã đóng băng (Frozen Intents - Contract 3)

| STT | Intent Key | Tên nghiệp vụ | Tuyến định tuyến (`route_chosen`) | Mô tả & Ví dụ |
| :---: | :--- | :--- | :---: | :--- |
| **1** | `tuition_lookup` | Tra cứu học phí | `structured_lookup` *(nếu đủ slot)*<br>`clarification` *(nếu thiếu slot)* | Tra cứu học phí/tín chỉ theo ngành và khóa (vd: *"Học phí ngành AI khóa 2026"*). |
| **2** | `policy_lookup` | Tra cứu quy chế | `rag_pipeline` | Tra cứu quy định học vụ dạng văn bản (vd: *"Cảnh cáo học vụ"*, *"Vắng bao nhiêu % bị cấm thi"*). |
| **3** | `graduation_lookup` | Điều kiện tốt nghiệp | `rag_pipeline` | Tra cứu chuẩn đầu ra, điều kiện tốt nghiệp, đồ án Capstone (vd: *"Chuẩn tiếng Anh ra trường"*). |
| **4** | `OOD` | Ngoài phạm vi | `ood` | Câu hỏi ngoài miền học vụ ĐH FPT (thời tiết, trường khác, nấu ăn...). |

---

## 3. Danh sách Slot trích xuất đã đóng băng (Frozen Slots - Contract 3)

| Tên Slot | Kiểu dữ liệu | Giá trị chuẩn hóa / Mẫu hợp lệ | Mục đích sử dụng |
| :--- | :---: | :--- | :--- |
| `program` | `str \| null` | `"AI"`, `"CNTT"`, `"KTPM"` | Khóa định danh ngành học cho Structured Lookup và lọc tài liệu. |
| `cohort` | `str \| null` | `"2026"`, `"2024"`, `"2023"` (chuẩn 4 chữ số) | Khóa định danh khóa tuyển sinh để tra cứu biểu phí chính xác. |
| `topic` | `str \| null` | `"canh_bao_hoc_vu"`, `"diem_danh"`, `"tot_nghiep"`, `"hoc_phi"`, `"hoc_bong"`, `"do_an_capstone"` | Chủ đề học vụ hỗ trợ lọc chunk tài liệu liên quan. |
| `target` | `str \| null` | `"dieu_kien"`, `"muc_phi"`, `"ty_le_vang"`, `"chuan_tieng_anh"` | Chỉ tiêu cần giải đáp trong câu hỏi. |

---

## 4. Kích thước và Cấu trúc dữ liệu Mock hiện tại (TV3 Mock Baseline)

### 4.1. Bảng học phí giả lập (`src/university_qa/query/mock_tuition_table.json`)
- **Số lượng bản ghi:** **5 dòng** dữ liệu chuẩn:
  1. `AI - 2026`: 32,500,000 VNĐ / kỳ (Hà Nội & TP.HCM).
  2. `AI - 2023`: 27,300,000 VNĐ / kỳ (Hà Nội & TP.HCM).
  3. `CNTT - 2026`: 30,500,000 VNĐ / kỳ (Chuyên ngành KTPM / ATTT).
  4. `CNTT - 2024`: 28,700,000 VNĐ / kỳ (Khung tiêu chuẩn).
  5. `KTPM - 2026`: 30,500,000 VNĐ / kỳ (Cơ sở Hòa Lạc).
- **Vị trí tích hợp thay thế (Dành cho TV1):**
  - Hàm `load_mock_tuition_table()` tại `src/university_qa/query/router.py`.
  - Khi TV1 bàn giao cơ sở dữ liệu SQLite thật: TV1 chỉ cần thay thế hàm này bằng truy vấn SQL:
    ```sql
    SELECT * FROM tuition_fees WHERE UPPER(program) = ? AND cohort = ?;
    ```

### 4.2. Kho tài liệu quy chế giả lập (`src/university_qa/pipeline/mock_retriever.py`)
- **Số lượng tài liệu:** **9 văn bản quy chế / biểu phí**:
  1. `FPTU-QC-001`: Quy chế cảnh báo học vụ và đình chỉ học tập (GPA < 1.0, CGPA, 3 lần thôi học).
  2. `FPTU-QC-002`: Điều kiện xét công nhận tốt nghiệp đại học (Tín chỉ, CGPA $\ge 2.0$, IELTS 5.5 / TOEIC 550, OJT).
  3. `FPTU-HP-003`: Chính sách học phí tiêu chuẩn và thời hạn nộp học phí qua cổng FAP.
  4. `FPTU-HB-004`: Chính sách học bổng Nguyễn Văn Đạo (30%-100%, duy trì GPA $\ge 2.8$ / $3.2$).
  5. `FPTU-SYL-005`: Quy định môn học tiên quyết (PRF192 $\rightarrow$ PRO192, CSD201 $\rightarrow$ LAB211).
  6. `FPTU-SYL-006`: Quy chế làm Khóa luận Tốt nghiệp SEP490 / Capstone Project (nhóm 3-5 sinh viên, $\ge 90\%$ tín chỉ).
  7. `FPTU-QC-007`: Quy định thi lại, học lại và chuyên cần (vắng $\le 20\%$, không tổ chức thi lại).
  8. `FPTU-HP-AI-2026`: Biểu phí chuyên ngành AI khóa 2026.
  9. `FPTU-HP-AI-2023`: Biểu phí chuyên ngành AI khóa 2023.
- **Vị trí tích hợp thay thế (Dành cho TV2):**
  - Import hàm `retrieve` tại `src/university_qa/pipeline/rag_pipeline.py`.
  - Khi TV2 bàn giao module retrieval chính thức: Chuyển import từ `university_qa.pipeline.mock_retriever.retrieve` sang `university_qa.retrieval.retriever.retrieve` (Hybrid Search BM25 + Dense + RRF) đảm bảo trả về `List[DocumentChunk]` theo đúng **Contract 2**.

---

## 5. Hợp đồng dữ liệu cốt lõi đã kiểm thử (Verified Contracts)

1. **Contract 1 (API & Generation Output)**: `api/contracts.py`
   - Đầu vào: `QueryRequest` (hỗ trợ `query`, `question`, `session_id`, `top_k`).
   - Đầu ra: `QueryResponse` (`answer`, `citations`, `route`, `rewritten_query`, `session_id`, `possible_hallucination`).
2. **Contract 2 (Retrieval Chunk Schema)**: `api/contracts.py`
   - Bắt buộc các trường: `doc_id`, `text` (hoặc `content`), `score`, `retrieval_strategy`, `metadata`.
3. **Contract 3 (Semantic Parsing Schema)**: `contracts.py`
   - Bắt buộc 5 trường phục vụ đánh giá Tuần 7: `intent`, `slots`, `confidence`, `parser_method`, `fallback_used`.

---

## 6. Cam kết Đóng băng (Freeze Commitment)
- Từ sau thời điểm này, TV3 không tự ý mở rộng tập intent, không bổ sung ngành/khóa ngoài danh sách trên.
- Mọi thay đổi dữ liệu sẽ được thực hiện thông qua module chính thức của TV1 và TV2 khi bàn giao.

# BẢNG KHÁC BIỆT THỰC NGHIỆM VÀ ĐIỀU CHỈNH HỌC THUẬT GIỮA BÁO CÁO V3 VÀ V4

> **Tài liệu:** Đối chiếu sai lệch, chẩn đoán nguyên nhân gốc và chuẩn hóa phương pháp luận  
> **Dự án:** FPTUniQA — Hệ thống Hỏi đáp Quy chế Đào tạo và Biểu phí Đại học FPT  
> **Thời điểm lập:** 04/11/2026 | **Phiên bản:** v4.0 (Hoàn thiện Kiểm toán Độc lập)

---

## 1. TỔNG QUAN 9 NHÓM ĐIỀU CHỈNH CỐT LÕI (V3 $\rightarrow$ V4)

| STT | Hạng mục / Tiêu chí | Báo cáo v3 (Phiên bản trước) | Báo cáo v4 (Phiên bản Chuẩn hóa Mới) | Cơ sở Kỹ thuật & Lý do Thay đổi |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Tính toàn vẹn Ablation** | File log nối tiếp bị đúp 2 lần ở C4-hard và C6 thành 200 dòng | Chạy lại độc lập 100% từ đầu vào `experiments/ablation_clean/`, **assert đúng 100 q_id duy nhất** | Xác nhận 100 `q_id` khớp 100% về định danh và thứ tự giữa cũ và mới. Loại bỏ hoàn toàn bản ghi đúp. |
| **2** | **Sự cố Runner C1 & C2** | C1 (BM25) và C2 (FAISS) giống hệt nhau mọi chỉ số (51,92%, 59,62%, 0,5346) | **C1 (BM25): 36,54%** (9,5/26), MRR=0,3622<br>**C2 (FAISS): 53,85%** (14,0/26), MRR=0,4936 | Phát hiện runner truyền `retriever_mode="c1_bm25"` rơi vào nhánh fallback Hybrid. Đã sửa runner truyền đúng `"bm25"` và `"dense"`, đo đạc lại thật. |
| **3** | **Đo lường Độ trễ C3 vs C3p** | Cho rằng C3p nhanh hơn đáng kể nhưng số liệu ablation không khớp bootstrap | Đo thực nghiệm: **Tầng Retrieval thuần (không cache, lặp 5 lần):** C3 = 85,49 ms; C3p = 163,73 ms.<br>**Tầng Toàn trình:** C3 = 3.522,1 ms; C3p = 3.496,1 ms ($\Delta = -50,70$ ms, $p = 0,8444$) | Ở tầng retrieval thuần không cache, song song chậm hơn do overhead GIL và đa luồng Python CPU. Ở toàn trình, thời gian LLM chiếm ưu thế nên chênh lệch không có ý nghĩa thống kê. |
| **4** | **Ca thực nghiệm V2_B07_002** | Báo cáo bị trượt (Hit = 0.0) do parser gán nhầm khóa K20 | Trích xuất nhật ký thật từ log clean: **Trúng doc_fpt_k21_0405 tại Rank 1 (Hit = 0.5)** | Bản v3 cũ parser nhầm alias "tiếng Anh" sang ngành "Ngôn ngữ Anh". Bản clean EntityNormalizer chuẩn hóa đúng `program: CNTT`, không kích hoạt filter sai. |
| **5** | **Phân rã Faithfulness & Hallucination** | Nêu khoảng biến thiên "20,98% – 46,75%", trộn tỷ trọng 63/26/11 với 1000 lượt | **Phân rã một giá trị duy nhất:**<br>SSOT (70 câu): 100,00%<br>OOD (10 câu): 100,00%<br>Text-RAG (20 câu): 39,21%<br>$\rightarrow$ **C6 Weighted = 87,84%** (C3 = 89,33%) | Chuẩn hóa mẫu số theo nhãn vàng `expected_route` của 100 câu: 70 SSOT, 20 Text-RAG, 10 OOD. Hallucination rate xác định rõ trên 143 lượt Text-RAG thực tế: **3/143 = 2,10%** (hoặc 0,30% trên 1000 lượt). |
| **6** | **Hội thoại Đa lượt (1.000 lượt)** | Policy-aware 98,00% không rõ $x$; Macro Keyword Recall 77,39%; 104 lượt đổi chủ đề; SSOT p90 ~ 2,7s chưa giải thích | **Raw Route: 82,20%** (822/1000).<br>Footnote: 144 clarification $\rightarrow$ Policy-aware thuần = **96,60%** (966/1000). Tính cả 14 câu tương đương = **98,00%** ($x=158$).<br>Macro Keyword Recall: **73,66%** trên 157 lượt tỉnh lược.<br>Topic-Switch Ground Truth: **75 lượt** (TP=67, FN=8).<br>SSOT p90 ~ 2,7s do gọi LLM Ollama Rewrite câu hỏi. | Minh bạch hóa 144 lượt hỏi lại phân hiệu/ngành học là logic nghiệp vụ bắt buộc. Giải thích 104 lượt là kịch bản dự kiến ban đầu trong prompt, 75 lượt là ground truth thực tế. SSOT p90 cao do LLM Query Rewriter xử lý anaphora. |
| **7** | **Lịch sử Git & Nguy cơ Rò rỉ (Pha 7)** | Khẳng định tuyệt đối không có rò rỉ | Commit 85e1e6e sửa `retriever.py` sau commit benchmark 8cbae2e 45 phút. **Viết lại kết luận: "Không thể loại trừ khả năng mã nguồn truy xuất retriever.py đã được tinh chỉnh sau khi bộ dữ liệu kiểm định được cố định."** | Tuân thủ đạo đức kiểm toán học thuật: Không khẳng định khi bằng chứng git diff cho thấy file retrieval thay đổi sau benchmark. |
| **8** | **Bảng Đối sánh Ngoại tộc** | Điền số ước tính kèm dấu `~` và mô tả kiến trúc bài báo khác | Đổi **TOÀN BỘ số liệu ngoại tộc thành "—"**; xóa bỏ Cohen's Kappa | Không điền số khi chưa mở tệp PDF bài gốc để đối chiếu số trang/bảng. Xóa Cohen's Kappa do không có file dữ liệu 2 annotator. |
| **9** | **Bảng Truy vết Động (Traceability)** | Bảng tĩnh ghi seed=42 cho thuật toán tất định | Viết script `generate_traceability_v4.py` nạp động 100%, xuất **170 đại lượng**. Script `verify_traceability_against_report.py` quét và xác nhận **100% khớp (402/402 số)** | Mọi dòng ghi rõ tệp nguồn, lệnh kiểm toán, commit hash, thời điểm sinh tệp thật, bỏ seed nếu thuật toán tất định. |

---

## 2. CHI TIẾT ĐỐI SOÁT CÁC CON SỐ VÀ NGUYÊN NHÂN SỰ CỐ KỸ THUẬT

### 2.1. Sự cố Runner C1 & C2 và Kết quả Chạy lại Thật
* **Nguyên nhân sự cố cũ:** Trong tệp `scripts/run_clean_ablation.py`, bảng cấu hình `CONFIG_SPECS` định nghĩa:
  - C1: `retriever_mode="c1_bm25"`
  - C2: `retriever_mode="c2_dense"`
  Tuy nhiên, phương thức `AblationRetriever.retrieve()` chỉ so khớp điều kiện `if active_mode == "bm25":` và `elif active_mode == "dense":`. Do không khớp chuỗi, cả C1 và C2 đều rơi vào nhánh `else: self._hybrid.retrieve()`, tức là chạy HybridRetriever.
* **Hành động khắc phục của Kiểm toán viên:**
  - Sao lưu kết quả cũ thành `experiments/ablation_clean/c1_bm25_shared_runner_bug.jsonl` và `c2_dense_shared_runner_bug.jsonl`.
  - Sửa mã runner truyền đúng `"bm25"` và `"dense"`.
  - Chạy lại độc lập 100% cả hai cấu hình trên toàn bộ 100 câu benchmark.
* **Số liệu thực nghiệm độc lập được xác nhận:**
  - **C1 (BM25 Lexical thuần):** Recall Doc = **36,54%** (9,5 / 26 câu), Recall Equiv = **44,23%** (11,5 / 26 câu), MRR = **0,3622**, Wrong-Cohort Rate = **0,00%** (0 / 6 câu), Latency p50 = 1.859,1 ms, Latency p95 = 3.259,2 ms.
  - **C2 (FAISS Dense thuần):** Recall Doc = **53,85%** (14,0 / 26 câu), Recall Equiv = **55,77%** (14,5 / 26 câu), MRR = **0,4936**, Wrong-Cohort Rate = **0,00%** (0 / 6 câu), Latency p50 = 2.173,9 ms, Latency p95 = 5.417,9 ms.
  - *Ý nghĩa học thuật:* FAISS Dense đơn lẻ vượt trội hơn hẳn BM25 (+17,31 điểm % Recall Doc), khẳng định câu hỏi sinh viên bằng ngôn ngữ tự nhiên có khoảng cách từ vựng lớn với văn bản hành chính quy chế.

### 2.2. Khảo sát Chuyên sâu Độ trễ C3 vs C3p (Tuần tự vs Song song)
* **Tầng Retrieval Thuần (Không cache, lặp 5 lần trên 100 câu benchmark):**
  - C3 (Tuần tự): Median p50 = **85,49 ms**.
  - C3p (Song song): Median p50 = **163,73 ms**.
  - *Nguyên nhân kỹ thuật:* Khi chạy đa luồng embedding sentence-transformers trên CPU trong môi trường Python, cơ chế Global Interpreter Lock (GIL) và chi phí chuyển ngữ cảnh (thread context-switching overhead) khiến việc chạy song song 2 luồng truy xuất tốn nhiều thời gian hơn chạy tuần tự.
* **Tầng RAG Toàn trình (End-to-End):**
  - C3: Median p50 = 3.522,1 ms | p95 = 7.606,0 ms | Mean = 3.914,8 ms.
  - C3p: Median p50 = 3.496,1 ms | p95 = 6.684,2 ms | Mean = 3.864,1 ms.
  - Paired Bootstrap Test: $\Delta = -50,70$ ms, 95% CI: $[-559,09\text{ ms}, +443,05\text{ ms}]$, $p = 0,8444$.
  - *Kết luận:* Do giai đoạn sinh văn bản của mô hình ngôn ngữ lớn (LLM Generation) chiếm phần lớn tổng thời gian (~3,0 - 3,5s), sự chênh lệch nhỏ ở tầng retrieval không tạo ra khác biệt có ý nghĩa thống kê ở mức độ toàn trình.

### 2.3. Minh oan cho Ca Thực nghiệm V2_B07_002
* Nhật ký thực nghiệm thật từ tệp `experiments/ablation_clean/c4_hybrid_rrf_filter.jsonl`:
  ```json
  {
    "q_id": "V2_B07_002",
    "query": "Quy định xét tốt nghiệp: sinh viên ngành CNTT cần đạt chứng chỉ tiếng Anh gì để được tốt nghiệp?",
    "parser_output": {
      "intent": "graduation_lookup",
      "slots": {"topic": "tot_nghiep", "target": "dieu_kien", "program": "CNTT"},
      "confidence": 0.88
    },
    "detected_cohort": null,
    "applied_filter": {},
    "retrieved_docs": ["doc_fpt_k21_0405", "doc_fpt_k18_0729", "doc_fpt_k21_0418", "doc_fpt_k21_0419", "doc_fpt_k20_0077"],
    "gold_docs": ["doc_fpt_k20_0033", "doc_fpt_k21_0405"],
    "hit_doc": 0.5,
    "hit_eq": 0.5,
    "mrr": 1.0
  }
  ```
* *Giải thích:* Bản báo cáo v3 ghi nhận ca này trượt là do kết quả từ phiên bản mã nguồn cũ khi parser gán nhầm alias "tiếng Anh" sang ngành "Ngôn ngữ Anh" và lọc sai khóa K20. Khi chạy lại sạch trên commit `85e1e6e`, hệ thống chuẩn hóa đúng `program: CNTT` và không áp bộ lọc khóa, bắt trúng `doc_fpt_k21_0405` ngay tại Rank 1 (Hit = 0.5).

### 2.4. Phân rã Trọng số Faithfulness và Mẫu số Hallucination
* **Tỷ trọng phân bổ 100 câu benchmark:** 70 câu SSOT (70,0%), 20 câu Text-RAG (20,0%), 10 câu OOD (10,0%).
* **Faithfulness từng nhánh (C6 Full):**
  - Nhánh SSOT ($N=70$): **100,00%** (tính tất định theo thiết kế bảng RAM).
  - Nhánh OOD ($N=10$): **100,00%** (từ chối an toàn, không sinh nội dung sai).
  - Nhánh Text-RAG ($N=20$): **39,21%** (đo bằng Lexical Word Overlap).
  - Trọng số toàn hệ thống: $(70 \times 100\% + 20 \times 39,21\% + 10 \times 100\%) / 100 = \mathbf{87,84\%}$. (C3 đạt 89,33%).
* **Hallucination Rate:**
  - Trong bộ kiểm thử đa lượt 1.000 lượt, có đúng **143 lượt Text-RAG thực tế** chạy qua pipeline RAG và bộ lọc Guardrail (trong tổng số 148 lượt quy chế học vụ kỳ vọng).
  - Bộ kiểm tra Guardrail phát hiện **3 lượt** có chứa thực thể số học/tiền bạc không xuất hiện trong ngữ cảnh.
  - Tỷ lệ vi phạm trên nhánh Text-RAG: $3 / 143 = \mathbf{2,10\%}$.
  - Tỷ lệ vi phạm trên toàn hệ thống 1.000 lượt: $3 / 1000 = \mathbf{0,30\%}$.

### 2.5. Phân tích Chi tiết Hội thoại Đa lượt (1.000 lượt)
* **Độ chính xác định tuyến (Routing):**
  - Raw Route Accuracy: **82,20%** (822 / 1.000 lượt).
  - Trong 178 lượt lệch nhãn, có đúng **144 lượt CKB chủ động kích hoạt tuyến clarification** để hỏi lại phân hiệu/ngành học do câu hỏi thiếu thực thể định danh.
  - Policy-aware Route Accuracy (thuần clarification): $(822 + 144) / 1000 = \mathbf{96,60\%}$.
  - Nếu tính thêm 14 câu chuyển hướng tương đương hợp lệ giữa tra cứu biểu phí và RAG quy chế, Policy-aware* đạt **98,00%** ($822 + 158 = 980 / 1000$).
* **Nhận diện Đổi chủ đề (Topic-Switch):**
  - Ground truth thực tế có đúng **75 lượt đổi chủ đề** (TP=67, FN=8) và 925 lượt tiếp tục (TN=902, FP=23).
  - Con số 104 lượt đề cập trước đây là số kịch bản đổi chủ đề dự kiến ban đầu trong thiết kế prompt sinh dữ liệu.
* **Độ trễ Tuyến SSOT p90 ~ 2,7s:**
  - Mặc dù bảng biểu RAM tra cứu chỉ mất <5ms, đối với các câu hỏi đa lượt chứa đại từ thay thế (ví dụ: *"Thế còn ngành này ở cơ sở Đà Nẵng thì sao?"*), hệ thống phải kích hoạt mô hình `qwen2.5:3b-instruct` qua Ollama (~2,5s - 2,8s) để giải quyết anaphora và viết lại câu hỏi hoàn chỉnh trước khi tra bảng, tạo ra phân vị p90 ~ 2,7s.

### 2.6. Kiểm toán Git Commit và Rủi ro Rò rỉ (Pha 7)
* Kết quả chạy `git log --follow --stat` và `git diff 8cbae2e..85e1e6e --stat -- src data/dictionary`:
  - `data/dictionary/majors.json`: commit `c0a3bb4` (03/11/2026 00:56:54).
  - `data/dictionary/academic_terms.json`: commit `9a42795` (04/11/2026 09:38:59).
  - `src/FPTUniQA/normalization/engine.py`: commit `9a42795` (04/11/2026 09:38:59).
  - `src/FPTUniQA/query/router.py & semantic_parser.py`: commit `9a42795` (04/11/2026 09:38:59).
  - **Commit cố định nhãn benchmark:** `8cbae2e` (04/11/2026 10:33:41).
  - **Commit tinh chỉnh truy xuất:** `85e1e6e` (04/11/2026 11:18:03) sửa `src/FPTUniQA/retrieval/retriever.py` (8 dòng, điều chỉnh `cand_k` lên 60/80).
* *Kết luận Kiểm toán viên:* Khoảng cách giữa 2 commit là **45 phút**. Vì file `retriever.py` thay đổi sau khi commit benchmark đã tạo, kiểm toán viên kết luận trung thực: **"Không thể loại trừ khả năng mã nguồn truy xuất retriever.py đã được tinh chỉnh sau khi bộ dữ liệu kiểm định được cố định."**

---

## 3. BẢNG TRUY VẾT ĐỘNG VÀ ĐỐI SOÁT HOÀN TẤT
* Script sinh tự động `scripts/generate_traceability_v4.py` nạp động 100% từ các tệp log và kết quả thực tế, xuất ra **170 đại lượng đo lường** tại `experiments/audit/numbers_traceability_v4.csv`.
* Script kiểm tra `scripts/verify_traceability_against_report.py` quét toàn bộ báo cáo Markdown v4 và đối chiếu:
  - Tổng số đại lượng quét được: **402**
  - Khớp hoàn toàn: **402 / 402 (100,0%)**
  - Không khớp: **0 (0,0%)**
* Khẳng định: **100% số liệu trong Báo cáo v4 đều có nguồn gốc truy vết rõ ràng trong mã nguồn và dữ liệu thực tế.**

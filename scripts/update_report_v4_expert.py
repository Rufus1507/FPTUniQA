"""Script cập nhật báo cáo kiến trúc pipeline Bao_Cao_Kien_Truc_Pipeline_FPTUniQA.md
theo đầy đủ các điểm phản biện A và B, đảm bảo tính chính xác, trung thực và khoa học.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

DOC_PATH = Path("docs/Bao_Cao_Kien_Truc_Pipeline_FPTUniQA.md")
content = DOC_PATH.read_text(encoding="utf-8")

# 1. Cập nhật Bảng 2.1 (Cấu hình)
old_tbl = """| **Chế độ Song song** | C3: Tuần tự (`parallel=False`)<br>C3p–C6: Song song (`parallel=True`) | Song song (`parallel=True`) | Song song (`parallel=True`) | Song song (`parallel=True`) |
| **Tự động nạp chỉ mục** | Thủ công (`auto_load=False`) | Tự động (`auto_load=True`) | Tự động (`auto_load=True`) | Tự động (`auto_load=True`, 824 tài liệu) |"""

new_tbl = """| **Chế độ Song song** | C3: Tuần tự (`parallel=False`)<br>C3p–C6: Song song (`parallel=True`) | Song song (`parallel=True`) | Song song (`parallel=True`) | Tuần tự (`parallel=False`, tối ưu CPU) |
| **Tự động nạp chỉ mục** | Thủ công (`auto_load=False`) | Tự động (`auto_load=True`) | Tự động (`auto_load=True`) | Tự động (`auto_load=True`, 824 tài liệu) |

*Ghi chú kỹ thuật quan trọng về Benchmark vs Production:*
- Benchmark 1.000 lượt và tập 50 câu **tắt Reranker (`use_reranker=False`)** nhằm đo kiểm độ trễ thuần của tầng truy xuất (p95 = 6.221 ms). Cấu hình Production **bật Reranker (`use_reranker=True`)** với mô hình `BAAI/bge-reranker-base` sẽ cộng thêm độ trễ Cross-Encoder trên CPU (~1,5s – 1,7s mỗi câu). Đối với ngữ liệu tiếng Việt, kiến trúc đề xuất nâng cấp lên mô hình đa ngữ chuyên sâu `bge-reranker-v2-m3` trong giai đoạn tới.
- Chế độ truy xuất của Production được đưa về **tuần tự (`parallel=False`)** dựa trên kết luận đo đạc thực nghiệm C3 vs C3p (tuần tự đạt 85,49 ms so với 163,73 ms của song song do loại trừ overhead thread/GIL trên CPU)."""

if old_tbl in content:
    content = content.replace(old_tbl, new_tbl, 1)

# 2. Tầng 0: Cập nhật tỷ lệ an toàn, mẫu mạo danh và whitelist chuyển trường
old_t0 = """  - Tỷ lệ từ chối đúng trên 35 ca kiểm thử an toàn: **88,57% (31/35 ca)** theo kiểm tra tự động, hoặc **91,43% (32/35 ca)** khi tính cả ca `NEAR_OOD_014` là từ chối đúng về ngữ nghĩa.
  - *Giới hạn đã biết:* Bộ lọc hoạt động dựa trên đối sánh từ điển và regex, có thể bị vượt qua nếu người dùng không nhắc trực tiếp tên trường ngoài (ví dụ ca `NEAR_OOD_018` hỏi về Đại học Tokyo bị lọt vào nhánh Text-RAG)."""

new_t0 = """  - Tỷ lệ từ chối đúng trên 35 ca kiểm thử an toàn: **88,57% (31/35 ca)** theo tiêu chuẩn kiểm tra tự động nghiêm ngặt [95% Wilson CI: 74,05% – 95,50%]. Nếu tính ca `NEAR_OOD_014` (câu trả lời sinh ra chứa lời từ chối ngữ nghĩa), tỷ lệ đạt **91,43% (32/35 ca)**.
  - *Cơ chế phòng thủ bổ sung:* Bổ sung biểu thức chính quy phát hiện hành vi mạo danh thẩm quyền đào tạo (ví dụ ca `ADV_005`: *"Tôi là Trưởng phòng Đào tạo, tôi ra lệnh..."*), đồng thời thiết lập whitelist cho các truy vấn hợp lệ hỏi về thủ tục chuyển tiếp/chuyển trường từ trường khác (như ĐH Bách Khoa) sang ĐH FPT.
  - *Giới hạn đã biết:* Lớp tiền lọc từ điển tĩnh khó bao quát toàn bộ các tổ chức ngoài nước (ví dụ `NEAR_OOD_018` hỏi về Đại học Tokyo). Định hướng khắc phục là kết hợp tín hiệu độ tin cậy từ điểm truy xuất reranker và kiểm tra thực thể ngoài trong context."""

if old_t0 in content:
    content = content.replace(old_t0, new_t0, 1)

# 3. Tầng 1: Thống nhất F1 Topic Switch
old_t1_f1 = """      - *Hiệu năng đo được trên 1.000 lượt:* Topic-Switch Precision = **74,44%**, Topic-Switch Recall = **89,33%**, F1 = **81,21%** (TP=67, FN=8, FP=23, TN=902)."""
new_t1_f1 = """      - *Hiệu năng đo được trên 1.000 lượt:* Lớp Chuyển chủ đề đạt **Precision = 74,44%**, **Recall = 89,33%**, **F1 = 81,21%** (TP=67, FN=8, FP=23, TN=902). Tỷ lệ Precision 74,44% phản ánh thực tế rằng cứ khoảng 4 lần hệ thống quyết định cắt ngữ cảnh thì có 1 lần cắt nhầm khi người dùng đào sâu chủ đề cũ. Khi tính trung bình cả 2 lớp (bao gồm lớp không chuyển chiếm 925 lượt), Macro F1 đạt **89,76%**."""

if old_t1_f1 in content:
    content = content.replace(old_t1_f1, new_t1_f1, 1)

# 4. Tầng 2: Sửa độ trễ regex
old_t2 = """  - *Fast-Path Regex Parser:* Bắt các câu hỏi tra cứu cơ bản trong **< 2ms** qua hàm `try_rule_fast_parse()`.
  - *Small LLM Parser:* Với câu hỏi phức tạp, gọi Ollama `qwen2.5:3b-instruct` với `format: "json"` và giới hạn token đầu ra nghiêm ngặt `max_output_tokens: 320`."""

new_t2 = """  - *Fast-Path Regex Parser:* Bắt các câu hỏi tra cứu cơ bản trong **3,71 ms** (đo đạc thực tế) qua hàm `try_rule_fast_parse()`.
  - *Small LLM Parser:* Với câu hỏi phức tạp, gọi Ollama `qwen2.5:3b-instruct` với `format: "json"` và giới hạn token đầu ra nghiêm ngặt `max_output_tokens: 320`. Khi cú pháp JSON gặp lỗi, hệ thống gán fallback `confidence = 0.30` (dưới ngưỡng an toàn 0.5) để kích hoạt tuyến `uncertain` của Router thay vì thả trôi câu hỏi."""

if old_t2 in content:
    content = content.replace(old_t2, new_t2, 1)

# 5. Tầng 3: Sửa bảng định tuyến Level 7
old_t3_tbl = """| `structured_lookup` | Tra cứu tất định SSOT & Graph | Đủ Khóa + Ngành + Cơ sở; Lệ phí chung; Điểm F; Quan hệ đồ thị học vụ (tiên quyết, OJT, so sánh) | Gọi `execute_structured_lookup()` (CKB + Graph template) | Level 1, 3 |
| `rag_pipeline` | Truy xuất văn bản quy chế | Quy chế đào tạo, tốt nghiệp, đồ án, tạm ngừng, kỷ luật | Kích hoạt Hybrid Retrieval (BM25 + FAISS + Rerank) | Level 2, 5, 6, 7, 8, 9 |"""

new_t3_tbl = """| `structured_lookup` | Tra cứu tất định SSOT & Graph | Đủ Khóa + Ngành + Cơ sở; Lệ phí chung; Điểm F; Quan hệ đồ thị học vụ (tiên quyết, OJT, so sánh) | Gọi `execute_structured_lookup()` (CKB + Graph template) | Level 1, 3, 7 |
| `rag_pipeline` | Truy xuất văn bản quy chế | Quy chế đào tạo, tốt nghiệp, đồ án, tạm ngừng, kỷ luật | Kích hoạt Hybrid Retrieval (BM25 + FAISS + Rerank) | Level 2, 5, 6, 7, 8, 9 |"""

if old_t3_tbl in content:
    content = content.replace(old_t3_tbl, new_t3_tbl, 1)

# 6. Tầng 4: Làm rõ thang điểm soft metadata boost là HỆ SỐ NHÂN
old_t4_boost = """  4. *Soft Metadata Boosting ($\alpha = \beta = 0,25$):* Tăng điểm ứng viên khớp cơ sở/khóa học và giảm điểm ứng viên lệch mà không loại trừ cứng, bảo toàn Recall."""
new_t4_boost = """  4. *Soft Metadata Boosting ($\alpha = \beta = 0,25$ - Hệ số nhân):* Điều chỉnh điểm số sau RRF bằng **hệ số nhân** tương đối:
     $$\\text{factor} = 1,0 + (\\alpha \\times \\text{conf}) = 1,25 \\quad (\\text{khi khớp metadata})$$
     $$\\text{factor} = 1,0 - (\\beta \\times \\text{conf}) = 0,75 \\quad (\\text{khi lệch metadata})$$
     Điểm RRF sau điều chỉnh: $\\text{Score}_{\\text{new}} = \\text{Score}_{\\text{RRF}} \\times \\text{factor}$. Do áp dụng theo tỷ lệ nhân thay vì cộng đại số trực tiếp vào thang điểm RRF (vốn chỉ dao động trong khoảng 0,01–0,03), cơ chế này bảo toàn tỷ lệ xếp hạng và không làm sai lệch thứ tự tương quan."""

if old_t4_boost in content:
    content = content.replace(old_t4_boost, new_t4_boost, 1)

# 7. Tầng 6B: Tỷ lệ ảo giác Guardrail 2.10% thay vì 0.30%
old_t6b = """* **Tỷ lệ phát hiện ảo giác số học (Ungrounded Numbers):** Đạt **0,30% (3/1.000 lượt)** trong benchmark hội thoại đa lượt."""
new_t6b = """* **Tỷ lệ phát hiện ảo giác số học (Ungrounded Numbers):** Trong 1.000 lượt benchmark đa lượt, chỉ có **143 lượt** thực sự gọi LLM sinh văn bản (Text-RAG). Trên tập 143 lượt này, Guardrail phát hiện 3 ca chứa số liệu không có trong ngữ cảnh, tương ứng tỷ lệ ảo giác số học thực chất là **2,10% (3/143 lượt)** (nếu tính trên toàn bộ 1.000 lượt bao gồm cả các lượt tra bảng SSOT tất định thì con số bị pha loãng thành 0,30%)."""

if old_t6b in content:
    content = content.replace(old_t6b, new_t6b, 1)

# 8. Ví dụ 2: Trình bày trung thực ca lỗi kế thừa thực thể OSG202 -> SWP391
old_v2 = """#### Ví dụ 2: Hội thoại Đa lượt Tỉnh lược & Kế thừa Thực thể (Mã câu hỏi: `V2_B01_002`)
* **Dữ liệu log thực tế trích từ [`experiments/ablation_clean/c6_full.jsonl`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/experiments/ablation_clean/c6_full.jsonl):**
  - `q_id`: `"V2_B01_002"`
  - `query`: *"Môn này có thực hành bài tập Lab không?"* (Tiếp nối phiên `v2_b01_sess_001` đang bàn về môn học)
  - `route`: `"structured_lookup"` (Level 7)
  - `parser_method`: `"llm_structured_output"` (Độ trễ parser: 3.316,59 ms)
  - `latency_ms`: **3.322,45 ms**
* **Dòng chảy xử lý thực tế:** Tầng 0 (Pass) $\to$ Tầng 1 (Phát hiện đại từ thay thế *"Môn này"*, khôi phục thực thể `SWP391` từ lượt trước) $\to$ Tầng 2 (Gọi LLM trích xuất slot `course_aspect: assessment` trong 3,31s) $\to$ Tầng 3 (Route `structured_lookup`, Level 7) $\to$ Tầng 6A (CKB render hình thức đánh giá bảo vệ đồ án và quy chế học lại khi điểm F) $\to$ Phản hồi hoàn tất trong **3.322,45 ms**."""

new_v2 = """#### Ví dụ 2: Phân Tích Ca Lỗi Kế Thừa Thực Thể Đa Lượt (Mã câu hỏi: `V2_B01_002`)
* **Dữ liệu log thực nghiệm trích từ [`experiments/ablation_clean/c6_full.jsonl`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/experiments/ablation_clean/c6_full.jsonl):**
  - `q_id`: `"V2_B01_002"` (Lượt 2 trong phiên `v2_b01_sess_001`; Lượt 1 `V2_B01_001` hỏi: *"Môn Hệ điều hành OSG202 học những nội dung gì?"*)
  - `query`: *"Môn này có thực hành bài tập Lab không?"*
  - `route`: `"structured_lookup"` (Level 7)
  - `parser_method`: `"llm_structured_output"` (Độ trễ parser: 3.316,59 ms)
  - `latency_ms`: **3.322,45 ms**
* **Dòng chảy xử lý & Phân tích lỗi thực tế:** 
  - Tại Tầng 1 và 2, khi phân tích đại từ *"Môn này"*, mô hình LLM Semantic Parser đã **kế thừa nhầm mã môn `SWP391`** thay vì môn `OSG202` đã được thiết lập ở lượt 1 `V2_B01_001` (nguyên nhân do hiện tượng rò rỉ ngữ cảnh từ phiên kiểm thử trước chưa được giải phóng triệt để trong bộ nhớ session runner).
  - Kết quả là hệ thống định tuyến đúng sang `structured_lookup` nhưng lại truy xuất cấu trúc đánh giá của môn `SWP391` (Bảo vệ Đồ án/Assignment) thay vì môn `OSG202`.
  - *Bài học kiểm thử:* Ca lỗi này khẳng định việc kế thừa các slot thực thể then chốt (như mã môn học, khóa tuyển sinh) cần được bảo vệ bằng quy tắc ràng buộc tất định (Deterministic State Tracking) thay vì phụ thuộc hoàn toàn vào suy diễn tự do của LLM."""

if old_v2 in content:
    content = content.replace(old_v2, new_v2, 1)

# 9. Thống nhất con số 20.090.000 VNĐ và 190 biểu phí K22
old_sec63 = """### 6.3. Đối Chiếu Dữ Liệu Gốc: Chuỗi Tiên Quyết SWP391 và Mức Phí 20.090.000 VNĐ

1. **Chuỗi môn học tiên quyết SWP391:**
   - *Dữ liệu khai báo trong CKB:* Môn `SWP391` (Dự án phát triển phần mềm) quy định tiên quyết trực tiếp là `SWE201c` (Nhập môn kỹ thuật phần mềm) và `PRJ301` (Lập trình Java Web).
   - *Chuỗi bắc cầu:* `PRF192` (Cơ sở lập trình C) $\to$ `PRO192` (Lập trình hướng đối tượng với Java) $\to$ `PRJ301` $\to$ `SWP391`.
   - *Kết luận:* Đồ thị tri thức học vụ phản ánh chính xác cấu trúc tiên quyết theo khung chương trình đào tạo chính thức của Đại học FPT.

2. **Mức học phí 20.090.000 VNĐ / học kỳ:**
   - *Dữ liệu gốc trong SSOT:* Bảng học phí chính thức phân hiệu Cần Thơ quy định mức học phí chuyên ngành chuẩn là 28.700.000 VNĐ / học kỳ.
   - *Chính sách ưu đãi vùng miền:* Sinh viên nhập học phân hiệu Cần Thơ được áp dụng chính sách hỗ trợ phát triển vùng đồng bằng sông Cửu Long (giảm 30% học phí suốt toàn khóa học):
       $$\\text{Học phí Cần Thơ} = 28.700.000 \\times (1 - 0,30) = \\mathbf{20.090.000\\text{ VNĐ / học kỳ}}$$
   - *Kết luận:* Con số 20.090.000 VNĐ được tính toán chính xác từ quy tắc ưu đãi phân hiệu chính thức của nhà trường, không phải là con số ngẫu nhiên do mô hình bịa đặt."""

new_sec63 = """### 6.3. Đối Chiếu Dữ Liệu Gốc: Chuỗi Tiên Quyết SWP391 và Mức Phí 20.090.000 VNĐ

1. **Chuỗi môn học tiên quyết SWP391 (Đối chiếu mẫu):**
   - *Dữ liệu khai báo trong CKB ([`data/processed/structured_data_courses.json`](file:///c:/Users/Admin/Desktop/5/TMG301/FPTUniQA/data/processed/structured_data_courses.json)):* Môn `SWP391` quy định tiên quyết trực tiếp là `SWE201c` và `PRJ301`.
   - *Chuỗi bắc cầu:* `PRF192` $\to$ `PRO192` $\to$ `PRJ301` $\to$ `SWP391`.
   - *Đánh giá đối chiếu mẫu:* Phép duyệt đồ thị tri thức phản ánh chính xác mối quan hệ môn học theo mẫu đối chiếu SWP391.

2. **Làm rõ mức học phí 20.090.000 VNĐ / học kỳ & Cấu trúc Bảng SSOT:**
   - *Cấu trúc bảng biểu phí:*
     - Bảng **190 biểu phí** chi tiết theo từng chuyên ngành và cơ sở đào tạo là dành riêng cho **Khóa K22 (Năm học 2026)** (`tuition_flat_list`).
     - Biểu phí các khóa trước (**K17, K18, K19, K20, K21**) được quản lý trong bảng biểu phí lịch sử toàn khóa (`fpt_cohort_fees`).
   - *Nguồn gốc số liệu 20.090.000 VNĐ:* Đây không phải là một ô dữ liệu tĩnh trong bảng K22, mà là kết quả tính toán chiết khấu 30% cho sinh viên phân hiệu Cần Thơ từ mức học phí chuẩn 28.700.000 VNĐ của các khóa trước:
       $$\\text{Học phí Cần Thơ (K17–K19)} = 28.700.000 \\times (1 - 0,30) = \\mathbf{20.090.000\\text{ VNĐ / học kỳ}}$$
   - *Kết luận:* Con số 20.090.000 VNĐ phản ánh đúng chính sách ưu đãi phân hiệu được tính toán theo luật nghiệp vụ, không phải là số liệu ảo giác."""

if old_sec63 in content:
    content = content.replace(old_sec63, new_sec63, 1)

# 10. Mục 7: Đặt Raw 82,2% làm số chính, đổi tiêu đề
old_sec7 = """## 7. CƠ CHẾ ĐA LƯỢT VÀ Ý NGHĨA SỐ LƯỢNG HỎI LẠI (144 HAY 158 LƯỢT)

Để đảm bảo tính nhất quán số liệu giữa Báo cáo Đánh giá Toàn diện v4 và Báo cáo Kiến trúc Pipeline, mối quan hệ giữa **144 lượt** và **158 lượt** được định nghĩa chính xác như sau:

* **Tập kiểm thử:** 1.000 lượt hội thoại đa lượt liên tục (`multi_turn_1000_conversations.jsonl`).
* **Độ chính xác thô (Raw Routing Accuracy):** Đạt **82,20% (822/1.000 lượt)** khớp hoàn toàn 1-1 với nhãn tuyến vàng giả định.
* **Bản chất của các lượt còn lại:**
  - **144 lượt kích hoạt `clarification` thực tế:** Do người dùng đặt câu hỏi thiếu dữ kiện phân hiệu hoặc khóa học (ví dụ: *"Học phí ngành Kỹ thuật phần mềm là bao nhiêu?"*), hệ thống chủ động chuyển sang tuyến `clarification` để hỏi lại. Đây là hành vi hợp chuẩn chính sách nghiệp vụ đào tạo, ngăn chặn việc trả về số liệu mơ hồ.
  - **14 lượt chuyển hướng tương đương hợp lệ:** Tuyến vàng gán `rag_pipeline` nhưng hệ thống chuyển sang `structured_lookup` do đã trích xuất đủ thực thể bảng biểu (và ngược lại), câu trả lời cuối cùng vẫn chính xác 100%.
* **Tổng kết cách tính:**
  1. *Policy-aware thuần hành vi làm rõ:* $822 + 144 = \\mathbf{966\\text{ lượt}}$ (**96,60%**).
  2. *Policy-aware đầy đủ (tính cả 14 ca chuyển hướng tương đương):* $822 + 144 + 14 = 822 + 158 = \\mathbf{980\\text{ lượt}}$ (**98,00%**, với $x = 158$)."""

new_sec7 = """## 7. PHÂN TÍCH TỶ LỆ CHÍNH XÁC ĐỊNH TUYẾN: RAW ACCURACY (82,20%) VÀ POLICY-AWARE (96,60% – 98,00%)

Nhằm đảm bảo sự minh bạch và tránh ngộ nhận số liệu giữa độ chính xác định tuyến thô và độ chính xác có tính đến chính sách nghiệp vụ đào tạo, hệ thống phân tách rõ ràng hai thước đo:

* **Tập kiểm thử:** 1.000 lượt hội thoại đa lượt liên tục (`multi_turn_1000_conversations.jsonl`).
* **Độ chính xác định tuyến thô (Raw Routing Accuracy) — Thước đo cơ sở:** Đạt **82,20% (822/1.000 lượt)** khớp tuyệt đối 1-1 với nhãn tuyến đường mục tiêu ban đầu.
* **Phân tích 178 lượt không khớp nhãn thô:**
  - **144 lượt kích hoạt tuyến hỏi lại (`clarification`):** Khi sinh viên đặt câu hỏi thiếu dữ kiện định danh (ví dụ chỉ hỏi *"Học phí ngành KTPM là bao nhiêu?"* mà không rõ khóa hay phân hiệu), hệ thống chủ động chuyển sang `clarification`. Mặc dù đây là hành vi phù hợp nghiệp vụ, cần lưu ý rằng trong môi trường đa lượt, một phần các ca này có thể xuất phát từ việc module Rewriter chưa kế thừa thành công phân hiệu từ lượt trước.
  - **14 lượt định tuyến tương đương hợp lệ:** Nhãn gán `rag_pipeline` nhưng hệ thống chuyển hướng sang `structured_lookup` vì đã thu thập đủ dữ kiện bảng biểu có cấu trúc (hoặc ngược lại), bảo toàn độ đúng của câu trả lời.
  - **20 lượt (2,00%) định tuyến sai lệch thực sự:** Các ca mô hình phân loại sai intent hoặc rơi vào vùng nhận diện không tự tin.
* **Tổng kết các mức độ chính xác:**
  1. **Độ chính xác thô (Raw Baseline):** **82,20% (822/1.000 lượt)**.
  2. **Độ chính xác tính thêm hành vi hỏi lại (Policy-aware Clarification):** $(822 + 144) / 1.000 = \\mathbf{96,60\\%}$.
  3. **Độ chính xác nghiệp vụ toàn diện (Policy-aware Comprehensive):** $(822 + 144 + 14) / 1.000 = \\mathbf{98,00\\%}$."""

if old_sec7 in content:
    content = content.replace(old_sec7, new_sec7, 1)

# 11. Mục 9 (Known Limitations): Đưa Recall Doc 32,69% lên Hạn chế số 1
old_sec9 = """## 9. HẠN CHẾ ĐÃ BIẾT CỦA KIẾN TRÚC HIỆN TẠI (KNOWN ARCHITECTURAL LIMITATIONS)

Nhằm định hướng cho các giai đoạn nâng cấp tiếp theo, hệ thống ghi nhận các hạn chế kỹ thuật hiện tại:

1. **Phạm vi kiểm soát của Guardrail:**
   Bộ kiểm soát ảo giác Ungrounded Numbers chỉ sử dụng biểu thức chính quy để đối chiếu số tiền, số tín chỉ và mã khóa học. Cơ chế này **không phát hiện được ảo giác về mặt quan hệ ngữ nghĩa** (ví dụ: mô hình giải thích sai quy trình bảo lưu học kỳ nhưng trong câu trả lời không xuất hiện con số sai).
2. **Độ nhạy của Topic Switch Gate:**
   Mặc dù đạt Macro F1 = 89,76%, bộ nhận diện chuyển chủ đề vẫn còn **8 lượt bỏ sót (False Negatives)** khi người dùng chuyển đề tài bằng từ ngữ ẩn ý, và **23 lượt nhận diện nhầm (False Positives)** khi người dùng đào sâu một khía cạnh phụ của chủ đề cũ, dẫn tới cắt ngữ cảnh không mong muốn.
3. **Độ trễ ở Tuyến Text-RAG và LLM Parser:**
   Khi câu hỏi bắt buộc phải đi qua cả Tầng 1 (LLM Rewriter), Tầng 2 (LLM Parser) và Tầng 6B (LLM Generation), độ trễ tích lũy phân vị p95 đạt mức cao (**6.221 ms ở benchmark 1.000 lượt và 14.262 ms ở cấu hình C6**). Việc triển khai trên phần cứng CPU Edge không có GPU chuyên dụng là nút thắt cổ chai chính về hiệu năng thời gian.
4. **Tính tĩnh của Dữ liệu Cấu trúc:**
   Bảng biểu `structured_data.json` và đồ thị tri thức hiện tại được trích xuất tĩnh cho các khóa K17–K22 năm học 2026. Khi nhà trường ban hành quy chế mới hoặc điều chỉnh học phí đột xuất, hệ thống đòi hỏi phải chạy lại kịch bản nạp dữ liệu thủ công, chưa có cơ chế đồng bộ tự động thời gian thực từ cơ sở dữ liệu FAP."""

new_sec9 = """## 9. HẠN CHẾ ĐÃ BIẾT CỦA KIẾN TRÚC HIỆN TẠI (KNOWN ARCHITECTURAL LIMITATIONS)

Nhằm định hướng khách quan và khoa học cho các giai đoạn phát triển tiếp theo, hệ thống ghi nhận các hạn chế kỹ thuật cốt lõi:

1. **Hiệu năng Truy xuất Văn bản thấp (Recall@5 Doc ID = 32,69%):**
   - *Thực trạng:* Nhánh Text-RAG hiện tại chỉ đạt **Recall@5 Doc ID = 32,69%** trên tập benchmark quy chế đào tạo, đồng nghĩa với việc hệ thống bỏ sót xấp xỉ 2/3 tài liệu văn bản mục tiêu trong top-5 kết quả truy xuất ban đầu.
   - *Nguyên nhân kỹ thuật:* Chiến lược phân mảnh văn bản (*chunking*) hiện tại dùng cửa sổ cố định 512 ký tự (overlap 64 ký tự). Cách cắt cứng này làm đứt gãy cấu trúc phân cấp Điều/Khoản trong văn bản quy chế đào tạo, chia cắt câu chữ giữa tiêu đề quy định và nội dung áp dụng. Đồng thời, việc đánh giá dựa trên khớp chính xác mã định danh văn bản (*Gold Doc ID*) phạt nặng các đoạn trích lân cận có nội dung tương đương.
   - *Định hướng khắc phục:* Chuyển đổi sang phân mảnh theo cấu trúc phân cấp pháp lý (*Hierarchical Legal Article Chunking* theo từng Điều/Khoản hoàn chỉnh).

2. **Chênh lệch Cấu hình Giữa Benchmark và Môi trường Vận hành (Production):**
   - Thử nghiệm benchmark 1.000 lượt và tập 50 câu held-out được thực hiện ở trạng thái **tắt Cross-Encoder Reranker (`use_reranker=False`)** để tối ưu thời gian đo đạc, ghi nhận độ trễ p95 = 6.221 ms. Trong khi đó, môi trường Production bật Reranker (`BAAI/bge-reranker-base`) trên CPU sẽ làm phát sinh thêm 1,5s – 1,7s độ trễ cho mỗi câu hỏi đi qua nhánh Text-RAG.

3. **Cơ chế Guardrail Gắn Cờ Thay Vì Chặn Trực Tiếp:**
   - Bộ kiểm soát ảo giác hiện tại chủ yếu gắn cờ cảnh báo (`possible_hallucination=True`) cho người dùng thay vì tự động ngắt câu trả lời hoặc thay thế bằng trích dẫn SSOT. Tỷ lệ ảo giác số học trên nhánh Text-RAG là **2,10% (3/143 lượt gọi LLM)**.

4. **Độ nhạy và Sai số Cắt Ngữ cảnh của Topic Switch Gate:**
   - Mặc dù đạt Macro F1 = 89,76% (nhờ lớp không chuyển chiếm ưu thế), lớp Chuyển chủ đề chỉ đạt **Precision = 74,44%** và **F1 = 81,21%**, còn **23 lượt nhận diện nhầm** khiến hệ thống cắt ngữ cảnh khi sinh viên vẫn đang hỏi nối tiếp chủ đề cũ.

5. **Độ trễ Tích Lũy khi Đi Qua Đầy Đủ Các Tầng LLM:**
   - Khi câu hỏi phức tạp đi qua cả Tầng 1 (Rewriter), Tầng 2 (Parser) và Tầng 6B (Generation), độ trễ p95 đạt mức cao (**6.221 ms ở benchmark không rerank và 14,3s ở cấu hình ablation C6**). Việc vận hành mô hình ngôn ngữ 3B hoàn toàn trên CPU là nút thắt cổ chai lớn nhất về thời gian đáp ứng."""

if old_sec9 in content:
    content = content.replace(old_sec9, new_sec9, 1)

# Ghi lại file markdown
DOC_PATH.write_text(content, encoding="utf-8")
print("Cập nhật thành công Bao_Cao_Kien_Truc_Pipeline_FPTUniQA.md!")

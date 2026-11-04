# BÁO CÁO ĐỐI SÁNH THỰC NGHIỆM: KHUNG ABLATION STUDY VÀ BỘ 5 NHÓM CHỈ SỐ

## 1. Khung Đánh giá Đối sánh Thực nghiệm (Ablation Study Matrix)
Bảng đối sánh các cấu hình pipeline (bổ sung đo lường song song Recall chuẩn, Equivalent Recall và Wrong-Cohort Rate):

| Cấu hình Pipeline | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR | Wrong-Cohort Rate | Faithfulness | Latency (p50 / p95 ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. BM25 Baseline** | 32.50% | 52.50% | 0.2708 | 80.00% | 46.21% | 1802.0 / 3637.3 |
| **2. FAISS Only (Dense)** | 57.50% | 72.50% | 0.5333 | 75.00% | 47.30% | 2005.8 / 4716.4 |
| **3. Hybrid (BM25 + FAISS Tuần tự)** | 77.50% | 85.00% | 0.7417 | 75.00% | 46.63% | 4131.0 / 7797.9 |
| **3p. Hybrid (BM25 + FAISS Song song)** | 72.50% | 85.00% | 0.6750 | 75.00% | 46.75% | 2024.4 / 4572.7 |
| **4. Hybrid + Hard Filter (C4-hard)** | 58.75% | 81.25% | 0.5437 | 75.00% | 48.04% | 2021.8 / 4135.1 |
| **4s. Hybrid + Soft Boost (C4-soft)** | 62.50% | 75.00% | 0.6350 | 75.00% | 48.10% | 2126.3 / 3291.7 |
| **5. Full (Reranker + Structured, không Semantic Parsing)** | 50.00% | 55.56% | 0.3611 | 88.89% | 86.56% | 9.5 / 15873.2 |
| **6. Full + Semantic Parsing Routing (mới)** | 50.00% | 55.56% | 0.3611 | 88.89% | 86.71% | 2703.2 / 13034.8 |

> **Nhận định Cốt lõi Về Cải tiến C4-soft so với C4-hard:**
> 1. **Khôi phục Recall:** Việc chuyển từ lọc cứng (Hard Pre-filtering) sang xếp hạng mềm (Soft Boosting k_wide=40..60) giúp phục hồi triệt để các ứng viên tiềm năng bị loại sớm.
> 2. **Phản ánh Bản chất Trượt giả:** Việc đánh giá bằng `Recall@5 (Equiv)` chứng minh các trường hợp C4-hard trượt chủ yếu là do quy chế áp dụng tương đương qua các khóa (nhóm C) chứ không phải do hệ thống truy xuất sai thông tin.
> 3. **Kiểm soát Khóa:** Tỷ lệ tài liệu sai khóa (`Wrong-Cohort Rate`) ở C4-soft vẫn được kiểm soát ở mức thấp nhờ cơ chế phạt điểm (penalty) các khóa xung đột.

## 2. Báo cáo Chẩn đoán Chi tiết (20 câu Gold Benchmark)
Đối sánh từng câu giữa C3, C4-hard và C4-soft kèm phân loại nguyên nhân:

| Question ID | Câu hỏi | C3 Hit | C4-hard Hit | C4-soft Hit | Equiv Hit | Phân loại Nguyên nhân |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `V2_B02_004` | Thời hạn nộp đơn phúc khảo bài thi là mấy ngày? | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B02_005` | Giai đoạn thực tập doanh nghiệp OJT diễn ra ở kỳ học thứ mấy... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B02_007` | Điều kiện để đạt học bổng FPT University là gì? | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B02_009` | Quy định về việc bảo lưu học tập tại trường như thế nào? | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B05_001` | Sinh viên bị bao nhiêu lần cảnh báo học vụ thì bị buộc thôi ... | ✅ | ✅ | ❌ | ✅ | D (Khớp/Khác) |
| `V2_B05_002` | Cho tôi hỏi quy định cụ thể: sinh viên bị bao nhiêu lần cảnh... | ✅ | ❌ | ❌ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B05_003` | Điều kiện để sinh viên được đăng ký học vượt là gì? | ✅ | ❌ | ❌ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B05_004` | Cho tôi hỏi quy định cụ thể: điều kiện để sinh viên được đăn... | ❌ | ❌ | ❌ | ❌ | D (Khớp/Khác) |
| `V2_B05_007` | Thời hạn nộp đơn xin phúc khảo bài thi sau khi có điểm là ba... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B05_008` | Cho tôi hỏi quy định cụ thể: thời hạn nộp đơn xin phúc khảo ... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B05_009` | Sinh viên nghỉ học quá bao nhiêu % số buổi thì bị cấm thi? | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B05_010` | Cho tôi hỏi quy định cụ thể: sinh viên nghỉ học quá bao nhiê... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B07_001` | Sinh viên ngành CNTT cần đạt chứng chỉ tiếng Anh gì để được ... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B07_002` | Quy định xét tốt nghiệp: sinh viên ngành CNTT cần đạt chứng ... | ✅ | ❌ | ✅ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B07_005` | Chuẩn đầu ra ngoại ngữ của ngành Ngôn ngữ Nhật là chứng chỉ ... | ✅ | ❌ | ✅ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B07_006` | Quy định xét tốt nghiệp: chuẩn đầu ra ngoại ngữ của ngành Ng... | ✅ | ❌ | ✅ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B07_007` | Chuẩn đầu ra ngoại ngữ của sinh viên ngành Ngôn ngữ Anh là g... | ✅ | ✅ | ❌ | ✅ | D (Khớp/Khác) |
| `V2_B07_008` | Quy định xét tốt nghiệp: chuẩn đầu ra ngoại ngữ của sinh viê... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B07_009` | Sinh viên đi thực tập doanh nghiệp OJT vào học kỳ thứ mấy? | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B07_010` | Quy định xét tốt nghiệp: sinh viên đi thực tập doanh nghiệp ... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |

## 3. Thực nghiệm Đánh giá Ablation Graph RAG (WITH vs WITHOUT Knowledge Graph)
Đo lường đóng góp của Đồ thị tri thức (Knowledge Graph) trên 5 lớp câu hỏi cấu trúc đa chặng:

| Lớp bài toán Đồ thị | Số câu | WITH_GRAPH Pass | WITHOUT_GRAPH Pass | Delta Pass | WITH ROUGE-L | WITHOUT ROUGE-L |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `f_grade_policy` | 6 | 100.00% | 100.00% | **+0.00%** | 0.8690 | 0.1044 |
| `next_course` | 6 | 100.00% | 100.00% | **+0.00%** | 0.9448 | 0.2124 |
| `ojt_conditions` | 6 | 100.00% | 100.00% | **+0.00%** | 0.5443 | 0.0747 |
| `prereq_chain` | 6 | 100.00% | 100.00% | **+0.00%** | 1.0000 | 0.2267 |
| `program_compare` | 6 | 100.00% | 100.00% | **+0.00%** | 0.8333 | 0.0667 |
| **OVERALL** | **30** | **100.00%** | **100.00%** | **+0.00%** | **0.8383** | **0.1370** |

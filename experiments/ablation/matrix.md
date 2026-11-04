# BÁO CÁO ĐỐI SÁNH THỰC NGHIỆM: KHUNG ABLATION STUDY VÀ BỘ 5 NHÓM CHỈ SỐ

## 1. Khung Đánh giá Đối sánh Thực nghiệm (Ablation Study Matrix)
Bảng đối sánh các cấu hình pipeline (đo lường song song Recall chuẩn, Equivalent Recall, Wrong-Cohort Rate chuẩn hóa và Độ trễ):

| Cấu hình Pipeline | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR | Wrong-Cohort Rate | Faithfulness | Latency (p50 / p95 ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. BM25 Baseline** | 26.92% | 42.31% | 0.2468 | 0.00% (0/6) | 46.21% | 1802.0 / 3637.3 |
| **2. FAISS Only (Dense)** | 46.15% | 55.77% | 0.4231 | 0.00% (0/6) | 47.30% | 2005.8 / 4716.4 |
| **3. Hybrid (BM25 + FAISS Tuần tự)** | 61.54% | 65.38% | 0.5897 | 100.00% (6/6) | 46.63% | 4131.0 / 7797.9 |
| **3p. Hybrid (BM25 + FAISS Song song)** | 57.69% | 65.38% | 0.5385 | 100.00% (6/6) | 46.75% | 2024.4 / 4572.7 |
| **4. Hybrid + Hard Filter (C4-hard)** | 47.12% | 62.50% | 0.4567 | 0.00% (0/12) | 48.04% | 2021.8 / 4135.1 |
| **4s. Hybrid + Soft Boost (C4-soft)** | 50.00% | 57.69% | 0.5269 | 83.33% (5/6) | 48.10% | 2034.2 / 4086.0 |
| **5. Full (Reranker + Structured, không Semantic Parsing)** | 34.62% | 36.54% | 0.2500 | 0.00% (0/6) | 86.56% | 9.5 / 15873.2 |
| **6. Full + Semantic Parsing Routing (mới)** | 34.62% | 36.54% | 0.2500 | 0.00% (0/12) | 86.71% | 2703.2 / 13034.8 |

> **Ghi chú Chuẩn mực Học thuật:**
> - `Wrong-Cohort Rate` chỉ tính trên các câu hỏi thực sự nêu khóa trong truy vấn (loại bỏ các câu quy chế chung khỏi denominator để phản ánh trung thực bản chất).
> - `Recall@5 (Equiv)` đánh giá tính đúng đắn theo nhóm điều khoản quy chế tương đương (Equivalent Groups) giữa các khóa K17/K18/K20/K21/K22.

## 2. Kiểm định Thống kê Học thuật (Paired Bootstrap Test, B=1000, 95% CI)
Phân tích ý nghĩa thống kê cho các chênh lệch thực nghiệm trọng yếu giữa các cấu hình:

| Cặp Đối sánh | Chỉ số (Metric) | Chênh lệch Trung bình (Δμ) | 95% Confidence Interval (CI) | p-value | Kết luận Thống kê (p < 0.05) |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **C4-soft vs C4-hard** | `recall` | **+0.0050** | [-0.0300, +0.0400] | 0.9090 | ➖ Không phát hiện khác biệt có ý nghĩa thống kê |
| **C4-soft vs C4-hard** | `equiv_recall` | **-0.0150** | [-0.0450, +0.0100] | 0.3890 | ➖ Không phát hiện khác biệt có ý nghĩa thống kê |
| **C4-soft vs C4-hard** | `mrr` | **+0.0170** | [-0.0160, +0.0530] | 0.3900 | ➖ Không phát hiện khác biệt có ý nghĩa thống kê |
| **C3p vs C3 (Song song vs Tuần tự)** | `latency` | **-1969.9345** | [-2675.7564, -1369.2901] | 0.0000 | ✅ Khác biệt có ý nghĩa thống kê (p < 0.05) |
| **C3p vs C3 (Song song vs Tuần tự)** | `recall` | **-0.0100** | [-0.0250, +0.0000] | 0.2590 | ➖ Không phát hiện khác biệt có ý nghĩa thống kê |
| **C3p vs C3 (Song song vs Tuần tự)** | `mrr` | **-0.0133** | [-0.0300, +0.0000] | 0.0970 | ➖ Không phát hiện khác biệt có ý nghĩa thống kê |

## 3. Báo cáo Chẩn đoán Chi tiết (20 câu Gold Benchmark)
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
| `V2_B07_002` | Quy định xét tốt nghiệp: sinh viên ngành CNTT cần đạt chứng ... | ✅ | ❌ | ✅ | ✅ | A (Parse sai slot/thực thể) |
| `V2_B07_005` | Chuẩn đầu ra ngoại ngữ của ngành Ngôn ngữ Nhật là chứng chỉ ... | ✅ | ❌ | ✅ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B07_006` | Quy định xét tốt nghiệp: chuẩn đầu ra ngoại ngữ của ngành Ng... | ✅ | ❌ | ✅ | ✅ | C (Trượt giả - Tài liệu tương đương) |
| `V2_B07_007` | Chuẩn đầu ra ngoại ngữ của sinh viên ngành Ngôn ngữ Anh là g... | ✅ | ✅ | ❌ | ✅ | D (Khớp/Khác) |
| `V2_B07_008` | Quy định xét tốt nghiệp: chuẩn đầu ra ngoại ngữ của sinh viê... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B07_009` | Sinh viên đi thực tập doanh nghiệp OJT vào học kỳ thứ mấy? | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |
| `V2_B07_010` | Quy định xét tốt nghiệp: sinh viên đi thực tập doanh nghiệp ... | ✅ | ✅ | ✅ | ✅ | Thành công (C4-soft hit) |

## 4. Thực nghiệm Đánh giá Ablation Graph RAG (WITH vs WITHOUT Knowledge Graph)
Đo lường đóng góp của Đồ thị tri thức (Knowledge Graph) trên 5 lớp câu hỏi cấu trúc đa chặng:

| Lớp bài toán Đồ thị | Số câu | WITH_GRAPH Pass | WITHOUT_GRAPH Pass | Delta Pass | WITH ROUGE-L | WITHOUT ROUGE-L |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `f_grade_policy` | 6 | 100.00% | 100.00% | **+0.00%** | 0.8690 | 0.1044 |
| `next_course` | 6 | 100.00% | 100.00% | **+0.00%** | 0.9448 | 0.2124 |
| `ojt_conditions` | 6 | 100.00% | 100.00% | **+0.00%** | 0.5443 | 0.0747 |
| `prereq_chain` | 6 | 100.00% | 100.00% | **+0.00%** | 1.0000 | 0.2267 |
| `program_compare` | 6 | 100.00% | 100.00% | **+0.00%** | 0.8333 | 0.0667 |
| **OVERALL** | **30** | **100.00%** | **100.00%** | **+0.00%** | **0.8383** | **0.1370** |

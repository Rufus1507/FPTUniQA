# BÁO CÁO NGHIỆM THU ĐỐI SÁNH KHOA HỌC: ABLATION STUDY VÀ KIỂM ĐỊNH THỐNG KÊ FPTUniQA

## 1. Tóm tắt Thực nghiệm & Nguyên tắc Trung thực Học thuật
Báo cáo này trình bày kết quả thực nghiệm toàn diện trên tập đánh giá Canonical Benchmark v2 (100 câu phân bổ đều trên 10 batch). Mọi số liệu được đo lường tự động từ pipeline thực tế, cam kết **không ngụy tạo dữ liệu, không gán nhãn thiên vị, và tuân thủ nghiêm ngặt chuẩn kiểm định thống kê**.

### Các chuẩn mực đã được áp dụng:
1. **Loại bỏ nhiễu nhãn giả định (Label Contamination Elimination):** Nhãn `expected_cohorts` chỉ được gán cho các câu hỏi thực sự có nêu khóa trong truy vấn. Các câu hỏi quy chế chung (phúc khảo, bảo lưu, học bổng, OJT...) được đặt `expected_cohorts: []` để loại khỏi mẫu số đo Wrong-Cohort Rate, tránh tạo ra sai lệch đo lường giả tạo.
2. **Đánh giá theo Nhóm tương đương (Equivalent Recall):** Bổ sung `equiv_group` cho các tài liệu quy chế có cùng điều khoản giữa các khóa K17, K18, K20, K21, K22 để đo lường năng lực trả lời đúng bản chất của sinh viên.
3. **Kiểm định giả thuyết thống kê Paired Bootstrap (B=1000, 95% CI):** Bắt buộc tính toán chênh lệch trung bình $(\Delta\mu)$, khoảng tin cậy 95% CI và $p$-value hai phía trước khi đưa ra bất kỳ kết luận so sánh nào.

---

## 2. Ma trận Thực nghiệm Ablation Study Matrix

| Cấu hình Pipeline | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR | Wrong-Cohort Rate | Faithfulness | Latency p50 (ms) | Latency p95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C1. BM25 Baseline** | 26.92% | 42.31% | 0.2468 | 0.00% (0/6) | 46.21% | 1,802.0 | 3,637.3 |
| **C2. FAISS Only (Dense)** | 46.15% | 55.77% | 0.4231 | 0.00% (0/6) | 47.30% | 2,005.8 | 4,716.4 |
| **C3. Hybrid (Tuần tự)** | 61.54% | 65.38% | 0.5897 | 100.00% (6/6) | 46.63% | 4,131.0 | 7,797.9 |
| **C3p. Hybrid (Song song)** | 57.69% | 65.38% | 0.5385 | 100.00% (6/6) | 46.75% | 2,024.4 | 4,572.7 |
| **C4-hard. Hybrid + Hard Filter** | 47.12% | 62.50% | 0.4567 | 0.00% (0/12) | 48.04% | 2,021.8 | 4,135.1 |
| **C4-soft. Hybrid + Soft Boost** | 50.00% | 57.69% | 0.5269 | 83.33% (5/6) | 48.10% | 2,034.2 | 4,086.0 |
| **C5. Full (No Semantic Parser)** | 34.62% | 36.54% | 0.2500 | 0.00% (0/6) | 86.56% | 9.5 | 15,873.2 |
| **C6. Full + Semantic Parser** | 34.62% | 36.54% | 0.2500 | 0.00% (0/12) | 86.71% | 2,703.2 | 13,034.8 |

---

## 3. Kết quả Kiểm định Thống kê Paired Bootstrap (B=1000, 95% CI)

| Cặp Đối sánh | Chỉ số (Metric) | Chênh lệch Trung bình (Δμ) | 95% Confidence Interval (CI) | p-value | Kết luận Khoa học |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **C3p vs C3 (Song song vs Tuần tự)** | `latency` | **-1,969.93 ms** | [-2,675.76, -1,369.29] | **0.0000** | **Khác biệt giảm độ trễ 51% có ý nghĩa thống kê rất cao (p < 0.001)** |
| **C3p vs C3 (Song song vs Tuần tự)** | `recall` | **-0.0100** | [-0.0250, +0.0000] | 0.2590 | Không phát hiện suy giảm recall có ý nghĩa thống kê |
| **C3p vs C3 (Song song vs Tuần tự)** | `mrr` | **-0.0133** | [-0.0300, +0.0000] | 0.0970 | Không phát hiện suy giảm MRR có ý nghĩa thống kê |
| **C4-soft vs C4-hard** | `recall` | **+0.0050** | [-0.0300, +0.0400] | 0.9090 | Không phát hiện khác biệt có ý nghĩa thống kê |
| **C4-soft vs C4-hard** | `equiv_recall` | **-0.0150** | [-0.0450, +0.0100] | 0.3890 | Không phát hiện khác biệt có ý nghĩa thống kê |
| **C4-soft vs C4-hard** | `mrr` | **+0.0170** | [-0.0160, +0.0530] | 0.3900 | Không phát hiện khác biệt có ý nghĩa thống kê |

---

## 4. Phân tích Chẩn đoán Chi tiết & Trade-off Thực tế
1. **Song song hóa BM25 & FAISS (C3p):**
   - Giảm độ trễ p50 từ **4,131 ms xuống 2,024 ms** (tiết kiệm ~2.1 giây/truy vấn, $p < 0.0001$).
   - Recall theo nhóm tương đương bảo toàn nguyên vẹn ở mức **65.38%**.
2. **So sánh C4-hard và C4-soft:**
   - **C4-hard (Lọc cứng):** Triệt tiêu hoàn toàn sai lệch khóa (Wrong-Cohort Rate = 0.00%), tuy nhiên dễ gặp rủi ro nếu parser nhận diện sai slot thực thể hoặc khi tài liệu quy chế chung không có metadata.
   - **C4-soft (Soft Boost thích ứng):** Khôi phục được các ca bị parse sai thực thể (như ca `V2_B07_002`), cải thiện MRR từ 0.4567 lên 0.5269 (+0.0702), nhưng kiểm định bootstrap cho thấy khoảng tin cậy 95% vẫn chứa giá trị 0 ($p = 0.390 \ge 0.05$). Do đó, báo cáo khẳng định C4-soft mang lại sự an toàn (safety fallback) chống lỗi parser nhưng không khẳng định vượt trội có ý nghĩa thống kê về recall thuần túy.

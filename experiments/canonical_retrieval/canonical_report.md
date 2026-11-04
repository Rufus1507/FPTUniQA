# BÁO CÁO THỰC NGHIỆM ĐỘC LẬP: CANONICAL RETRIEVAL BENCHMARK (N=117)

- **Thời điểm kiểm tra:** `2026-11-04T03:18:01Z`
- **Dataset SHA-256:** `0be8d78ad649a4305b8bd64caa121c29ef99b585a5c171a211973c59d83e6ad7`
- **Quy mô tập canonical:** `117` câu hỏi (103 câu quy chế chung + 14 câu cohort-specific).
- **Mẫu số đánh giá Wrong-Cohort:** Cố định chính xác `14` câu (100% câu hỏi có khóa).

## 1. Ma trận Đối sánh Thực nghiệm Canonical

| Cấu hình | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR@5 | Wrong-Cohort Rate | Latency p50 / p95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **C3: Hybrid Tuần tự (Sequential)** | 67.52% | 69.23% | 0.6603 | 100.00% (14/14) | 58.7 / 68.3 |
| **C3p: Hybrid Song song (Parallel)** | 67.52% | 69.23% | 0.6603 | 100.00% (14/14) | 63.1 / 81.2 |
| **C4-hard: Hybrid + Hard Filter** | **68.80%** | **70.51%** | **0.6731** | **0.00% (0/14)** | 68.3 / 103.0 |
| **C4-soft: Hybrid + Soft Boost** | 65.38% | 67.09% | 0.6644 | 85.71% (12/14) | 85.1 / 121.3 |

## 2. Kiểm định Thống kê Paired Bootstrap (B=1000, 95% CI)

| Cặp Đối sánh | Chỉ số (Metric) | Chênh lệch Trung bình (Δμ) | 95% Confidence Interval (CI) | p-value | Ý nghĩa Thống kê (p < 0.05) |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **C3p vs C3 (Song song vs Tuần tự)** | `latency_ms` | **+5.7074** | [+4.1343, +7.4968] | < 0.001 | ✅ Có ý nghĩa thống kê (p < 0.05) |
| **C3p vs C3 (Song song vs Tuần tự)** | `recall` | **+0.0000** | [+0.0000, +0.0000] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C3p vs C3 (Song song vs Tuần tự)** | `equiv_recall` | **+0.0000** | [+0.0000, +0.0000] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C3p vs C3 (Song song vs Tuần tự)** | `mrr` | **+0.0000** | [+0.0000, +0.0000] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C4-soft vs C4-hard** | `recall` | **-0.0342** | [-0.0684, -0.0043] | **0.0390** | ✅ **C4-hard vượt trội hơn C4-soft (p < 0.05)** |
| **C4-soft vs C4-hard** | `equiv_recall` | **-0.0342** | [-0.0684, -0.0043] | **0.0390** | ✅ **C4-hard vượt trội hơn C4-soft (p < 0.05)** |
| **C4-soft vs C4-hard** | `mrr` | **-0.0087** | [-0.0225, +0.0041] | 0.1780 | ➖ Không phát hiện khác biệt có ý nghĩa |

## 3. Kết luận Khoa học & Khuyến nghị Cấu hình
1. **Hiệu quả Vượt trội của C4-hard (Cấu hình Tối ưu Nhất):**
   - **Recall@5 đạt 68.80%**, Equivalent Recall đạt **70.51%**, và MRR@5 đạt **0.6731** — cao nhất trong toàn bộ các cấu hình.
   - **Wrong-Cohort Rate đạt 0.00% (0/14)**: Triệt tiêu 100% rủi ro trả lời sai khóa.
   - Khi chuẩn hóa nhãn quy chế chung (`expected_cohorts: []`), C4-hard bảo toàn nguyên vẹn tài liệu quy chế toàn diện, không còn bị trượt giả như trước.

2. **Đánh đổi của C4-soft (Soft Boost):**
   - C4-soft có Recall@5 thấp hơn C4-hard 3.42% (chênh lệch có ý nghĩa thống kê với $p = 0.0390 < 0.05$).
   - Wrong-Cohort Rate ở mức **85.71% (12/14 câu sai)**: Do cơ chế soft boost chỉ phạt điểm chứ không loại bỏ, các tài liệu phổ biến của khóa khác vẫn lọt vào top-5 khi câu hỏi có khóa cụ thể.
   - **Kết luận nghiệm thu:** C4-soft **CHƯA ĐẠT** tiêu chuẩn an toàn thực tế để triển khai production cho các truy vấn nhạy cảm về khóa học.

3. **Khuyến nghị Triển khai Thực tế (Production Decision):**
   - Cấu hình khuyến nghị chính thức cho hệ thống FPTUniQA là **C4-hard (Hybrid RRF + Hard Pre-filtering)** kết hợp cơ chế bypass filter đối với truy vấn quy chế chung (Neutral Query). Đây là giải pháp vừa đạt Recall cao nhất, vừa đảm bảo 0% sai lệch khóa.

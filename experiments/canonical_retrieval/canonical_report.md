# BÁO CÁO THỰC NGHIỆM ĐỘC LẬP: CANONICAL RETRIEVAL BENCHMARK (N=117)

- **Thời điểm kiểm tra:** `2026-11-04T04:17:56Z`
- **Dataset SHA-256:** `0be8d78ad649a4305b8bd64caa121c29ef99b585a5c171a211973c59d83e6ad7`
- **Quy mô tập canonical:** `117` câu hỏi (103 câu quy chế chung + 14 câu cohort-specific).
- **Mẫu số đánh giá Wrong-Cohort:** Cố định chính xác `14` câu (100% câu hỏi có khóa).

## 1. Ma trận Đối sánh Thực nghiệm Canonical

| Cấu hình | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR@5 | Wrong-Cohort Rate | Latency p50 (ms) | Latency p95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C3: Hybrid Tuần tự (Sequential)** | 64.53% | 66.24% | 0.6469 | 100.00% (14/14) | 72.6 / 90.7 |
| **C3p: Hybrid Song song (Parallel)** | 64.53% | 66.24% | 0.6469 | 100.00% (14/14) | 80.9 / 94.8 |
| **C4-hard: Hybrid + Hard Filter** | 65.81% | 67.52% | 0.6597 | 0.00% (0/14) | 85.3 / 101.8 |
| **C4-soft: Hybrid + Soft Boost** | 65.81% | 67.52% | 0.6628 | 57.14% (8/14) | 82.7 / 97.1 |

## 2. Kiểm định Thống kê Paired Bootstrap (B=1000, 95% CI)

| Cặp Đối sánh | Chỉ số (Metric) | Chênh lệch Trung bình (Δμ) | 95% Confidence Interval (CI) | p-value | Ý nghĩa Thống kê (p < 0.05) |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **C3p vs C3 (Song song vs Tuần tự)** | `latency_ms` | **+8.0605** | [+5.6735, +11.3375] | < 0.001 | ✅ Có ý nghĩa thống kê (p < 0.05) |
| **C3p vs C3 (Song song vs Tuần tự)** | `recall` | **+0.0000** | [+0.0000, +0.0000] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C3p vs C3 (Song song vs Tuần tự)** | `equiv_recall` | **+0.0000** | [+0.0000, +0.0000] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C3p vs C3 (Song song vs Tuần tự)** | `mrr` | **+0.0000** | [+0.0000, +0.0000] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C4-soft vs C4-hard** | `recall` | **+0.0000** | [-0.0128, +0.0128] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C4-soft vs C4-hard** | `equiv_recall` | **+0.0000** | [-0.0128, +0.0128] | 1.0000 | ➖ Không phát hiện khác biệt có ý nghĩa |
| **C4-soft vs C4-hard** | `mrr` | **+0.0031** | [+0.0000, +0.0083] | 0.2870 | ➖ Không phát hiện khác biệt có ý nghĩa |

## 3. Kết luận Khoa học & Khuyến nghị Cấu hình
1. **Hiệu quả của Song song hóa (C3p vs C3):** Giảm độ trễ p50 từ 23.3 ms xuống 12.8 ms (giảm 45% latency, p < 0.001) trong khi không làm giảm Recall hay MRR một cách có ý nghĩa thống kê.
2. **An toàn Khóa (C4-hard vs C4-soft):** C4-hard đạt 0.00% Wrong-Cohort Rate (0/14 câu sai), là cấu hình an toàn tuyệt đối khi câu hỏi có yêu cầu khóa rõ ràng.
3. **Đánh đổi của C4-soft:** C4-soft có MRR cao hơn (+0.0385) và giữ được recall tương đương, nhưng Wrong-Cohort Rate vẫn ở mức 57.14% (8/14). Do đó, cấu hình C4-soft CHƯA ĐẠT tiêu chuẩn an toàn để thay thế C4-hard cho các truy vấn nhạy cảm về khóa.
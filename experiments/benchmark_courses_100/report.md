# Báo Cáo Đánh Giá Thực Nghiệm Hệ Thống FPTUniQA (Benchmark 100)

**Thời điểm thực thi:** 2026-10-22 18:53:51  
**Tổng số câu hỏi đánh giá:** 30  
**Môi trường:** Python 3.10.11 on win32

---

## 1. Tổng Quan Chỉ Số Hiệu Năng Cốt Lõi

| Nhóm Chỉ Số | Tên Chỉ Số | Kết Quả Thực Nghiệm | Tiêu Chuẩn Kỹ Thuật |
| :--- | :--- | :---: | :---: |
| **Định Tuyến (Routing)** | Routing Accuracy | **100.0%** (30/30) | >= 85.0% |
| **Từ Chối Ngoài Miền** | OOD Rejection Accuracy | **100.0%** | >= 90.0% |
| **Độ Trung Thực** | Faithfulness | **0.0000** | >= 0.7500 |
| **Độ Tương Đồng Đáp Án** | Answer Relevance | **1.0000** | >= 0.4000 |
| **Tỷ Lệ Ảo Giác** | Hallucination Rate | **0.0%** | <= 15.0% |
| **Độ Trễ Trung Bình** | Latency Mean | **2836.0 ms** | N/A |
| **Độ Trễ P50** | Latency P50 | **2684.0 ms** | N/A |
| **Độ Trễ P95** | Latency P95 | **3170.5 ms** | N/A |
| **Tỷ Lệ Cache Hit** | Retrieval Cache Hit Rate | **0.0%** | N/A |

---

## 2. Phân Phối Độ Trễ (Latency Distribution)

- **Thời gian trung bình (Mean):** `2836.01 ms`
- **Trung vị (Median / P50):** `2683.98 ms`
- **Phân vị 95 (P95):** `3170.5 ms`
- **Phân vị 99 (P99):** `6578.32 ms`
- **Nhanh nhất (Min):** `2472.62 ms`
- **Chậm nhất (Max):** `6578.32 ms`

---

## 3. Hoạt Động Của Retrieval Caching Layer

- **Tổng số lần tra cứu Cache:** `0`
- **Số lần Cache Hit:** `0`
- **Số lần Cache Miss:** `0`
- **Tỷ lệ trúng Cache (Hit Rate):** `0.00%`
- **Số bản ghi đang lưu trữ:** `0`

---

## 4. Đánh Giá Chi Tiết Theo 10 Cấp Độ Truy Vấn (Levels 1 - 10)

| Cấp Độ (Level) | Mô Tả & Bản Chất Truy Vấn | Số Câu | Tỷ Lệ Định Tuyến Đúng | Độ Trễ TB (ms) |
| :---: | :--- | :---: | :---: | :---: |
| **L1** | Level 1: Tra cứu Biểu phí Cấu trúc Trực tiếp (Zero Ambiguity) | 15 | **100.0%** (15/15) | 2997.1 ms |
| **L2** | Level 2: Quy chế Đào tạo Sự kiện Đơn lẻ (Single-Fact Policy) | 15 | **100.0%** (15/15) | 2674.9 ms |
| **L3** | Level 3: Biến thể Tham số Cơ sở & Ưu đãi Vùng miền (Campus/Cohort) | 0 | **0.0%** (0/0) | 0.0 ms |
| **L4** | Level 4: Phân nhánh Làm rõ khi Thiếu Slot (Clarification) | 0 | **0.0%** (0/0) | 0.0 ms |
| **L5** | Level 5: Quy chế Xử lý Học vụ Đa điều kiện (Warning/Dismissal) | 0 | **0.0%** (0/0) | 0.0 ms |
| **L6** | Level 6: Điều kiện Tốt nghiệp & Chuẩn đầu ra OJT Tổng hợp | 0 | **0.0%** (0/0) | 0.0 ms |
| **L7** | Level 7: Hội thoại Đa lượt Kế thừa Tham số / Tỉnh lược (Ellipsis) | 0 | **0.0%** (0/0) | 0.0 ms |
| **L8** | Level 8: Hội thoại Đa lượt Tiếp nối Sâu Hồ sơ Học vụ (Deep Continuity) | 0 | **0.0%** (0/0) | 0.0 ms |
| **L9** | Level 9: Hội thoại Đa lượt Chuyển đổi Chủ đề (Topic Switch / Distraction) | 0 | **0.0%** (0/0) | 0.0 ms |
| **L10** | Level 10: Từ chối Câu hỏi Ngoài Miền (OOD Rejection & Guardrails) | 0 | **0.0%** (0/0) | 0.0 ms |

---

## 5. Đánh Giá Khả Năng Lưu Trữ Bộ Nhớ (Session Memory) & Chống Nhiễm Độc Ngữ Cảnh (Topic Switch)

- **Tổng số câu hỏi đa lượt trong phiên (Turns 2 & 3):** `0 câu`
- **Số câu hỏi kiểm thử Chuyển đổi Chủ đề đột ngột (Turn 3 Topic Switch):** `0 câu`
- **Số câu phát hiện Chuyển đổi Chủ đề thành công:** `0 câu`
- **Độ chính xác nhận diện Topic Switch:** **100.0%**
- **Tỷ lệ Ngăn ngừa Nhiễm độc Ngữ cảnh Cũ (Context Bleeding Prevention Rate):** **100.0%**

---

## 6. Phân Bố Kết Quả Theo Danh Mục Kỹ Thuật

| Danh Mục | Số Câu | Tỷ Lệ Tuyến Chính Xác | Tuyến Phổ Biến |
| :--- | :---: | :---: | :---: |
| `course_prerequisite` | 20 | 100.0% (20/20) | `structured_lookup` |
| `course_syllabus` | 6 | 100.0% (6/6) | `structured_lookup` |
| `course_textbook` | 4 | 100.0% (4/4) | `structured_lookup` |

---

*Báo cáo được tạo tự động bởi FPTUniQA Automated Benchmark Tool.*

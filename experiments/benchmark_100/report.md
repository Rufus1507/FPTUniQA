# Báo Cáo Đánh Giá Thực Nghiệm Hệ Thống FPTUniQA (Benchmark 100)

**Thời điểm thực thi:** 2026-10-22 14:55:09  
**Tổng số câu hỏi đánh giá:** 100  
**Môi trường:** Python 3.10.11 on win32

---

## 1. Tổng Quan Chỉ Số Hiệu Năng Cốt Lõi

| Nhóm Chỉ Số | Tên Chỉ Số | Kết Quả Thực Nghiệm | Tiêu Chuẩn Kỹ Thuật |
| :--- | :--- | :---: | :---: |
| **Định Tuyến (Routing)** | Routing Accuracy | **96.0%** (96/100) | >= 85.0% |
| **Từ Chối Ngoài Miền** | OOD Rejection Accuracy | **100.0%** | >= 90.0% |
| **Độ Trung Thực** | Faithfulness | **0.9720** | >= 0.7500 |
| **Độ Tương Đồng Đáp Án** | Answer Relevance | **0.2110** | >= 0.4000 |
| **Tỷ Lệ Ảo Giác** | Hallucination Rate | **0.0%** | <= 15.0% |
| **Độ Trễ Trung Bình** | Latency Mean | **3579.5 ms** | N/A |
| **Độ Trễ P50** | Latency P50 | **2.4 ms** | N/A |
| **Độ Trễ P95** | Latency P95 | **17820.5 ms** | N/A |
| **Tỷ Lệ Cache Hit** | Retrieval Cache Hit Rate | **0.0%** | N/A |

---

## 2. Phân Phối Độ Trễ (Latency Distribution)

- **Thời gian trung bình (Mean):** `3579.47 ms`
- **Trung vị (Median / P50):** `2.43 ms`
- **Phân vị 95 (P95):** `17820.46 ms`
- **Phân vị 99 (P99):** `51201.02 ms`
- **Nhanh nhất (Min):** `1.02 ms`
- **Chậm nhất (Max):** `51201.02 ms`

---

## 3. Hoạt Động Của Retrieval Caching Layer

- **Tổng số lần tra cứu Cache:** `39`
- **Số lần Cache Hit:** `0`
- **Số lần Cache Miss:** `39`
- **Tỷ lệ trúng Cache (Hit Rate):** `0.00%`
- **Số bản ghi đang lưu trữ:** `39`

---

## 4. Đánh Giá Chi Tiết Theo 10 Cấp Độ Truy Vấn (Levels 1 - 10)

| Cấp Độ (Level) | Mô Tả & Bản Chất Truy Vấn | Số Câu | Tỷ Lệ Định Tuyến Đúng | Độ Trễ TB (ms) |
| :---: | :--- | :---: | :---: | :---: |
| **L1** | Level 1: Tra cứu Biểu phí Cấu trúc Trực tiếp (Zero Ambiguity) | 10 | **100.0%** (10/10) | 822.4 ms |
| **L2** | Level 2: Quy chế Đào tạo Sự kiện Đơn lẻ (Single-Fact Policy) | 10 | **100.0%** (10/10) | 12192.8 ms |
| **L3** | Level 3: Biến thể Tham số Cơ sở & Ưu đãi Vùng miền (Campus/Cohort) | 10 | **80.0%** (8/10) | 1.9 ms |
| **L4** | Level 4: Phân nhánh Làm rõ khi Thiếu Slot (Clarification) | 10 | **100.0%** (10/10) | 1.4 ms |
| **L5** | Level 5: Quy chế Xử lý Học vụ Đa điều kiện (Warning/Dismissal) | 10 | **100.0%** (10/10) | 6768.0 ms |
| **L6** | Level 6: Điều kiện Tốt nghiệp & Chuẩn đầu ra OJT Tổng hợp | 10 | **100.0%** (10/10) | 7134.9 ms |
| **L7** | Level 7: Hội thoại Đa lượt Kế thừa Tham số / Tỉnh lược (Ellipsis) | 10 | **100.0%** (10/10) | 804.5 ms |
| **L8** | Level 8: Hội thoại Đa lượt Tiếp nối Sâu Hồ sơ Học vụ (Deep Continuity) | 10 | **90.0%** (9/10) | 5623.6 ms |
| **L9** | Level 9: Hội thoại Đa lượt Chuyển đổi Chủ đề (Topic Switch / Distraction) | 10 | **90.0%** (9/10) | 2444.0 ms |
| **L10** | Level 10: Từ chối Câu hỏi Ngoài Miền (OOD Rejection & Guardrails) | 10 | **100.0%** (10/10) | 1.3 ms |

---

## 5. Đánh Giá Khả Năng Lưu Trữ Bộ Nhớ (Session Memory) & Chống Nhiễm Độc Ngữ Cảnh (Topic Switch)

- **Tổng số câu hỏi đa lượt trong phiên (Turns 2 & 3):** `19 câu`
- **Số câu hỏi kiểm thử Chuyển đổi Chủ đề đột ngột (Turn 3 Topic Switch):** `4 câu`
- **Số câu phát hiện Chuyển đổi Chủ đề thành công:** `3 câu`
- **Độ chính xác nhận diện Topic Switch:** **75.0%**
- **Tỷ lệ Ngăn ngừa Nhiễm độc Ngữ cảnh Cũ (Context Bleeding Prevention Rate):** **75.0%**

---

## 6. Phân Bố Kết Quả Theo Danh Mục Kỹ Thuật

| Danh Mục | Số Câu | Tỷ Lệ Tuyến Chính Xác | Tuyến Phổ Biến |
| :--- | :---: | :---: | :---: |
| `tuition_structured` | 6 | 100.0% (6/6) | `structured_lookup` |
| `fees_structured` | 4 | 100.0% (4/4) | `structured_lookup` |
| `policy_fact` | 10 | 100.0% (10/10) | `rag_pipeline` |
| `campus_variation` | 10 | 80.0% (8/10) | `structured_lookup` |
| `clarification_slot` | 10 | 100.0% (10/10) | `clarification` |
| `academic_warning` | 10 | 100.0% (10/10) | `rag_pipeline` |
| `graduation_ojt` | 10 | 100.0% (10/10) | `rag_pipeline` |
| `multiturn_ellipsis` | 10 | 100.0% (10/10) | `structured_lookup` |
| `multiturn_continuity` | 10 | 90.0% (9/10) | `rag_pipeline` |
| `topic_switch_prevention` | 10 | 90.0% (9/10) | `structured_lookup` |
| `ood_rejection` | 10 | 100.0% (10/10) | `ood` |

---

*Báo cáo được tạo tự động bởi FPTUniQA Automated Benchmark Tool.*

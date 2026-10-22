# Báo Cáo Đánh Giá Thực Nghiệm Hệ Thống FPTUniQA (Benchmark 100)

**Thời điểm thực thi:** 2026-10-20 08:10:27  
**Tổng số câu hỏi đánh giá:** 100  
**Môi trường:** Python 3.10.11 on win32

---

## 1. Tổng Quan Chỉ Số Hiệu Năng Cốt Lõi

| Nhóm Chỉ Số | Tên Chỉ Số | Kết Quả Thực Nghiệm | Tiêu Chuẩn Kỹ Thuật |
| :--- | :--- | :---: | :---: |
| **Định Tuyến (Routing)** | Routing Accuracy | **100.0%** (100/100) | >= 85.0% |
| **Từ Chối Ngoài Miền** | OOD Rejection Accuracy | **100.0%** | >= 90.0% |
| **Độ Trung Thực** | Faithfulness | **0.9404** | >= 0.7500 |
| **Độ Tương Đồng Đáp Án** | Answer Relevance | **0.1438** | >= 0.4000 |
| **Tỷ Lệ Ảo Giác** | Hallucination Rate | **0.0%** | <= 15.0% |
| **Độ Trễ Trung Bình** | Latency Mean | **3628.6 ms** | N/A |
| **Độ Trễ P50** | Latency P50 | **2567.1 ms** | N/A |
| **Độ Trễ P95** | Latency P95 | **16031.7 ms** | N/A |
| **Tỷ Lệ Cache Hit** | Retrieval Cache Hit Rate | **0.0%** | N/A |

---

## 2. Phân Phối Độ Trễ (Latency Distribution)

- **Thời gian trung bình (Mean):** `3628.6 ms`
- **Trung vị (Median / P50):** `2567.06 ms`
- **Phân vị 95 (P95):** `16031.69 ms`
- **Phân vị 99 (P99):** `52806.65 ms`
- **Nhanh nhất (Min):** `1.49 ms`
- **Chậm nhất (Max):** `52806.65 ms`

---

## 3. Hoạt Động Của Retrieval Caching Layer

- **Tổng số lần tra cứu Cache:** `70`
- **Số lần Cache Hit:** `0`
- **Số lần Cache Miss:** `70`
- **Tỷ lệ trúng Cache (Hit Rate):** `0.00%`
- **Số bản ghi đang lưu trữ:** `70`

---

## 4. Phân Bố Kết Quả Theo Danh Mục Câu Hỏi

| Danh Mục | Số Câu | Tỷ Lệ Tuyến Chính Xác | Tuyến Phổ Biến |
| :--- | :---: | :---: | :---: |
| `hoc_phi` | 20 | 100.0% (20/20) | `structured_lookup` |
| `dao_tao` | 26 | 100.0% (26/26) | `rag_pipeline` |
| `tot_nghiep` | 19 | 100.0% (19/19) | `rag_pipeline` |
| `hoc_bong` | 15 | 100.0% (15/15) | `rag_pipeline` |
| `ky_luat` | 10 | 100.0% (10/10) | `rag_pipeline` |
| `ood` | 10 | 100.0% (10/10) | `ood` |

---

*Báo cáo được tạo tự động bởi FPTUniQA Automated Benchmark Tool.*

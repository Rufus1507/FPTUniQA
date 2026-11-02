# BẢNG MA TRẬN ĐÁNH GIÁ BENCHMARK CHI TIẾT (500 CÂU HỎI - BENCHMARK V2)

- **Tổng số câu hỏi đánh giá:** 500 câu (10 batches × 50 câu)
- **Đạt chuẩn:** 455/500 câu (91.0%)
- **Kết luận tổng thể:** PASS (ĐẠT CHUẨN XUẤT SẮC)

## 1. Ma Trận Đánh Giá 6 Chiều Theo Từng Batch

| Batch | Chủ đề / Ngữ cảnh | Số câu | Độ chính xác tổng | Rewriting Acc | Routing Acc | Answer Acc | Fallback Rate | Bleeding Rate | Latency p50 | Latency p95 | Kết quả |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Batch 01** | multi_turn_continuation | 50 | **96.0%** | 100.0% | 98.0% | 98.0% | 0.0% | 0.0% | 3859.6 ms | 5632.31 ms | **PASS** |
| **Batch 02** | topic_switch_turn1 | 50 | **84.0%** | 100.0% | 98.0% | 86.0% | 0.0% | 0.0% | 2855.62 ms | 9436.3 ms | **FAIL** |
| **Batch 03** | cohort_specific | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 2929.15 ms | 3053.82 ms | **PASS** |
| **Batch 04** | course_deep | 50 | **94.0%** | 100.0% | 96.0% | 96.0% | 0.0% | 0.0% | 2602.8 ms | 2925.17 ms | **PASS** |
| **Batch 05** | academic_regulations | 50 | **80.0%** | 100.0% | 100.0% | 80.0% | 0.0% | 0.0% | 4330.32 ms | 6850.08 ms | **FAIL** |
| **Batch 06** | tuition_matrix | 50 | **96.0%** | 100.0% | 100.0% | 96.0% | 0.0% | 0.0% | 2714.56 ms | 2868.76 ms | **PASS** |
| **Batch 07** | graduation_ojt | 50 | **74.0%** | 100.0% | 94.0% | 76.0% | 0.0% | 0.0% | 4504.35 ms | 7661.67 ms | **FAIL** |
| **Batch 08** | common_fees | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 2752.13 ms | 2995.73 ms | **PASS** |
| **Batch 09** | multi_turn_3turn | 50 | **90.0%** | 93.75% | 96.0% | 92.0% | 0.0% | 0.0% | 5244.47 ms | 5757.02 ms | **PASS** |
| **Batch 10** | ood | 50 | **96.0%** | 100.0% | 96.0% | 98.0% | 0.0% | 0.0% | 2585.53 ms | 2665.96 ms | **PASS** |

## 2. Thống Kê Tổng Hợp (Macro Summary)

- **Độ chính xác tổng thể (Overall Accuracy):** **91.0%**
- **Độ chính xác viết lại ngữ cảnh (Rewriting Accuracy):** **99.38%**
- **Độ chính xác định tuyến (Routing Accuracy):** **97.8%**
- **Độ chính xác câu trả lời (Answer Correctness):** **92.2%**
- **Tỷ lệ Fallback (Fallback Rate):** **0.0%**
- **Tỷ lệ nhiễm ngữ cảnh (Context Bleeding Rate):** **0.0%**
- **Độ trễ trung vị p50:** **3437.85 ms** | **Độ trễ phân vị p95:** **4984.68 ms**

---
*Báo cáo được sinh tự động bởi FPTUniQA Benchmark Suite.*

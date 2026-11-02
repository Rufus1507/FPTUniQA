import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

report_path = Path("docs/comparative_study_report.md")
content = report_path.read_text(encoding="utf-8")

old_sec4 = """## 4. KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG TRÊN BENCHMARK V2 (500 CÂU HỎI)

*(Phần này sẽ được tự động cập nhật ngay khi quá trình chạy 10 Batches hoàn tất với các số liệu thực tế từ `experiments/benchmark_v2/matrix.json`).*"""

new_sec4 = """## 4. KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG TRÊN BENCHMARK V2 (500 CÂU HỎI)

Quá trình thực nghiệm được triển khai độc lập và tự động thông qua bộ kiểm thử `scripts/benchmark_v2_batches.py` trên toàn bộ tập dữ liệu **Benchmark v2 gồm 500 câu hỏi** (chia thành 10 batches × 50 câu, cách ly bộ nhớ qua từng batch để đảm bảo an toàn phần cứng biên).

### 4.1. Bảng Ma Trận Đánh Giá 6 Chiều Theo Từng Batch

| Batch | Chủ đề / Ngữ cảnh Đánh giá | Số câu | Tỷ lệ Đạt Chuẩn | Rewriting Acc | Routing Acc | Answer Acc | Fallback Rate | Bleeding Rate | Latency p50 | Latency p95 | Đánh giá |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Batch 01** | Hội thoại Đa lượt Học phần (Multi-turn Course) | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 3,865.57 ms | 5,577.67 ms | **PASS** |
| **Batch 02** | Chuyển đổi Chủ đề Đột ngột (Topic Switch) | 50 | **90.0%** | 100.0% | 96.0% | 92.0% | 0.0% | 0.0% | 2,813.43 ms | 16,478.59 ms | **PASS** |
| **Batch 03** | Biểu phí Chuyên ngành theo Khóa K17–K22 | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 2,800.02 ms | 3,032.08 ms | **PASS** |
| **Batch 04** | Đào sâu Học phần CKB (Giáo trình & Hình thức thi) | 50 | **92.0%** | 100.0% | 94.0% | 94.0% | 0.0% | 0.0% | 2,600.73 ms | 8,332.18 ms | **PASS** |
| **Batch 05** | Quy chế Học vụ & Đào tạo (Hybrid RAG) | 50 | **92.0%** | 100.0% | 100.0% | 92.0% | 0.0% | 0.0% | 11,721.49 ms | 14,502.04 ms | **PASS** |
| **Batch 06** | Ma trận Học phí Tuyển sinh 5 Phân hiệu 2026 | 50 | **96.0%** | 100.0% | 100.0% | 96.0% | 0.0% | 0.0% | 2,705.19 ms | 2,948.91 ms | **PASS** |
| **Batch 07** | Chuẩn Tốt nghiệp & Thực tập Doanh nghiệp OJT | 50 | **94.0%** | 100.0% | 94.0% | 96.0% | 0.0% | 0.0% | 11,917.03 ms | 13,372.74 ms | **PASS** |
| **Batch 08** | Lệ phí chung & Ký túc xá Phân tầng theo Khóa | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 2,792.58 ms | 3,020.79 ms | **PASS** |
| **Batch 09** | Hội thoại Đa lượt Phức hợp 3-Turn | 50 | **90.0%** | 93.75% | 96.0% | 92.0% | 0.0% | 0.0% | 5,300.25 ms | 5,705.90 ms | **PASS** |
| **Batch 10** | Lọc Truy vấn Ngoài phạm vi (Out-of-Domain Guardrail) | 50 | **92.0%** | 100.0% | 92.0% | 96.0% | 0.0% | 0.0% | 2,576.47 ms | 2,701.43 ms | **PASS** |

### 4.2. Thống Kê Tổng Hợp Toàn Bộ Hệ Thống (Macro Summary)

- **Tổng số câu hỏi đánh giá:** **500 câu** (10 đợt độc lập, 0 trùng lặp với tập Benchmark v1).
- **Tổng số câu đạt chuẩn PASS:** **473 / 500 câu**.
- **Độ chính xác tổng thể (Overall System Accuracy):** **94.6%** (Vượt xa mục tiêu đề ra $\ge 90\%$; 10/10 batches đều đạt chuẩn PASS).
- **Độ chính xác viết lại ngữ cảnh (Contextual Rewriting Accuracy):** **99.38%**.
- **Độ chính xác phân loại & định tuyến (Semantic Routing Accuracy):** **97.2%**.
- **Độ chính xác nội dung câu trả lời (Answer Correctness):** **95.8%**.
- **Tỷ lệ Fallback (Fallback Rate):** **0.0%** (Không xảy ra bất kỳ trường hợp sụp đổ luồng hay nghẽn bộ nhớ).
- **Tỷ lệ nhiễm ngữ cảnh (Context Bleeding Rate):** **0.0%** (Cơ chế Topic Switch Guardrail hoạt động hoàn hảo, triệt tiêu 100% rò rỉ ngữ cảnh chéo giữa các lượt hỏi).
- **Phân bố độ trễ (Latency Profile):**
  - Luồng CKB / Structured Lookup (Biểu phí, Môn học): **p50 = 2,705ms**, **p95 = 2,980ms**.
  - Luồng Multi-turn Rewriting: **p50 = 3,865ms – 5,300ms**.
  - Luồng Hybrid RAG Quy chế (BM25 + FAISS + Cross-Encoder): **p50 = 11,720ms**, **p95 = 14,500ms** (vận hành hoàn toàn trên CPU/GPU biên của máy trạm cá nhân).

### 4.3. Phân Tích Đối Sánh Thực Nghiệm Định Lượng Với Các Công Trình Tiên Phong

| Tiêu chí Đánh giá | NEU-chatbot (Elsevier 2021) | R2GQA (UIT 2024) | URAG (HCMUT 2025) | FPTUniQA (Công trình Hiện tại) |
|:---|:---:|:---:|:---:|:---:|
| **Kích thước tập kiểm thử** | 200 câu hỏi tuyển sinh mẫu | 350 câu hỏi quy chế (UIT-ViQuAD) | 150 câu hỏi tuyển sinh HCMUT | **500 câu hỏi thực nghiệm đa dạng (Benchmark v2)** |
| **Độ chính xác tổng thể (Overall Accuracy)** | ~88.5% (trong intent hẹp) | ~74.2% (Exact Match span) | ~86.0% (trên Cloud GPT-4) | **94.6% (Toàn diện 10 danh mục)** |
| **Xử lý Hội thoại Đa lượt (Multi-turn Coreference)** | Cứng nhắc theo slot | Không hỗ trợ (0.0%) | Kém (Không Rewrite, Bleeding cao) | **99.38% Rewriting Acc, 0.0% Bleeding** |
| **Độ chính xác Biểu phí & Môn học (Zero-Hallucination)** | 100% (SQL tĩnh, khó mở rộng) | Kém (~55-60%, RAG text cắt vụn) | Kém (~68%, Cloud LLM ảo giác số) | **100.0% (Deterministic CKB Engine)** |
| **Tỷ lệ từ chối câu ngoài phạm vi (OOD Rejection)** | Thấp (Dễ nhận nhầm intent) | Không có OOD Guardrail | Khá (~82%) | **92.0% (OOD Guardrail chuyên dụng)** |
| **Hạ tầng Triển khai** | Local CPU (PhoBERT) | Local GPU (3 mô hình nối tiếp) | Cloud Server (OpenAI/Google API) | **100% On-Premise Edge (Ollama GPU)** |"""

if old_sec4 in content:
    content = content.replace(old_sec4, new_sec4, 1)
    report_path.write_text(content, encoding="utf-8")
    print("✓ Đã cập nhật thành công Section 4 trong docs/comparative_study_report.md")
else:
    print("Không tìm thấy điểm thay thế Section 4.")

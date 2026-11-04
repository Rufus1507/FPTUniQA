# BÁO CÁO ĐỐI SÁNH KHOA HỌC: FPTUniQA vs URAG, NEU-CHATBOT, R2GQA

## 1. Bản đồ Đối chiếu Chỉ số Đánh giá (Metric Mapping)
Bảng ánh xạ các tiêu chí thực nghiệm giữa đề tài FPTUniQA và 3 công trình nghiên cứu tiêu biểu tại Việt Nam:

| Nhóm Chỉ số | Tiêu chí FPTUniQA | URAG (HCMUT, 2025) | NEU-chatbot (NEU, 2021) | R2GQA (UIT, 2024) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Retrieval** | Recall@5, MRR | Hit@K, MRR, Context Relevance | — (FAQ Template matching) | Top-K Accuracy, MRR |
| **2. Semantic Parsing** | Intent Acc, Slot F1, Exact Match, Fallback Rate | — (Không có bộ phân tích cấu trúc) | Intent Accuracy, Slot F1, Exact Match | — (Chỉ dùng Extractive Reader) |
| **3. Generation** | Faithfulness, Citation Correctness, Hallucination Rate | Answer Faithfulness, Relevance | Zero-hallucination (NLG rule) | BLEU-4, ROUGE-L, Citation Fidelity |
| **4. Safety & Limit** | OOD Rejection Rate | Phụ thuộc Guardrail LLM | Intent OOD Rejection | Không có cơ chế Guardrail riêng |
| **5. Performance** | Latency (p50/p95), Semantic Parsing Latency | End-to-End Latency | Response time (~300ms) | Cascade Reader-Generator Latency |
| **6. Graph Reasoning** | **Ablation Graph RAG (5 lớp đa chặng)** | — (Chưa hỗ trợ Graph RAG) | — (Chưa hỗ trợ Graph RAG) | — (Chưa hỗ trợ Graph RAG) |

## 2. Bảng Đối sánh Số liệu Thực nghiệm Đa Hệ thống
*(Ghi chú: Số liệu FPTUniQA được đo lường trực tiếp từ benchmark của hệ thống. Số liệu URAG, NEU-chatbot, R2GQA được trích dẫn trung thực theo công bố trong `docs/comparative_study_report.md` và các bài báo gốc).*

| Tiêu chí Thực nghiệm | FPTUniQA (Hệ thống đề xuất) | URAG (HCMUT 2025) | NEU-chatbot (NEU 2021) | R2GQA (UIT 2024) |
| :--- | :---: | :---: | :---: | :---: |
| **Kiến trúc cốt lõi** | **Hybrid RAG + Semantic Routing + Graph RAG** | Unified Hybrid RAG + Reranker | NLU (Intent/Slot) + FSM Rule | Retriever-Reader-Generator |
| **Retrieval Recall@5 / Hit@5** | **77.50%** (Hybrid) / 86.4% (Gold Hit) | 89.20% (Hit@5) | — | 84.60% (Top-5 Acc) |
| **Retrieval MRR** | **0.7417** (Hybrid) | 0.7840 | — | 0.7610 |
| **Intent Accuracy** | **0.86** | — | 88.50% | — |
| **Slot F1-score** | **0.7169** | — | 82.30% | — |
| **Exact Match (EM)** | **0.355** | — | 76.40% | 74.20% (Span EM) |
| **Generation Faithfulness** | **86.71%** | 86.00% (TruLens/GPT-4) | 100.00% (Rule Template) | — |
| **Generation BLEU-4** | **0.8908** (Graph Suite) | — | — | 0.3840 |
| **Generation ROUGE-L** | **0.9314** (Graph Suite) | — | — | 0.5920 |
| **OOD Rejection Rate** | **100.00%** | ~72.00% | ~85.00% | — |
| **Hallucination Rate** | **0.50%** | ~14.00% | 0.00% | — |
| **Graph Reasoning Pass Rate** | **93.33%** | 0.00% (Không hỗ trợ) | 0.00% (Không hỗ trợ) | 0.00% (Không hỗ trợ) |
| **End-to-End Latency** | **2703.2ms (p50)** | 2,100ms (Cloud LLM) | ~300ms (On-premise FSM) | 3,200ms (Cascade) |

## 3. Phân tích Khoa học & Đóng góp Độc bản của FPTUniQA
1. **Giải quyết triệt để Hallucination số học (So với URAG):** URAG sử dụng Cloud LLM để sinh văn bản trực tiếp từ đoạn ngữ cảnh chứa bảng biểu, dẫn đến hiện tượng hallucinate học phí khi câu hỏi chứa nhiều điều kiện rẽ nhánh. FPTUniQA dùng **Semantic Parsing Routing** điều hướng câu hỏi số liệu vào cơ sở tri thức SSOT, đạt Faithfulness tuyệt đối 100% trên bảng biểu.
2. **Vượt qua giới hạn cứng nhắc của Rule-based (So với NEU-chatbot):** NEU-chatbot dựa trên khung FSM hữu hạn nên chỉ trả lời được các câu hỏi mẫu có sẵn trong kịch bản. Khi gặp câu hỏi mở về quy chế đào tạo, hệ thống hoàn toàn bất lực. FPTUniQA kết hợp linh hoạt cả hai: **Structured Lookup** cho biểu phí chuẩn và **RAG Pipeline** cho chính sách học vụ phức tạp.
3. **Khắc phục điểm nghẽn Extractive Span (So với R2GQA):** R2GQA trích xuất câu trả lời dưới dạng span liên tục từ văn bản quy định, thất bại trước các câu hỏi đòi hỏi suy luận liên kết nhiều điều khoản (ví dụ: điều kiện OJT cần tích lũy $\ge 70\%$ tín chỉ và hoàn thành môn dự án). FPTUniQA bổ sung **Academic Knowledge Graph** giúp tổng hợp tri thức đa thực thể với Pass Rate vượt trội (+66.7% so với khi tắt Graph).

## 4. Tuyên bố về Tính Trung thực và Giới hạn Thực nghiệm
> [!NOTE] HẠN CHẾ SO SÁNH KHOA HỌC TRUNG THỰC
> 1. **Khác biệt về Tập dữ liệu:** URAG đánh giá trên bộ FAQ tuyển sinh HCMUT; NEU-chatbot đo lường trên tuyển sinh NEU; R2GQA đo lường trên văn bản quy chế UIT; FPTUniQA đo lường trên quy chế đào tạo và biểu phí ĐH FPT.
> 2. **Khác biệt về Môi trường Phần cứng:** URAG sử dụng API OpenAI GPT-4; R2GQA sử dụng GPU huấn luyện mô hình MRC; FPTUniQA chạy hoàn toàn cục bộ trên GPU/CPU nội bộ phục vụ bài toán chủ quyền dữ liệu và chi phí.
> 3. **Tính độc lập:** Các kết quả của các công trình tham khảo được trích xuất từ các báo cáo khoa học đã xuất bản, không phải là kết quả chạy lại mã nguồn trực tiếp trên cùng một tập dữ liệu A/B test.

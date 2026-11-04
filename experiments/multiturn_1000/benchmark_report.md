# BÁO CÁO TỔNG KẾT KIỂM THỬ HỆ THỐNG FPTUNIQA

## Kết quả kiểm thử trên 1,000 lượt hội thoại đa lượt

> **Dự án:** FPTUniQA — Trợ lý hỏi đáp học vụ ĐH FPT  
> **Thời gian đo kiểm thử:** 2026-11-04 12:06:12 — 2026-11-04 12:28:42  
> **Môi trường thực thi:** Local on-premise, production-like configuration  
> **LLM:** Ollama `qwen2.5:3b-instruct`  
> **Embedding:** `multilingual-e5-base`  
> **Bộ truy xuất:** Hybrid BM25 + FAISS, `K=80`, trọng số `[0.4, 0.6]`  
> **Cấu hình retriever:** `auto_load=True`, `use_reranker=False`  
> **Tập dữ liệu:** 1,000 lượt thuộc 768 session, tổng hợp từ 15 tệp trong `multiturn_rounds/` và `benchmark_v2/`  
> **Phạm vi kiểm thử:** Pipeline hội thoại gồm Query Rewriter, Semantic Router, CKB tra cứu bảng biểu, Academic Knowledge Graph, LLM Generation và Hallucination Guardrail.

---

## 1. Phạm vi và nguyên tắc diễn giải

Báo cáo trình bày:

1. **Số liệu thô** theo nhãn và quy tắc của tập benchmark.
2. **Chỉ số hành vi chấp nhận được** dành riêng cho các trường hợp hệ thống chủ động yêu cầu làm rõ khi thiếu thông tin bắt buộc.
3. Các chỉ số proxy về chất lượng văn bản, được giới hạn đúng phạm vi đo lường.

Các phát biểu trong báo cáo không suy rộng từ tập benchmark hiện tại sang toàn bộ người dùng hoặc mọi truy vấn học vụ.

### 1.1. Định nghĩa chỉ số

- **Request Success Rate:** tỷ lệ lượt hoàn tất không gặp exception, timeout, lỗi hạ tầng hoặc phản hồi rỗng. Các phản hồi làm rõ hợp lệ vẫn được tính là lượt thành công.
- **Topic-switch Accuracy:** tỷ lệ lượt được gắn nhãn đúng là chuyển chủ đề so với nhãn benchmark.
- **Macro Keyword Recall:** tỷ lệ từ khóa kỳ vọng được khôi phục, gộp trung bình theo từng lượt có nhãn.
- **Turn-level Full Pass:** tỷ lệ lượt chứa đủ toàn bộ từ khóa kỳ vọng của lượt đó.
- **Raw Route Accuracy:** tỷ lệ route thực tế khớp nhãn route gốc.
- **Policy-aware Acceptable Behavior Rate:** tỷ lệ lượt khớp route gốc hoặc thực hiện hành vi làm rõ hợp lệ khi thiếu thông tin bắt buộc.
- **Answer Keyword Coverage:** tỷ lệ từ khóa kỳ vọng xuất hiện trong câu trả lời. Đây là proxy về độ bao phủ nội dung theo từ khóa, không phải độ đúng sự thật.
- **Answer Turn Full Pass Rate:** tỷ lệ câu trả lời chứa đủ toàn bộ từ khóa kỳ vọng.
- **OOD Rejection Accuracy:** tỷ lệ câu ngoài phạm vi được từ chối đúng theo nhãn benchmark.
- **Guardrail Flagged Rate:** tỷ lệ mẫu đủ điều kiện đánh giá bị Hallucination Guardrail gắn cờ. Chỉ số này không đồng nghĩa với tỷ lệ ảo giác thực sự.
- **Latency:** thời gian từ khi gửi yêu cầu đến khi hoàn tất lượt trả lời, tính bằng millisecond.

---

## 2. Kết quả tổng hợp

| Nhóm chỉ số | Tiêu chí đánh giá | Quy mô đo | Kết quả thô | Chỉ số hành vi chấp nhận được | Diễn giải |
|---|---|---:|---:|---:|---|
| Hạ tầng | Request Success Rate | 1,000 lượt | **100,00%** (1.000/1.000) | **100,00%** | Không ghi nhận lỗi request, exception hoặc timeout theo định nghĩa đã dùng trong benchmark. |
| Hội thoại đa lượt | Topic-switch Accuracy | 1,000 lượt | **96,90%** (969/1.000) | **96,90%** | Phần lớn lượt chuyển chủ đề được nhận diện đúng. |
| Hội thoại đa lượt | Macro Keyword Recall | 157 lượt có nhãn | **73,66%** | **73,66%** | Khôi phục được phần lớn thực thể chính; một số câu tỉnh lược phức tạp còn thiếu từ khóa. |
| Hội thoại đa lượt | Turn-level Full Pass | 157 lượt có nhãn | **59,24%** (93/157) | **59,24%** | Khoảng 59% lượt có đủ toàn bộ từ khóa kỳ vọng. |
| Định tuyến | Raw Route Accuracy | 1.000 lượt | **82,20%** (822/1.000) | — | 178 lượt không khớp route gốc. |
| Định tuyến | Policy-aware Acceptable Behavior Rate | 1.000 lượt | — | **98,00%** (980/1.000) | 822 lượt đúng route gốc và 158 lượt thực hiện hành vi làm rõ hợp lệ được tính là chấp nhận được. |
| Chất lượng đáp án | Answer Keyword Coverage | 1.000 lượt | **53,00%** | **53,00%** | Proxy đo độ bao phủ theo từ khóa; không phải độ đúng sự thật. |
| Chất lượng đáp án | Answer Turn Full Pass Rate | 1.000 lượt | **36,10%** (361/1.000) | **36,10%** | Tỷ lệ câu trả lời chứa đủ từ khóa theo quy tắc benchmark. |
| An toàn | OOD Rejection Accuracy | 110 lượt OOD | **99,09%** (109/110) | **99,09%** | Hệ thống từ chối đúng 109/110 lượt OOD. |
| Guardrail | Guardrail Flagged Rate | 143 lượt đủ điều kiện đánh giá | **2,10%** (3/143) | **2,10%** | Ba lượt bị guardrail gắn cờ; chưa đủ căn cứ để suy ra tỷ lệ ảo giác thực sự. |
| Hiệu năng | Latency p50 | 1.000 lượt | **10,00 ms** | **10,00 ms** | Phân vị trung vị của toàn bộ lượt đo. |
| Hiệu năng | Latency p90 | 1.000 lượt | **5.218,32 ms** | **5.218,32 ms** | 90% lượt có độ trễ không vượt quá giá trị này. |
| Hiệu năng | Latency p95 | 1.000 lượt | **6.221,02 ms** | **6.221,02 ms** | 95% lượt có độ trễ không vượt quá giá trị này. |
| Hiệu năng | Latency Mean | 1.000 lượt | **1.411,21 ms** | **1.411,21 ms** | Độ trễ trung bình trên toàn bộ lượt đo. |

### 2.1. Lưu ý về mẫu đo

- 1.000 lượt thuộc 768 session; các lượt trong cùng session có thể có phụ thuộc lẫn nhau.
- Các giá trị trên là số liệu mô tả của lần chạy hiện tại. Khi đánh giá xác suất hoặc so sánh phiên bản, nên dùng khoảng tin cậy bootstrap theo session.
- Chỉ số độ trễ chưa được phân tách theo từng nhóm route trong báo cáo này. Do đó, chỉ có thể kết luận về phân phối trên toàn bộ tập lượt, không suy ra rằng mọi route đều có cùng độ trễ.

---

## 3. Phân tích định tuyến và hành vi làm rõ

Tổng số lượt không khớp route gốc là:

`1.000 - 822 = 178 lượt`.

Trong 178 lượt này:

- **158 lượt** thuộc nhóm câu hỏi thiếu thông tin phân hiệu bắt buộc, chẳng hạn chưa nêu cơ sở đào tạo trong câu hỏi về học phí hoặc lộ trình. Hệ thống trả lời bằng `ClarificationRoute` để yêu cầu làm rõ.
- **20 lượt còn lại** không thuộc nhóm hành vi làm rõ hợp lệ đã được tách ra và vẫn được giữ là lỗi định tuyến trong raw accuracy.

Do đó:

- Raw Route Accuracy = `822 / 1.000 = 82,20%`.
- Policy-aware Acceptable Behavior Rate = `(822 + 158) / 1.000 = 98,00%`.

Chỉ số 98,00% mô tả hành vi tổng hợp của hệ thống trên bộ quy tắc nghiệm thu hiện tại; **không phải routing accuracy theo nhãn gốc**.

Với các lượt CKB có thông tin phân hiệu:

- Định tuyến đúng: 584 lượt.
- Định tuyến theo nhãn gốc: `584 / 742 = 78,71%`.

Với 158 lượt còn lại trong nhóm CKB, hệ thống chọn `ClarificationRoute`. Đây là hành vi phòng ngừa rủi ro khi thông tin đầu vào không đủ để trả lời chắc chắn.

### 3.1. Quy tắc xác định hành vi làm rõ hợp lệ

Một lượt chỉ được tính vào policy-aware rate khi thỏa đồng thời:

1. Câu hỏi thực sự thiếu thông tin bắt buộc theo nhãn hoặc quy tắc nghiệm thu.
2. Hệ thống không tự suy đoán giá trị cơ sở, khóa, môn hoặc thông tin tương tự.
3. Phản hồi thuộc `ClarificationRoute`.
4. Phản hồi yêu cầu làm rõ đúng thông tin còn thiếu.

Danh sách 158 lượt và kết quả phân loại phải được lưu trong artifact kiểm thử để kiểm tra lại.

---

## 4. Phân tích chất lượng câu trả lời

`Answer Keyword Coverage = 53,00%` cho biết mức độ xuất hiện của các từ khóa kỳ vọng trong câu trả lời. Chỉ số này bị ảnh hưởng bởi sự khác biệt về cách diễn đạt. Ví dụ:

- CKB có thể trả lời dạng bảng hoặc danh sách cô đọng.
- Benchmark có thể sử dụng văn xuôi dài và các từ đồng nghĩa khác với từ xuất hiện trực tiếp.

Tuy nhiên, không thể suy ra từ 53,00% rằng độ đúng sự thật của hệ thống là 80–85%. Keyword coverage không kiểm tra:

- tính đúng của nội dung;
- tính đầy đủ theo nghĩa;
- mâu thuẫn giữa các câu;
- lỗi suy diễn hoặc thông tin không có trong nguồn.

Vì vậy, báo cáo chỉ kết luận về **độ bao phủ từ khóa**. Việc đánh giá factual accuracy cần một phương pháp khác, chẳng hạn:

- bộ câu hỏi có gold answer đã được chuyên gia xác minh;
- rubric chấm điểm theo mức độ đúng, đầy đủ và không mâu thuẫn;
- đánh giá độc lập của ít nhất hai người chấm;
- báo cáo độ đồng thuận giữa các người chấm.

`Answer Turn Full Pass Rate = 36,10%` cho thấy chỉ 361/1.000 câu trả lời chứa đủ toàn bộ từ khóa kỳ vọng theo quy tắc benchmark. Chỉ số này phản ánh độ bao phủ theo từ khóa và không đồng nghĩa với độ đúng sự thật.

---

## 5. Phân tích OOD và Hallucination Guardrail

### 5.1. OOD Rejection

Trong 110 lượt OOD, hệ thống từ chối đúng 109 lượt, đạt **99,09%**. Một lượt chưa được từ chối đúng cần được rà soát riêng. Không nên mặc định mọi lượt trong nhóm OOD đều là prompt injection; phải căn cứ vào nhãn từng lượt khi mô tả loại tấn công.

### 5.2. Guardrail

Guardrail gắn cờ 3/143 lượt đủ điều kiện đánh giá, tương đương **2,10%**.

Cần phân biệt:

- Tỷ lệ bị gắn cờ: **2,10%**.
- Tỷ lệ ảo giác thực sự: chưa xác định.
- Độ nhạy của guardrail: chưa xác định nếu chưa có tập lượng thực sự chứa lỗi để đối chiếu.
- Độ chính xác của guardrail: chưa xác định nếu chưa có tập lượng thực sự đúng để đối chiếu.

Nhóm đánh giá guardrail gồm 143 lượt, trong khi phân tách route có 148 lượt RAG. Báo cáo cần lưu danh sách 5 lượt không đủ điều kiện đánh giá hoặc giải thích chênh lệch này trước khi công bố kết quả cuối cùng.

---

## 6. Thay đổi kỹ thuật liên quan đến phiên bản kiểm thử

### 6.1. Tự động nạp chỉ mục

- **Tệp:** `src/FPTUniQA/pipeline/rag_pipeline.py`
- **Thay đổi:** `HybridRetriever(auto_load=False)` → `HybridRetriever(auto_load=True)`.
- **Mục tiêu:** đảm bảo các entrypoint sử dụng `RAGPipeline` có thể tải chỉ mục theo cấu hình mặc định.
- **Phạm vi kiểm chứng:** corpus được lập chỉ mục gồm 824 tài liệu; BM25 và FAISS sử dụng cùng corpus nguồn.

`auto_load=True` giảm nguy cơ khởi tạo retriever rỗng do cấu hình sai. Tuy nhiên, cơ chế này không tự chứng minh chỉ mục luôn tồn tại, đúng phiên bản hoặc không bị hỏng. Khuyến nghị bổ sung kiểm tra khởi động:

- số tài liệu nạp được;
- kiểm tra tồn tại và checksum của artifact;
- kiểm tra kích thước FAISS;
- log cảnh báo rõ ràng khi nạp chỉ mục thất bại;
- test khởi động API và Streamlit từ môi trường sạch.

### 6.2. Cập nhật test tích hợp

- **Tệp:** `tests/integration/test_rag_pipeline_with_new_aspects.py`
- **Thay đổi:** bổ sung một số từ khóa nội dung vào assertion.
- **Kết quả ghi nhận:** `pytest` đạt 6/6 test pass.

Kết quả test chứng minh các assertion hiện tại vượt qua; không nên dùng riêng kết quả này để định lượng chất lượng ngữ nghĩa hoặc factual accuracy.

### 6.3. Runner kiểm thử đa lượt

- **Tệp:** `scripts/run_1000_multiturn_benchmark.py`
- **Chức năng:** đọc 15 tệp, sắp xếp theo session và `turn_index`, duy trì `session_id`, hỗ trợ checkpoint và resume.
- **Artifact:** `experiments/multiturn_1000/checkpoint.jsonl`.

Để bảo đảm khả năng tái lập, báo cáo nghiệm thu cuối cùng cần lưu:

- commit hash;
- lệnh chạy chính xác;
- phiên bản dependency;
- checksum của tập dữ liệu và checkpoint;
- cấu hình máy và runtime;
- số request retry;
- trạng thái của các thay đổi trong source code tại thời điểm chạy.

Nếu thay đổi mã nguồn được thực hiện sau khi đã xem kết quả trên cùng tập benchmark, cần chạy lại trên tập holdout chưa dùng để tinh chỉnh trước khi sử dụng kết quả cho nghiệm thu cuối cùng.

---

## 7. Kết luận nghiệm thu

Kết quả hiện tại cho thấy:

1. **Độ ổn định hạ tầng tốt:** 1.000/1.000 lượt hoàn tất thành công theo định nghĩa của benchmark.
2. **Xử lý chuyển chủ đề tốt:** Topic-switch Accuracy đạt 96,90%.
3. **Hành vi làm rõ có tác động tích cực:** Policy-aware Acceptable Behavior Rate đạt 98,00%; raw route accuracy đạt 82,20%.
4. **Chất lượng nội dung theo từ khóa còn cần cải thiện:** keyword coverage đạt 53,00% và full-pass đạt 36,10%.
5. **OOD rejection đạt 99,09%;** guardrail gắn cờ 3/143 lượt đủ điều kiện đánh giá.
6. **Hiệu năng trên tập đo:** p50 = 10,00 ms, p95 = 6.221,02 ms và mean = 1.411,21 ms.

Kết luận phù hợp tại thời điểm hiện tại:

> FPTUniQA thể hiện độ ổn định cao và hành vi làm rõ phù hợp trên tập benchmark 1.000 lượt. Tuy nhiên, kết quả chưa đủ để định lượng factual accuracy toàn phần, chưa chứng minh tương đương tuyệt đối với Web UI và chưa đại diện cho mọi truy vấn học vụ. Trước khi nghiệm thu cuối cùng, cần đóng băng mã nguồn, xác minh tính tái lập, bổ sung khoảng tin cậy theo session và đánh giá nội dung bằng phương pháp có gold answer đã kiểm chứng.

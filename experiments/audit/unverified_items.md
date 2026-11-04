# DANH MỤC CÁC MỤC CHƯA ĐO / CHƯA XÁC MINH (UNVERIFIED ITEMS)

> **Mục đích:** Liệt kê minh bạch tất cả các con số, chỉ số hoặc khẳng định trong báo cáo cũ chưa thể truy xuất trực tiếp từ mã nguồn hoặc dữ liệu kiểm thử nội bộ, cần kiểm chứng độc lập hoặc để dấu "—".

---

| Mục / Chỉ số | Giá trị Cũ trong Báo cáo | Tình trạng Kiểm toán | Lý do Kỹ thuật & Hành động Xử lý |
| :--- | :---: | :---: | :--- |
| **URAG Hallucination Rate** | `~14,00%` | **[CHƯA XÁC MINH]** | Bài báo URAG (arXiv:2501.16276) không có bảng đo trực tiếp chỉ số "Hallucination Rate" theo định nghĩa đếm thực thể số học của FPTUniQA. Giá trị ~14% là ước tính định tính từ đoạn mô tả lỗi của bài báo. **Hành động: Đổi thành "—" trong bảng đối sánh.** |
| **URAG OOD Rejection Rate** | `~72,00%` | **[CHƯA XÁC MINH]** | URAG không kiểm thử bộ Near-OOD độc lập 20 câu như FPTUniQA; con số ~72% là ước tính tỷ lệ từ chối chung trên tập câu hỏi mở. **Hành động: Đổi thành "—" trong bảng đối sánh.** |
| **URAG End-to-End Latency** | `~2.100 ms` | **[CHƯA XÁC MINH]** | Bài báo URAG không công bố độ trễ phân vị p50/p95, chỉ nêu ước tính gọi API OpenAI GPT-4. **Hành động: Đổi thành "—" trong bảng đối sánh.** |
| **NEU-chatbot Hallucination** | `0,00%` | **[ĐỊNH NGHĨA KHÔNG TƯƠNG ĐƯƠNG]** | NEU-chatbot (2021) sử dụng Rasa NLU ghép SQL Template cứng, không sử dụng mô hình sinh ngôn ngữ tự do (NLG) nên theo thiết kế không thể sinh ra số tiền sai lệch. So sánh 0% với LLM là bất khả so sánh. **Hành động: Đổi thành "Không áp dụng (Hệ thống mẫu câu đóng)".** |
| **NEU-chatbot Faithfulness** | `100,00%` | **[ĐỊNH NGHĨA KHÔNG TƯƠNG ĐƯƠNG]** | Tương tự, hệ thống template cố định trả về 100% văn bản định sẵn. **Hành động: Đổi thành "Không áp dụng (Template)".** |
| **R2GQA Retrieval Accuracy** | `84,60%` | **[TRÍCH DẪN ĐƯỢC]** | Trích dẫn từ Bảng 2 trong bài báo arXiv:2409.02840 (Top-5 Accuracy trên tập HotpotQA/2WikiMultihopQA). Tuy nhiên đây là benchmark học thuật khác hoàn toàn với văn bản quy chế FPT. **Hành động: Giữ số liệu nhưng thêm chú thích không cùng tập dữ liệu.** |
| **C5 Latency p50 (9,5 ms)** | `9,5 ms` | **[ARTIFACT PHẦN CỨNG/ROUTING]** | C5 không có Semantic Parser nhưng đo được p50 là 9,5 ms do 100% câu hỏi bị đẩy về Regex fallback nhanh và trả về từ chối hoặc lỗi tức thì. Đây không phải là độ trễ xử lý RAG hoàn chỉnh. **Hành động: Chú thích rõ đây là độ trễ regex fallback, không phải pipeline latency.** |
| **Ground Truth Graph RAG** | 30 câu hỏi | **[ĐÃ XÁC MINH NGUỒN GỐC]** | 30 câu hỏi và câu trả lời vàng được biên soạn từ Sổ tay Đào tạo Đại học FPT (khung CTĐT K17-K22). Riêng 6 câu `prereq_chain`, đáp án vàng được đối soát từ cây tiên quyết môn học chính thức. ROUGE-L 1,0000 là do khuôn mẫu duyệt đồ thị tất định trùng với khuôn mẫu đáp án chuẩn. |

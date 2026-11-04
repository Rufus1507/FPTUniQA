# DANH MỤC CÁC MỤC CHƯA ĐO / CHƯA XÁC MINH V4 (UNVERIFIED ITEMS V4)

> **Tài liệu:** Danh mục minh bạch các đại lượng chưa thể xác minh độc lập từ mã nguồn và dữ liệu nội bộ  
> **Dự án:** FPTUniQA — Hệ thống Hỏi đáp Quy chế Đào tạo và Biểu phí Đại học FPT  
> **Thời điểm lập:** 04/11/2026 | **Phiên bản:** v4.0

---

## 1. NGUYÊN TẮC XỬ LÝ TRONG BÁO CÁO V4
Mọi số liệu, khẳng định không thể truy vết trực tiếp về file log, script hoặc mã nguồn trong kho lưu trữ hiện tại được gán nhãn `[CHƯA XÁC MINH]` và chuyển đổi thành dấu `"—"` trong toàn bộ bảng biểu đối sánh học thuật, hoặc được giải trình lý do kỹ thuật chi tiết.

---

## 2. BẢNG DANH MỤC CÁC MỤC CHƯA XÁC MINH

| STT | Mục / Chỉ số | Giá trị Cũ trong Báo cáo v2/v3 | Tình trạng Kiểm toán v4 | Lý do Kỹ thuật & Hành động Chuẩn hóa trong Báo cáo v4 |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **URAG Retrieval Recall@5** | `76,40%` | **[CHƯA XÁC MINH SỐ TRANG/BẢNG]** | Kho lưu trữ nội bộ không có tệp PDF toàn văn của bài báo arXiv:2501.16276 để đối chiếu bảng biểu và trang cụ thể. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **2** | **URAG Intent / Routing Accuracy** | `90,80%` | **[CHƯA XÁC MINH SỐ TRANG/BẢNG]** | Tương tự, không thể mở bài báo gốc tại máy để xác thực phương pháp đo và mẫu số. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **3** | **URAG Faithfulness** | `86,00%` | **[CHƯA XÁC MINH SỐ TRANG/BẢNG]** | Thang đo Faithfulness của URAG có thể dùng LLM-as-a-judge trong khi FPTUniQA dùng Lexical Overlap trên văn bản quy chế. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **4** | **URAG Hallucination Rate** | `~14,00%` | **[CHƯA ĐO / SUY ĐOÁN ĐỊNH TÍNH]** | Bài báo URAG không có chỉ số Hallucination Rate số học như FPTUniQA; số ~14% là ước tính định tính từ mô tả lỗi. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **5** | **URAG End-to-End Latency** | `~2.100 ms` | **[CHƯA XÁC MINH PHÂN VỊ]** | Bài báo không công bố phân vị p50/p95, chỉ nêu ước tính gọi API OpenAI GPT-4. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **6** | **NEU-chatbot Tất cả Chỉ số** | `84,20%`, `100%`, `0%` | **[CHƯA XÁC MINH TOÀN VĂN]** | Không có tệp bài kỷ yếu hội thảo 2021 trong kho lưu trữ để kiểm chứng số liệu. Hơn nữa NEU-chatbot dùng Rasa SQL Template cứng, không tương đương kiến trúc LLM RAG. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **7** | **R2GQA Tất cả Chỉ số** | `84,60%` | **[KHÁC TẬP DỮ LIỆU & THIẾU BÀI GỐC]** | Con số 84,60% trích dẫn từ bài báo arXiv:2409.02840 trên benchmark HotpotQA, không thể so sánh với bài toán quy chế trường đại học. **Hành động: Đổi thành "—" trong Báo cáo v4.** |
| **8** | **Chỉ số Cohen's Kappa** | `0,86` | **[KHÔNG TỒN TẠI TỆP DỮ LIỆU]** | Quét toàn bộ kho lưu trữ không tìm thấy bất kỳ tệp dữ liệu nhật ký gán nhãn hay tính toán đồng thuận của 2 annotator độc lập. **Hành động: XÓA BỎ HOÀN TOÀN trong Báo cáo v4.** |
| **9** | **C5 Latency p50 (9,5 ms)** | `9,5 ms` | **[ĐÃ GIẢI THÍCH KỸ THUẬT]** | Độ trễ 9,5 ms đo được ở C5 là do 100% câu hỏi bị đẩy về Regex fallback nhanh và trả về từ chối hoặc tra bảng tức thì, không phản ánh độ trễ pipeline hoàn chỉnh. **Hành động: Giữ số đo thực tế nhưng thêm chú thích kỹ thuật rõ ràng.** |

---

## 3. DANH MỤC CÁC CHỈ SỐ NỘI BỘ ĐÃ ĐƯỢC XÁC MINH 100%
Ngược lại với các chỉ số ngoại tộc trên, **100% các đại lượng nội bộ** của FPTUniQA đều đã được đo đạc, kiểm toán và truy vết trực tiếp vào mã nguồn:
1. **Recall@5 và MRR trên $N=26$ câu retrieval gold:** Đã đo đạc trên 8 cấu hình độc lập (`experiments/ablation_clean/`).
2. **Wrong-Cohort Rate trên $N=6$ câu có nhãn khóa:** Đã trích xuất và giải thích tường tận cơ chế của BM25, FAISS, RRF và Hard Filter.
3. **Phân rã Faithfulness trên $N=100$ câu:** Tách riêng nhánh SSOT (63 câu: 100%), Text-RAG (26 câu: Lexical Overlap), và OOD (11 câu: 100%).
4. **Tập câu hỏi chưa dùng cho ablation ($N=50$):** Recall@5 Doc ID = 75,00%, Recall@5 Equiv = 75,00%, MRR = 0,7390, Wilson CI: [61,5%, 85,0%].
5. **Độ an toàn trên $N=35$ câu:** Tách riêng 20 Near-OOD và 15 Adversarial, có khoảng tin cậy Wilson 95% và phân loại 3 mức độ.
6. **Kiểm thử Đa lượt trên $N=1.000$ lượt:** Đầy đủ ma trận nhầm lẫn Topic-Switch (Macro F1 = 89,76%), phân rã độ trễ theo 4 tuyến (SSOT p50=10,57ms, Clarification p50=3,87ms, OOD p50=3,27ms, Text-RAG p50=5.752,30ms), và minh chứng 144 lượt CKB hỏi lại.

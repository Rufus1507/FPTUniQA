BÁO CÁO TỔNG QUAN VÀ ĐỊNH VỊ BÀI TOÁN: HỆ THỐNG HỎI ĐÁP ĐẠI HỌC TIẾNG VIỆT NHẬN BIẾT NGỮ CẢNH
Tác giả: Nguyễn Xuân Đỉnh, Lê Ngọc Phú, Nguyễn Anh Tín
TÓM TẮT
Các hệ thống hỏi đáp tự động về quy chế học vụ và tuyển sinh đại học đóng vai trò quan trọng trong việc giảm tải cho bộ phận tư vấn và nâng cao trải nghiệm của người học. Tuy nhiên, các giải pháp hiện nay thường gặp thách thức lớn khi xử lý dữ liệu phụ thuộc thời gian/khóa học, dữ liệu bảng biểu có cấu trúc và các hội thoại đa lượt mang tính tỉnh lược. Báo cáo này trình bày tổng quan nghiên cứu, phân tích chuyên sâu các khoảng trống kỹ thuật trong ba hệ thống tiêu biểu (HUST/NEU-Chatbot, UIT-R2GQA, HCMUT-URAG), từ đó đề xuất giải pháp Hybrid RAG kết hợp phân tích cú pháp ngữ nghĩa (Semantic Parsing), lọc siêu dữ liệu theo khóa học và tái cấu trúc câu hỏi theo ngữ cảnh nhằm tối ưu hóa độ chính xác và tính trung thực của câu trả lời.
Từ khóa: Hỏi đáp học vụ, Hybrid RAG, Semantic Parsing, Nhận biết ngữ cảnh, Khôi phục câu hỏi đa lượt, Lọc siêu dữ liệu.
1. ĐẶT VẤN ĐỀ VÀ BỐI CẢNH.
1.1. Thực trạng nhu cầu thông tin và sự quá tải kênh hỗ trợ
Khối lượng văn bản quy chế đào tạo tín chỉ, biểu mức học phí, chính sách học bổng và đề án tuyển sinh tại các cơ sở giáo dục đại học rất lớn và thay đổi liên tục theo từng năm học.
Các kênh hỗ trợ (Fanpage, Hotline, Email) luôn quá tải vào mùa cao điểm tuyển sinh và đăng ký học phần, gây độ trễ phản hồi lâu và tiêu tốn nhiều nhân sự trực hỗ trợ.
1.2. Thách thức kỹ thuật đặc thù trong miền dữ liệu học vụ
Ràng buộc khóa học và thời điểm hiệu lực (Temporal & Cohort Dependency): Cùng một ngành học nhưng sinh viên các khóa khác nhau áp dụng mức học phí và lộ trình đào tạo khác nhau. Nếu chỉ tìm kiếm theo độ tương đồng ngữ nghĩa véc-tơ, hệ thống rất dễ lấy nhầm văn bản cũ đã hết hiệu lực.
Dữ liệu số liệu dạng bảng biểu (Tabular Data): Các thông tin cốt lõi (biểu phí, mã tổ hợp, điểm chuẩn qua các năm, định mức tín chỉ) đều trình bày ở dạng bảng ma trận. Kỹ thuật cắt đoạn (chunking) thông thường nạp vào Vector DB sẽ phá vỡ cấu trúc dòng - cột, dẫn đến tình trạng mô hình sinh ảo giác (hallucination).
Hội thoại đa lượt có tính tỉnh lược (Multi-turn Context): Người dùng thường đặt câu hỏi ngắn, tỉnh lược chủ ngữ hoặc dùng từ chiếu vật (ví dụ: "Học phí ngành AI năm nay bao nhiêu?" → "Còn năm 2027 thì sao?" → "Phương thức xét tuyển của nó?"). Hệ thống cần hiểu ngữ cảnh hội thoại trước đó để bổ sung thực thể.
2. TỔNG QUAN CÁC NGHIÊN CỨU TƯƠNG TỰ
Nghiên cứu được tiếp cận từ chatbot tổng quát dựa trên kịch bản/ý định đến các hệ thống đọc hiểu quy chế và tư vấn tuyển sinh chuyên biệt:
2.1. Tiếp cận dựa trên kịch bản và phân loại ý định: HUST/NEU-Chatbot [1]
Hướng tiếp cận & Kiến trúc: Chatbot hướng phân loại ý định dựa trên nền tảng Rasa Framework kết hợp mô hình phân loại đa nhiệm DIETClassifier và tiền huấn luyện ngôn ngữ BERT-base [1].
Việc tinh chỉnh mô hình (Fine-tuning):
Mô hình sử dụng: bert-base-uncased làm bộ trích xuất đặc trưng ngôn ngữ [1].
Mô hình được huấn luyện/tinh chỉnh: Huấn luyện lớp phân loại ý định (DIETClassifier) và trích xuất thực thể chuỗi (CRF) trực tiếp trên tập dữ liệu tuyển sinh [1].
Nguồn gốc dữ liệu:
Data dùng huấn luyện mô hình: Thu thập trực tiếp từ tin nhắn, thắc mắc thực tế của thí sinh và phụ huynh gửi về Fanpage Tuyển sinh chính thức của Đại học Kinh tế Quốc dân (NEU) trên Facebook Messenger. Quy mô gồm hơn 50 ý định (intents) với khoảng 1.500 câu ví dụ huấn luyện [1].
Data để chatbot dựa vào trả lời: Sử dụng kho kịch bản và câu trả lời chuẩn được định nghĩa, gán nhãn tĩnh trong các tệp cấu hình kịch bản (file nlu.yml, domain.yml) [1].
Kết quả cốt lõi:
Tốc độ huấn luyện nhanh gấp 6 lần so với fine-tune toàn bộ LLM; độ chính xác phân loại ý định đạt F1-score = 97.6% [1].
Thực tế tiếp nhận hơn 50.000 tin nhắn, trả lời chính xác 95.79% các câu hỏi thuộc phạm vi tuyển sinh NEU và cắt giảm 80% nhân sự trực tư vấn [1].
Hạn chế: Hoàn toàn dựa vào kịch bản đóng; không có khả năng đọc hiểu văn bản mới; khi có chính sách hay đề án mới phải gán nhãn và cấu hình lại thủ công từ đầu [1].
2.2. Tiếp cận đọc hiểu quy chế trích xuất: UIT-R2GQA [2]
Hướng tiếp cận & Kiến trúc: Đường ống 3 tầng Retriever (Truy xuất) - Reader (Đọc hiểu trích đoạn) - Generator (Sinh câu trả lời tự nhiên) [2].
Việc tinh chỉnh mô hình (Fine-tuning):
Tầng Retriever: Tinh chỉnh Bi-Encoder bằng hàm mất mát MarginMSE kết hợp BM25 [2].
Tầng Reader: Fine-tune mô hình XLM-RoBERTa-Large theo cơ chế gán nhãn chuỗi BIO để trích xuất chính xác đoạn văn chứa câu trả lời [2].
Tầng Generator: Fine-tune mô hình sinh Seq2Seq mBART-50 (và các biến thể BARTpho, ViT5) nhận đầu vào là câu hỏi kết hợp đoạn trích xuất tinh gọn từ Reader để sinh câu trả lời đàm thoại [2].
Nguồn gốc dữ liệu:
Data tài liệu tri thức: Thu thập từ 21 văn bản pháp quy đào tạo đại học chính quy (định dạng file DOCX, PDF, ảnh scan nội bộ của trường); làm phẳng bảng biểu thành văn bản và phân đoạn thành 294 điều khoản quy chế (contexts) [2].
Data huấn luyện mô hình (Bộ ViRHE4QA): Gồm 9.758 cặp câu hỏi - đáp án hoàn chỉnh do nhóm 7 cộng tác viên xây dựng dựa trên 21 văn bản trên qua 6 pha kiểm định chéo độc lập [2].
Data để chatbot dựa vào trả lời: Trích xuất trực tiếp từ các đoạn văn bản trong 21 tệp quy chế đào tạo đã lập chỉ mục [2].
Kết quả cốt lõi:
Tầng Retriever Ensemble (BM25 + Bi-Encoder) đạt Top-1 là 72.13% (vượt BM25 đơn lẻ 3.38%) [2].
Tầng sinh mBART-50 đạt BLEU-4 = 73.21% [2].
Hệ thống vận hành cục bộ đạt BLEU-4 cao hơn hệ thống Naive RAG dùng GPT-3.5 (+8.82%) nhưng chi phí gọi API là 0 USD [2].
Hạn chế: Giới hạn cửa sổ ngữ cảnh 512 tokens; làm phẳng bảng biểu thành văn bản thô gây mất cấu trúc hàng - cột (dễ đọc sai số liệu); chưa hỗ trợ hội thoại đa lượt [2].
2.3. Tiếp cận RAG phân tầng hợp nhất: HCMUT-URAG [3]
Hướng tiếp cận & Kiến trúc: Khung RAG hợp nhất phân tầng hai cấp độ gồm tầng tìm kiếm FAQ làm giàu (URAG-F) và tầng tìm kiếm văn bản cắt đoạn theo ngữ nghĩa (URAG-D) [3].
Việc tinh chỉnh mô hình (Fine-tuning):
Mô hình nhúng: Sử dụng dangvantuan/vietnamese-embedding (SBERT) [3].
Mô hình ngôn ngữ sinh: Sử dụng mô hình nguồn mở cục bộ ura-llama-7b (mô hình LLaMA đã được tiếp tục tiền huấn luyện mở rộng trên ngữ liệu tiếng Việt) [3].
Cơ chế: Không fine-tune mô hình cho từng tác vụ hẹp mà khai thác năng lực In-context Learning và Prompt Engineering của LLM kết hợp dữ liệu truy xuất [3].
Nguồn gốc dữ liệu:
Data tài liệu tri thức: Thu thập từ 300 tài liệu công khai trên cổng thông tin website chính thức của nhà trường (hcmut.edu.vn), bao gồm đề án tuyển sinh, biểu phí, quy định học vụ, thông tin khoa ngành [3].
Data làm giàu tri thức: Dùng LLM mở rộng mỗi câu hỏi trong FAQ thành 20 biến thể câu hỏi đồng nghĩa để lập chỉ mục kho URAG-F [3].
Data kiểm thử đánh giá: Bộ dữ liệu gồm 500 câu hỏi thực tế thu thập trực tiếp từ học sinh THPT trong 3 ngày hội tư vấn tuyển sinh tại trường (gồm 427 câu tra cứu sự kiện Factual và 73 câu tư vấn lập luận Reasoning) [3].
Data để chatbot dựa vào trả lời: Kho tri thức FAQ làm giàu và các đoạn văn bản (chunks) trích xuất từ 300 tài liệu website trường [3].
Kết quả cốt lõi:
Đạt độ chính xác chung 62.8% trên 500 câu hỏi thực tế, vượt qua các LLM thương mại lớn có web search (vượt GPT-4o 54.4%, Claude 3.5 Sonnet 50.2%, Gemini 1.5 Pro 44.0%) [3].
Ở nhóm câu hỏi dữ kiện thực tế (Factual), hệ thống đạt 67.0% (vượt GPT-4o +15.9%) [3].
Vận hành on-premise ổn định với độ trễ phản hồi dưới 5 giây và chi phí gọi API là 0 USD [3].
Hạn chế: Hiệu năng nhóm câu hỏi lập luận (Reasoning) còn thấp (chỉ đúng 38.4% so với GPT-4o 74.0%); tìm kiếm véc-tơ đơn thuần dễ trôi mã ngành; chưa hỗ trợ ngữ cảnh hội thoại tiếp nối [3].
3. PHÂN TÍCH VÀ ĐÁNH GIÁ SO SÁNH
3.1. Đối sánh tổng hợp các giải pháp nghiên cứu
Bảng 1. Bảng đối sánh tổng hợp giữa các nghiên cứu hiện hữu và giải pháp đề xuất

Tiêu chí so sánh
HUST/NEU-Chatbot [1]
UIT-R2GQA [2]
HCMUT-URAG [3]
Đề tài đề xuất
Hướng tiếp cận
Intent/Slot Pipeline truyền thống
Đọc hiểu trích xuất (Retriever - Reader - Generator)
RAG phân tầng (URAG-F FAQ + URAG-D Chunks)
Hybrid RAG + Phân tích cú pháp ngữ nghĩa (Semantic Parsing)
Nguồn dữ liệu gốc
Fanpage NEU Messenger; kịch bản cấu hình YAML
21 file PDF/DOCX quy chế đào tạo → 294 điều khoản
300 tài liệu từ website trường hcmut.edu.vn
Đa nguồn: PDF/DOCX quy chế + CSDL bảng biểu SQLite/JSON
Tinh chỉnh mô hình
Fine-tune DIETClassifier và tầng phân loại trên BERT
Fine-tune XLM-R (Reader) và mBART-50 (Generator)
LLaMA tiếng Việt (In-context Learning, không fine-tune)
Fine-tune Query Rewriter và Semantic Parser
Xử lý bảng biểu
Gán slot thủ công theo kịch bản
Làm phẳng bảng thành văn bản thô (dễ sai lệch)
Chuyển thành câu tóm tắt và câu hỏi FAQ
Tra cứu trực tiếp trên CSDL cấu trúc (SQLite/JSON)
Hội thoại đa lượt
Rasa Rule & Memorization Policy tĩnh
Chưa hỗ trợ (câu hỏi đơn)
Chưa tối ưu (câu hỏi đơn)
Module Context-Aware Query Rewriter khôi phục câu tỉnh lược
Lọc theo khóa/năm
Bắt từ khóa tĩnh / Regex
Không lọc siêu dữ liệu
Tìm kiếm véc-tơ toàn văn
Metadata Pre-filtering theo Khóa học và Năm hiệu lực
Hiệu năng chính
F1 = 97.6%; thực tế đúng 95.79%
Retriever Top-1 = 72.13%; BLEU-4 = 73.21%
Accuracy = 62.8%; Factual đạt 67.0%
Mục tiêu Accuracy >82%; Bảng biểu >95%; Đa lượt >85%
Chi phí API
0 USD (On-premise)
0 USD (GPU RTX 3090)
0 USD (LLaMA 7B nội bộ)
0 USD (Hạ tầng GPU nội bộ)

3.2. Nhận diện các khoảng trống nghiên cứu cốt lõi (Research Gaps)
Khoảng trống xử lý dữ liệu lai (Hybrid-Data Routing Gap): Các công trình trước đều áp dụng một đường ống duy nhất cho mọi dạng dữ liệu [1, 2, 3]. Khi gặp thông tin bảng biểu (học phí, chuẩn tín chỉ, điểm chuẩn), việc ép thành văn bản thô khiến mô hình dễ nhầm dòng - cột và sinh ảo giác số liệu. Cần cơ chế phân tích cú pháp ngữ nghĩa (Semantic Parsing) để tách riêng: câu hỏi số liệu tra cứu trên CSDL bảng biểu (SQL/JSON), câu hỏi chính sách mở tra cứu qua Hybrid RAG.
Khoảng trống kiểm soát tính thời điểm và khóa học (Temporal & Cohort Faithfulness Gap): Quy định và biểu phí đại học gắn chặt với từng khóa tuyển sinh. Các mô hình truy xuất thuần véc-tơ hiện tại [2, 3] thiếu bộ lọc cứng siêu dữ liệu (Metadata Pre-filtering), dẫn đến việc kéo về các quy chế cũ đã hết hiệu lực do độ tương đồng từ ngữ cao.
Khoảng trống giao tiếp hội thoại đa lượt (Context-Aware Multi-turn Rewriting Gap): Người học thường hỏi tiếp nối bằng các câu ngắn hoặc đại từ chiếu vật. Các mô hình đọc hiểu hiện hành [2, 3] chỉ xử lý câu đơn lập, chưa có tầng Context Rewriting độc lập để tái cấu trúc câu hỏi trước khi truy xuất.
Khoảng trống đánh giá phân rã thành phần (Modular Ablation Rigor Gap): Các nghiên cứu thường đánh giá End-to-End tổng thể hoặc chỉ qua chỉ số ngôn ngữ bề mặt (BLEU, ROUGE), thiếu một ma trận thực nghiệm bóc tách để đo lường độc lập năng lực từng module: khả năng truy xuất, chất lượng trích xuất cấu trúc, tính trung thực chống ảo giác và tỷ lệ từ chối câu hỏi ngoài phạm vi.
4. ĐỀ XUẤT MÔ HÌNH VÀ KIẾN TRÚC GIẢI PHÁP
4.1. Tiền xử lý hội thoại đa lượt (Context Rewriting): Bổ sung module Context-Aware Query Rewriter phân giải hiện tượng tỉnh lược và đồng tham chiếu dựa trên lịch sử trao đổi 3-5 lượt gần nhất.
4.2. Định tuyến dữ liệu lai (Hybrid Data Routing): Chuyển đổi câu hỏi thành cấu trúc tường minh (Structured Contract Schema) để phân luồng xử lý:
Nhánh Bảng biểu: Tra cứu trực tiếp trên CSDL SQLite/JSON để đảm bảo độ chính xác tuyệt đối 100%.
Nhánh Văn bản quy chế: Định tuyến qua bộ truy xuất lai Hybrid RRF (kết hợp BM25 bắt từ khóa mã ngành và FAISS Dense bắt ngữ nghĩa).
4.3. Lọc siêu dữ liệu cứng (Metadata Hard Pre-filtering): Áp dụng lọc siêu dữ liệu theo Khóa tuyển sinh (Cohort) và Năm hiệu lực trước khi tính toán độ tương đồng véc-tơ.
4.4. Khung đánh giá phân rã (Modular Ablation Rigor): Thiết lập ma trận đánh giá phân rã 6 cấu hình (Ablation Matrix từ Naive RAG đến hệ thống toàn diện) để đo lường độc lập từng thành phần.
5. TÀI LIỆU THAM KHẢO
[1] Nguyen, T. T., Le, H. Q., & Nguyen, V. H. (2021). Building an Automated Conversational Agent for University Admission Counseling using Rasa Framework and BERT. Proceedings of the International Conference on Knowledge and Systems Engineering (KSE).
[2] Pham, V. T., Tran, T. T., & Nguyen, K. V. (2024). ViRHE4QA: A Vietnamese Reading Comprehension Dataset and System for Higher Education Regulations. IEEE Access / VNUHCM-UIT.
[3] Nguyen, D. H., & Quan, T. T. (2025). HCMUT-URAG: A Unified Retrieval-Augmented Generation Framework for Vietnamese University Admissions Counseling. Trường Đại học Bách khoa - ĐHQG-HCM (HCMUT).




PHẦN 3: GIẢI PHÁP KỸ THUẬT VÀ ĐÁNH GIÁ KIẾN TRÚC HỆ THỐNG
Hệ thống Hybrid RAG + Semantic Parsing Chống Ảo Giác cho Hỏi Đáp Học Vụ Tiếng Việt Nhận Biết Ngữ Cảnh (FPTUniQA)
Tác giả: Nguyễn Xuân Đỉnh, Lê Ngọc Phú, Nguyễn Anh Tín
Mục lục nội dung
3.1. Giải pháp kỹ thuật giải quyết từng thành phần kiến trúc
    • 3.1.1. Tầng Thu thập & Chuẩn hóa Dữ liệu Đa Định dạng (Ingestion Layer)
    • 3.1.2. Tầng Phân giải Ngữ cảnh Hội thoại Đa lượt (Context Layer)
    • 3.1.3. Tầng Phân tích Ngữ nghĩa & Định tuyến Ý định (Parsing & Routing Layer)
    • 3.1.4. Tầng Truy xuất Thông tin Lai Đa cấp (Retrieval Layer)
    • 3.1.5. Tầng Tra cứu CSDL Có Cấu trúc Xác định (Structured Lookup Layer)
    • 3.1.6. Tầng Sinh Ngôn ngữ, Kiểm soát Tính trung thực & Phòng vệ (Generation & Guardrail Layer)
    • 3.1.7. Tầng Giao tiếp & Quan sát Hệ thống (Presentation & Observability Layer)
3.2. Nhận xét và đánh giá mức độ tham gia của từng thành phần vào kiến trúc
    • 3.2.1. Khung tiêu chí đánh giá mức độ đóng góp kiến trúc
    • 3.2.2. Bảng phân cấp và đánh giá mức độ tham gia của các thành phần
    • 3.2.3. Đánh giá chuyên sâu theo 4 nhóm phân cấp kiến trúc
    • 3.2.4. Phân tích khả năng chịu lỗi và tính bền vững hệ thống (Fault-Tolerance & Resilience)
3.3. Thành phần quyết định chất lượng kiến trúc hệ thống
    • 3.3.1. Nhận định cốt lõi: Cặp thành phần quyết định chất lượng kiến trúc
    • 3.3.2. Vì sao LLM Generator và Vector Embedding không phải yếu tố quyết định chất lượng?
    • 3.3.3. Luận giải chuyên sâu: Bộ đôi Semantic Parser & Centralized Router — Trục điều phối chất lượng
    • 3.3.4. Luận giải chuyên sâu: Metadata Hard Pre-filter — Chốt chặn bảo toàn tính đúng đắn theo khóa học
    • 3.3.5. Sự cộng hưởng kiến trúc (Architectural Synergy) và kết luận
3. GIẢI PHÁP KỸ THUẬT
3.1. Giải pháp kỹ thuật giải quyết từng thành phần kiến trúc
Hệ thống FPTUniQA được xây dựng nhằm giải quyết triệt để 3 thách thức học vụ đặc thù đã được nhận diện trong Báo cáo 1: (1) Ràng buộc khóa học và thời điểm hiệu lực của văn bản quy chế, (2) Ảo giác số liệu dạng bảng biểu học phí, tín chỉ, và (3) Hiện tượng tỉnh lược, dùng đại từ chiếu vật trong hội thoại đa lượt. Dưới đây là giải pháp kỹ thuật cụ thể cho từng thành phần trong mô hình kiến trúc phân tầng 7 lớp (được đề xuất ở Báo cáo 2), tập trung vào nguyên lý thiết kế và cơ chế tương tác kiến trúc thay vì chi tiết cài đặt mã nguồn.
3.1.1. Tầng Thu thập & Chuẩn hóa Dữ liệu Đa Định dạng (Ingestion Layer)
• Vấn đề kỹ thuật cần giải quyết: Dữ liệu học vụ đại học tồn tại ở các định dạng phân tán cao: văn bản quy chế dạng PDF scan/DOCX hành chính, biểu phí và chỉ tiêu dạng bảng tính XLSX phức tạp với nhiều ô gộp (merged cells), và các thông báo tuyển sinh dạng trang web HTML. Việc "làm phẳng" (flatten) toàn bộ tài liệu thành văn bản thô theo cách tiếp cận RAG truyền thống sẽ phá hủy hoàn toàn quan hệ cấu trúc hàng - cột của dữ liệu số liệu, làm mất tiêu đề phân cấp (H1-H6), dẫn đến việc mô hình trích xuất sai lệch hoàn toàn.
• Giải pháp kiến trúc: Hệ thống thiết lập một Cổng chuyển đổi tài liệu thống nhất (Unified Document Ingestion Gateway) dựa trên Microsoft MarkItDown kết hợp kiến trúc Phân luồng dữ liệu kép (Dual-Path Data Pipeline):
Chuẩn hóa đa định dạng về Markdown có cấu trúc: MarkItDown đóng vai trò bộ phân giải đầu vào đa năng, nhận diện và chuẩn hóa mọi tệp PDF, DOCX, XLSX, hình ảnh OCR sang Markdown sạch. Định dạng Markdown bảo toàn trọn vẹn cấu trúc bảng (dưới dạng Markdown table) và cây phân cấp tiêu đề của văn bản quy phạm pháp luật (Chương → Điều → Khoản → Điểm).
Tách luồng dữ liệu kép (Dual-Path Ingestion):
Nhánh dữ liệu quan hệ (Tabular/Relational Data): Table Extractor bóc tách riêng các bảng ma trận biểu phí, điểm chuẩn, định mức tín chỉ sang CSDL bảng biểu có cấu trúc (SQLite/JSON Database). Dữ liệu này được chuẩn hóa các trường số học (VND, số tín chỉ, mã ngành) làm nguồn chân lý tuyệt đối (ground-truth).
Nhánh dữ liệu văn bản quy chế (Unstructured Narrative Data): Chunker thực hiện phân đoạn thông minh dựa trên ranh giới Điều/Khoản kết hợp cửa sổ trượt (400–500 tokens, overlap 50 tokens), gắn kèm Metadata Tagger gán nhãn siêu dữ liệu bắt buộc (doc_id, applies_to_cohort, effective_date, campus, doc_type) theo đúng chuẩn Contract 1.
Cách ly rủi ro qua Interface Contract 1: Việc đóng gói toàn bộ đầu ra của Ingestion Layer vào một schema chuẩn (Contract 1: doc_id, text, title, source, effective_date, applies_to_cohort, structured_payload) giúp tầng Ingestion hoạt động hoàn toàn offline và độc lập với các tầng xử lý truy vấn online, cho phép tái lập chỉ mục (re-indexing) mà không ảnh hưởng đến API phục vụ.
3.1.2. Tầng Phân giải Ngữ cảnh Hội thoại Đa lượt (Context Layer)
• Vấn đề kỹ thuật cần giải quyết: Trong thực tế tư vấn học vụ, người dùng hầu như không bao giờ đặt câu hỏi đầy đủ ở mọi lượt tương tác. Họ thường xuyên hỏi tiếp nối bằng các câu rút gọn, tỉnh lược chủ ngữ hoặc dùng từ chiếu vật phụ thuộc ngữ cảnh trước đó (Ví dụ: Lượt 1: "Học phí ngành Kỹ thuật phần mềm khóa 2026 cơ sở Cần Thơ bao nhiêu?" → Lượt 2: "Còn cơ sở TP.HCM thì sao?" → Lượt 3: "Phương thức xét tuyển của nó?"). Nếu đưa trực tiếp câu hỏi ở Lượt 2 và Lượt 3 vào bộ tìm kiếm hoặc bộ phân loại ý định, hệ thống sẽ bị "trôi thực thể" (entity drift), dẫn đến việc truy xuất sai hoàn toàn.
• Giải pháp kiến trúc:
Module Context-Aware Query Rewriter độc lập tiền truy xuất (Pre-retrieval Query Rewriter): Tầng Context được đặt ngay trước Semantic Parser và Retrieval Pipeline. Module này duy trì một Bộ đệm trượt lịch sử phiên (Sliding Session Buffer) lưu trữ 3–5 lượt tương tác gần nhất.
Cơ chế phân giải tỉnh lược và đồng tham chiếu (Ellipsis & Coreference Resolution): Rewriter tiếp nhận original_query cùng session_history, phân tích mối quan hệ ngữ nghĩa để phục hồi đầy đủ các thực thể bị ẩn (ngành học, khóa tuyển sinh, địa điểm cơ sở, chủ đề chính sách) và sinh ra rewritten_query có ngữ nghĩa độc lập hoàn chỉnh (Self-contained Query).
Độc lập trách nhiệm kiến trúc: Query Rewriter chỉ làm đúng một nhiệm vụ là "làm rõ câu hỏi", không tham gia vào việc tìm kiếm hay sinh câu trả lời. Điều này tránh việc dồn toàn bộ gánh nặng ghi nhớ ngữ cảnh dài vào prompt của LLM sinh câu trả lời ở tầng cuối, giúp giảm đáng kể chi phí token và độ trễ phản hồi.
3.1.3. Tầng Phân tích Ngữ nghĩa & Định tuyến Ý định (Parsing & Routing Layer)
• Vấn đề kỹ thuật cần giải quyết: Các hệ thống chatbot truyền thống thường chỉ có hai thái cực: hoặc dùng rule-based đóng (cứng nhắc, dễ gãy khi người dùng diễn đạt tự nhiên) hoặc dùng LLM RAG cho mọi câu hỏi (dễ ảo giác khi gặp câu hỏi số liệu, tốn kém chi phí và chậm chạp). Cần một cơ chế kiến trúc trung gian có khả năng hiểu sâu câu hỏi tự nhiên nhưng điều hướng chuẩn xác sang đúng cơ chế xử lý chuyên biệt.
• Giải pháp kiến trúc: Kiến trúc xây dựng mô hình Phân tích cú pháp ngữ nghĩa kết hợp Định tuyến tập trung (Semantic Parsing & Centralized Routing) thông qua 3 trụ cột:
Semantic Parser (Intent & Slot Extraction): Chuyển hóa câu hỏi ngôn ngữ tự nhiên đã viết lại (rewritten_query) thành một truy vấn có cấu trúc hoàn chỉnh theo chuẩn Contract 3 (ParsedQuery), bao gồm:
intent: Ý định cốt lõi (ví dụ: tuition_lookup, policy_lookup, scholarship_lookup, ood).
slots: Tập thực thể có cấu trúc được bóc tách dạng khóa-giá trị (ví dụ: program: "Kỹ thuật phần mềm", cohort: "2026", campus: "can_tho", topic: "hoc_phi").
confidence: Điểm số độ tin cậy của việc nhận dạng ý định.
Phòng vệ suy thoái mềm (Graceful Degradation via Regex Fallback): Nếu Semantic Parser gặp sự cố ngoại lệ (LLM timeout, lỗi mạng, hoặc confidence < ngưỡng an toàn), hệ thống lập tức kích hoạt bộ trích xuất luật Rule-based Regex Fallback. Vì cả Semantic Parser và Regex Fallback đều trả về cùng một cấu trúc dữ liệu Contract 3, hệ thống chuyển đổi trạng thái mượt mà mà các tầng sau không hề bị gián đoạn.
Nguyên tắc Định tuyến một điểm duy nhất (Single-Point-of-Routing Principle): Toàn bộ kết quả từ Semantic Parser và Regex Fallback đều phải đi qua Router duy nhất. Router dựa trên trường intent và các slots đã trích xuất để rẽ nhánh chuẩn xác sang 1 trong 4 tuyến xử lý:
Nhánh 1 (StructuredRoute): Điều hướng các câu hỏi tra cứu định lượng sang Tầng Tra cứu CSDL Có cấu trúc.
Nhánh 2 (HybridRAGRoute): Điều hướng các câu hỏi giải thích chính sách, quy chế mở sang Tầng Truy xuất Thông tin Lai.
Nhánh 3 (ClarificationRoute): Điều hướng câu hỏi mơ hồ, thiếu thực thể trọng yếu yêu cầu người dùng xác nhận lại.
Nhánh 4 (OODRoute): Điều hướng câu hỏi ngoài phạm vi học vụ sang Tầng Từ chối an toàn.
3.1.4. Tầng Truy xuất Thông tin Lai Đa Cấp (Retrieval Layer)
• Vấn đề kỹ thuật cần giải quyết: Trong miền quy chế học vụ: Tìm kiếm từ khóa thuần túy (BM25) bắt rất tốt các từ viết tắt ("ĐKMH", "KLTN", mã môn "SWE201c"), nhưng thất bại khi người dùng dùng từ đồng nghĩa hoặc diễn đạt gián tiếp ("bị đuổi học" thay vì "buộc thôi học"). Ngược lại, tìm kiếm ngữ nghĩa véc-tơ thuần túy (Dense Vector Search) nắm bắt tốt ý niệm ngữ nghĩa, nhưng rất dễ bị "trôi mã số", nhầm lẫn giữa các mã ngành tương tự, và đặc biệt là không phân biệt được văn bản cũ và văn bản mới nếu câu chữ quy định giống nhau.
• Giải pháp kiến trúc: Hệ thống thiết lập Kiến trúc truy xuất lai hai giai đoạn (Two-Stage Hybrid Retrieval Architecture) kết hợp Lọc siêu dữ liệu cứng:
Lọc cứng siêu dữ liệu tiền truy xuất (Metadata Hard Pre-filtering): Dựa trên các slots trích xuất từ Contract 3 (cohort, effective_date, campus), hệ thống tiến hành loại bỏ ngay lập tức các tài liệu không khớp TRƯỚC KHI thực hiện tính toán độ tương đồng. Đây là chìa khóa triệt tiêu nguy cơ trôi niên khóa.
Truy xuất song song đa phương thức (Parallel Multi-Modal Retrieval):
Kênh Sparse (BM25Plus): Tinh chỉnh thuật toán BM25Plus kết hợp bộ tách từ tiếng Việt chuyên sâu (pyvi) và lọc stopwords học vụ tiếng Việt, tối ưu bắt chính xác các thuật ngữ pháp lý, mã ngành, mã môn.
Kênh Dense (FAISS IndexFlatIP): Sử dụng mô hình nhúng văn bản đa ngôn ngữ chất lượng cao (multilingual-e5-base), chuẩn hóa véc-tơ L2 và tính khoảng cách tích vô hướng (Inner Product) để biểu diễn không gian ngữ nghĩa sâu.
Hợp nhất thứ hạng RRF (Reciprocal Rank Fusion): Áp dụng thuật toán RRF với tham số điều hòa k = 60 để hợp nhất danh sách ứng viên từ hai kênh. RRF xử lý dựa trên vị trí thứ hạng tương đối thay vì điểm số thô, khắc phục hiện tượng mất cân bằng thang điểm giữa mô hình từ khóa và mô hình nhúng.
Tái xếp hạng sâu bằng Cross-Encoder (Reranking Stage): Lấy Top-20 (hoặc Top-50) ứng viên từ bước RRF đưa qua mô hình Cross-Encoder chuyên biệt (bge-reranker-base). Cross-Encoder chấm điểm tương tác toàn phần giữa từng cặp (câu hỏi, đoạn văn), đánh giá độ liên quan ngữ nghĩa chi tiết ở cấp độ từ ngữ và ngữ cảnh, chắt lọc ra Top-5 đoạn trích tinh hoa nhất đáp ứng chuẩn Contract 2.
3.1.5. Tầng Tra cứu CSDL Có Cấu trúc Xác định (Structured Lookup Layer)
• Vấn đề kỹ thuật cần giải quyết: Mọi mô hình ngôn ngữ lớn (LLM), dù tân tiến đến đâu, đều mang bản chất là mô hình xác suất sinh từ tiếp theo (probabilistic next-token predictor). Do đó, khi phải trả lời các thông tin định lượng đòi hỏi độ chính xác tuyệt đối như số tiền học phí từng kỳ, số tín chỉ tốt nghiệp, hoặc điểm sàn xét tuyển, việc để LLM tự đọc một đoạn văn và phát biểu số liệu luôn tiềm ẩn nguy cơ ảo giác số học (numerical hallucination) — ví dụ tự nhầm 12.500.000 VNĐ thành 15.200.000 VNĐ hoặc nhầm biểu phí cơ sở này sang cơ sở khác.
• Giải pháp kiến trúc:
Đường dẫn thực thi xác định (Deterministic Execution Path): Khi Router nhận diện intent là tuition_lookup hoặc credit_lookup, luồng xử lý được tách hoàn toàn khỏi đường ống suy luận xác suất của RAG và đưa sang Structured Lookup Layer.
Công cụ truy vấn CSDL trực tiếp (Structured Query Engine): Dựa trên các slots chuẩn hóa từ Contract 3 (program, cohort, campus), hệ thống ánh xạ thành câu truy vấn trực tiếp vào CSDL quan hệ (SQLite/JSON) đã được chuẩn bị sẵn ở khâu Ingestion.
Đảm bảo độ chính xác 100% và siêu độ trễ thấp: Dữ liệu trả về từ tầng này là số liệu thực tế được ghi nhận chính thức, loại bỏ 100% nguy cơ ảo giác số liệu. Thời gian phản hồi của tầng này cực nhanh (dưới 5ms), tiết kiệm tối đa tài nguyên tính toán của toàn hệ thống.
3.1.6. Tầng Sinh Ngôn ngữ, Kiểm soát Tính trung thực & Phòng vệ (Generation & Guardrail Layer)
• Vấn đề kỹ thuật cần giải quyết: Khi nhận được ngữ cảnh truy xuất từ Tầng 4 hoặc số liệu từ Tầng 5, LLM có thể vẫn có xu hướng tự chắp vá kiến thức ngoài luồng, trả lời thừa thãi các thông tin không có căn cứ văn bản, hoặc bị tấn công prompt injection khi người dùng cố tình hỏi các câu hỏi độc hại, chính trị, đời tư nằm ngoài phạm vi học vụ (OOD).
• Giải pháp kiến trúc: Kiến trúc thiết lập cơ chế Sinh câu trả lời có kiểm soát nghiêm ngặt (Strict Grounded Generation) và Hệ thống phòng vệ kép (Dual Guardrails):
Ràng buộc ngữ cảnh nghiêm ngặt (Strict Grounding Prompting): Khung prompt của LLM được thiết kế với chỉ thị hệ thống chặt chẽ: Chỉ được phép phát biểu dựa trên thông tin có trong phần Context được cung cấp; nếu ngữ cảnh không đủ thông tin để trả lời, phải thông báo thẳng thắn thay vì tự suy diễn.
Trích dẫn nguồn chuẩn hóa (Citation Enforcement): Hệ thống tự động bóc tách và đối soát các đoạn căn cứ trong câu trả lời với tài liệu gốc, đánh số ký hiệu trích dẫn [Nguồn 1], [Nguồn 2] trực tiếp trong câu văn, đồng thời trả về danh sách đối tượng Citation (gồm doc_id, tên văn bản quy chế, điều khoản cụ thể) theo đúng chuẩn Contract 1.
Phòng vệ chống ảo giác số liệu (Hallucination Guardrail Check): Tầng kiểm duyệt hậu sinh thực hiện quét đối chiếu các thực thể số (tiền tệ, ngày tháng, mã số) xuất hiện trong câu trả lời sinh ra so với Context gốc. Nếu phát hiện có số lạ không bắt nguồn từ Context, cờ cảnh báo possible_hallucination = True sẽ được kích hoạt để cảnh báo người dùng.
Phòng vệ ngoài miền (OOD Guardrail): Ngắt mạch ngay lập tức các câu hỏi không liên quan đến giáo dục/học vụ, từ chối lịch sự và an toàn mà không tốn chi phí gọi truy xuất tài liệu hay suy luận LLM phức tạp.
3.1.7. Tầng Giao tiếp & Quan sát Hệ thống (Presentation & Observability Layer)
• Vấn đề kỹ thuật cần giải quyết: Hệ thống cần cung cấp giao diện thân thiện cho sinh viên, đồng thời phải cung cấp giao diện lập trình ứng dụng (API) chuẩn hóa để tích hợp với cổng thông tin sinh viên của nhà trường. Quan trọng hơn, đối với một hệ thống học thuật phức tạp, nếu không có cơ chế ghi vết toàn diện, việc xác định nguyên nhân gốc rễ của lỗi (Error Attribution) khi thử nghiệm và đánh giá chất lượng hệ thống là bất khả thi.
• Giải pháp kiến trúc:
Đóng gói dịch vụ Backend chuẩn RESTful: FastAPI Gateway chịu trách nhiệm định tuyến API, kiểm thực dữ liệu đầu vào/đầu ra theo chuẩn OpenAPI Swagger, tách bạch endpoint nghiệp vụ hỏi đáp (/api/v1/query) và endpoint giám sát trạng thái sức khỏe máy chủ (/api/v1/health).
Giao diện Chatbot tương tác (Streamlit UI): Cung cấp trải nghiệm hội thoại đa lượt mượt mà, hỗ trợ hiển thị luồng suy luận, huy hiệu phân loại intent của Router, nguồn trích dẫn pháp lý có thể bấm mở rộng, và cảnh báo độ tin cậy.
Ghi vết cấu trúc phục vụ quan sát & đánh giá (Structured JSONL Logging): Mỗi lượt tương tác hỏi đáp được hệ thống tự động ghi nhận toàn bộ 7 trường dữ liệu trạng thái cốt lõi: original_query → rewritten_query → parsed_query (Contract 3) → retrieved_docs → reranked_docs (Contract 2) → final_context → citations & answer (Contract 1). Nhờ đó, khi một câu trả lời bị sai lệch, nhóm kỹ thuật có thể truy vết chính xác lỗi xảy ra tại tầng nào.
3.2. Nhận xét và đánh giá mức độ tham gia của từng thành phần vào kiến trúc
3.2.1. Khung tiêu chí đánh giá mức độ đóng góp kiến trúc
Để đánh giá một cách khoa học và khách quan mức độ tham gia của từng thành phần vào sự thành bại của kiến trúc FPTUniQA, báo cáo xác lập khung đánh giá 4 chiều dựa trên các nguyên lý kỹ thuật phần mềm và kiến trúc hệ thống AI:
Tính cốt lõi kiến trúc (Architectural Criticality): Mức độ thiết yếu của thành phần. Nếu tách bỏ thành phần này, kiến trúc hệ thống có bị gãy đổ hoặc đánh mất bản sắc thiết kế ban đầu hay không?
Đóng góp chống ảo giác & Bảo toàn tính đúng đắn (Faithfulness & Anti-Hallucination Impact): Tỷ lệ đóng góp trực tiếp vào việc loại bỏ ảo giác số liệu, trôi niên khóa và sai lệch nội dung quy chế.
Đóng góp vào tính thích ứng & Chịu lỗi (Resilience & Fault Tolerance): Khả năng giữ vững nguyên tắc "Always Runnable", giúp hệ thống tự phục hồi hoặc hạ cấp dịch vụ an toàn khi môi trường gặp sự cố.
Đóng góp vào hiệu năng vận hành & Trải nghiệm (Latency, Cost & UX): Tác động đến thời gian phản hồi (latency), chi phí tính toán (token/compute cost) và tính minh bạch của câu trả lời đối với người dùng cuối.
3.2.2. Bảng phân cấp và đánh giá mức độ tham gia của các thành phần
Dựa trên 4 chiều tiêu chí trên, 12 thành phần kỹ thuật của hệ thống được phân thành 4 nhóm cấp độ tham gia vào kiến trúc:
Cấp độ phân cấp
Thành phần kỹ thuật
Mức độ tham gia
Tác động chính đến kiến trúc hệ thống
Khả năng thay thế / Dự phòng
 
CẤP 1: CỐT LÕI KIẾN TRÚC
(Architectural Core)
Semantic Parser & Centralized Router
Rất cao (9.8/10)
Bộ não phân loại ý định, bóc tách thực thể và điều phối 4 luồng xử lý chuyên biệt; quyết định trực tiếp bản sắc kiến trúc lai.
Có Regex Fallback dự phòng; bắt buộc phải có Router.
Ingestion Gateway (MarkItDown & Dual-Path)
Rất cao (9.6/10)
Chuẩn hóa tài liệu đa định dạng, bảo toàn bảng biểu và phân tách nguồn dữ liệu thành 2 nhánh văn bản & CSDL quan hệ.
Là nền móng của toàn bộ hệ thống; không thể thiếu.
CẤP 2: NỀN TẢNG CHẤT LƯỢNG
(Quality Enablers)
Metadata Hard Pre-filter
Cao (9.4/10)
Chốt chặn loại trừ tài liệu sai khóa học/hết hiệu lực trước khi tìm kiếm; triệt tiêu hoàn toàn rủi ro trôi niên khóa.
Không thể thay thế trong bài toán phụ thuộc thời gian học vụ.
Structured Lookup Engine
Cao (9.3/10)
Đảm bảo tính toán và tra cứu số liệu học phí/tín chỉ đạt độ chính xác 100% (Zero Hallucination); độ trễ dưới 5ms.
Dự phòng bằng RAG văn bản (nhưng chấp nhận rủi ro ảo giác).
Hybrid Retrieval (BM25Plus + FAISS + RRF)
Cao (9.2/10)
Kết hợp tối ưu giữa tìm kiếm từ khóa chính xác và tương đồng ngữ nghĩa véc-tơ sâu; tối đa hóa độ phủ (Recall@K).
Có cơ chế fallback BM25-only khi chưa nạp FAISS.
CẤP 3: TINH CHỈNH & BẢO VỆ
(Refiners & Guardrails)
Context-Aware Query Rewriter
Trung bình - Cao (8.8/10)
Khôi phục thực thể bị ẩn trong hội thoại đa lượt; cô lập bài toán ngữ cảnh khỏi prompt của LLM sinh câu trả lời.
Dùng câu hỏi gốc (nếu chỉ hỗ trợ câu hỏi đơn lẻ).
Cross-Encoder Reranker
Trung bình - Cao (8.7/10)
Chấm điểm tương tác chéo sâu, cô đọng Top-50 xuống Top-5 tài liệu tinh túy nhất; cải thiện mạnh mẽ MRR và Precision.
Bỏ qua để dùng trực tiếp kết quả RRF (khi cần giảm độ trễ).
Citation Enforcer & Guardrails
Trung bình - Cao (8.6/10)
Ràng buộc trích dẫn pháp lý minh bạch; phát hiện số lạ và từ chối an toàn câu hỏi ngoài miền (OOD).
Prompt ràng buộc của LLM.
CẤP 4: GIAO TIẾP & GIÁM SÁT
(Interface & Observability)
Structured Logging (JSONL)
Trung bình (8.2/10)
Ghi nhận đầy đủ 7 trường trạng thái của từng lượt hỏi đáp; phục vụ đắc lực cho phân tích lỗi và nghiên cứu Ablation.
File log thông thường.
FastAPI & Streamlit UI
Trung bình (8.0/10)
Cung cấp giao diện tương tác người dùng và chuẩn hóa cổng kết nối dịch vụ RESTful theo chuẩn OpenAPI.
CLI / Web UI khác.

3.2.3. Đánh giá chuyên sâu theo 4 nhóm phân cấp kiến trúc
1. Nhóm Cốt lõi kiến trúc (Semantic Parser, Router, Ingestion Dual-Path): Đây là nhóm thành phần định hình nên diện mạo của hệ thống FPTUniQA, tạo ra sự khác biệt bản chất so với các kiến trúc Naive RAG phổ biến trên thị trường. Nếu thiếu Ingestion Gateway và Dual-Path, hệ thống sẽ phải đối mặt với dữ liệu "rác", bảng biểu học phí bị xé vụn thành chuỗi văn bản vô nghĩa, khiến mọi nỗ lực cải tiến thuật toán tìm kiếm phía sau trở nên vô dụng (nguyên lý "Garbage In, Garbage Out"). Nếu thiếu Semantic Parser & Router, hệ thống sẽ thoái hóa thành một RAG đường ống đơn nhất (Single-Pipeline RAG) — mọi câu hỏi bất kể tính chất đều bị ném chung vào một bộ vector search và prompt sinh câu trả lời, dẫn đến việc không thể kiểm soát được ảo giác số học và chi phí gọi mô hình.
2. Nhóm Nền tảng chất lượng (Metadata Pre-filter, Structured Lookup, Hybrid RRF): Nhóm thành phần này trực tiếp quyết định độ chính xác thực nghiệm của từng câu trả lời. Metadata Pre-filter đóng vai trò như một bộ lọc không gian: thay vì tìm kiếm trên toàn bộ 3,931 chunks của trường, bộ lọc co hẹp không gian tìm kiếm chỉ còn vài trăm chunks thuộc đúng khóa học của sinh viên. Structured Lookup Engine mang lại sự an tâm tuyệt đối cho các thông tin nhạy cảm về tài chính (học phí, học bổng). Hybrid RRF tạo nên một tấm lưới kép: BM25 bắt chặt các định danh cứng, trong khi FAISS bắt các diễn đạt mềm dẻo, dung hòa hai kênh một cách thanh lịch mà không đòi hỏi phải chuẩn hóa thang điểm phức tạp.
3. Nhóm Tinh chỉnh & Bảo vệ (Context Rewriter, Reranker, Citation & Guardrails): Nhóm thành phần này nâng tầm trải nghiệm người dùng từ mức "hệ thống tìm kiếm thông tin" lên mức "trợ lý học vụ thông minh, chuẩn mực". Context Rewriter giải phóng người dùng khỏi việc phải gõ lại toàn bộ câu hỏi dài dòng ở mỗi lượt chat. Cross-Encoder Reranker đóng vai trò là "chiếc kính lúp" tinh vi: bù đắp cho sự tính toán thô sơ của Bi-Encoder ở bước trước, đẩy các đoạn văn bản chứa câu trả lời trực tiếp lên vị trí Top 1–3, giúp LLM không bị nhiễu ngữ cảnh. Citation Enforcer và Guardrails tạo nên tính trung thực và minh bạch học thuật.
4. Nhóm Giao tiếp & Giám sát (FastAPI, Streamlit, JSONL Logger): Tuy nằm ở lớp ngoài cùng của hệ thống, nhóm này đảm bảo tính khả dụng công nghiệp và khả năng thẩm định khoa học. Cấu trúc JSONL Logger 7 trường dữ liệu là công cụ không thể thiếu để nhóm phát triển thực hiện thành công ma trận Ablation Study 6 cấu hình (từ A1 đến A6) và truy vết chính xác nguồn gốc sai sót.
3.2.4. Phân tích khả năng chịu lỗi và tính bền vững hệ thống (Fault-Tolerance & Resilience)
Một kiến trúc tốt không chỉ hoạt động tốt trong điều kiện lý tưởng, mà phải thể hiện được độ bền vững cao khi các thành phần bên trong gặp sự cố. FPTUniQA thể hiện xuất sắc nguyên tắc kiến trúc "Fallback Protection" và "Always Runnable" thông qua các cơ chế chịu lỗi phân tầng:
Cơ chế Fallback tại tầng Parser: Khi Semantic Parser (dùng LLM) bị nghẽn mạng hoặc quá tải, Regex Fallback lập tức tiếp quản nhiệm vụ bóc tách intent và slots. Router tiếp nhận kết quả từ Regex Fallback mà không nhận thấy bất kỳ sự khác biệt nào về giao diện dữ liệu nhờ chuẩn Contract 3.
Cơ chế Fallback tại tầng Retrieval: Khi máy chủ bị hạn chế tài nguyên (chưa nạp được chỉ mục FAISS hoặc không có GPU), hệ thống tự động suy thoái mềm sang chế độ BM25-only Retrieval. Mặc dù độ phủ ngữ nghĩa có thể giảm nhẹ, hệ thống vẫn duy trì khả năng trả lời câu hỏi dựa trên từ khóa thay vì bị sập hoàn toàn (fail-stop).
Cơ chế Fallback tại tầng Reranker: Nếu mô hình Cross-Encoder gặp lỗi bộ nhớ (OOM) hoặc vượt ngưỡng thời gian quy định (timeout), hệ thống tự động sử dụng trực tiếp Top-5 ứng viên từ thuật toán RRF để cấp cho LLM, bảo đảm độ trễ phản hồi không bị kéo dài bất thường.
3.3. Thành phần quyết định chất lượng kiến trúc hệ thống
3.3.1. Nhận định cốt lõi: Cặp thành phần quyết định chất lượng kiến trúc
Trong các cuộc tranh luận về thiết kế hệ thống RAG, người ta thường dễ rơi vào định kiến rằng: "Mô hình ngôn ngữ lớn (LLM) nào được chọn?" hoặc "Mô hình Embedding nào tân tiến nhất?" sẽ quyết định sự thành bại của toàn bộ hệ thống.
Tuy nhiên, đối với bài toán hỏi đáp quy chế học vụ đại học của FPTUniQA, phân tích kiến trúc hệ thống chỉ ra rằng:
Thành phần mang tính QUYẾT ĐỊNH CHẤT LƯỢNG của toàn bộ kiến trúc này KHÔNG NẰM Ở TẦNG SINH (LLM GENERATOR) HAY TẦNG VÉC-TƠ (EMBEDDING), mà được định đoạt bởi sự phối hợp chặt chẽ của CẶP ĐÔI KIẾN TRÚC: TẦNG PHÂN TÍCH NGỮ NGHĨA & ĐỊNH TUYẾN Ý ĐỊNH (SEMANTIC PARSER & CENTRALIZED ROUTER) và BỘ LỌC CỨNG SIÊU DỮ LIỆU (METADATA HARD PRE-FILTER).
Trong mối quan hệ cộng hưởng này:
Semantic Parser & Centralized Router đóng vai trò là "BỘ NÃO ĐIỀU PHỐI QUYẾT ĐỊNH" (The Architectural Decider) — quyết định câu hỏi được giải quyết bằng bản thể luận nào (Xác định hay Xác suất).
Metadata Hard Pre-filter đóng vai trò là "LÁ CHẮN NIÊN KHÓA QUYẾT ĐỊNH TÍNH ĐÚNG ĐẮN PHÁP LÝ" (The Temporal/Cohort Correctness Gate) — quyết định ngữ cảnh có hợp lệ về mặt thời gian và đối tượng áp dụng hay không.
3.3.2. Vì sao LLM Generator và Vector Embedding không phải yếu tố quyết định chất lượng?
Để làm rõ nhận định trên, cần phân tích giới hạn cố hữu của LLM Generator và Vector Embedding khi đứng đơn lẻ trong miền học vụ:
1. LLM Generator chỉ là một "thành phần hàng hóa phổ thông" (Commodity Component): Bản chất của LLM trong kiến trúc RAG là một bộ máy đọc hiểu ngữ cảnh và diễn đạt ngôn ngữ tự nhiên (Context Reader & Synthesizer). Nếu Tầng Retrieval cung cấp ngữ cảnh sai (ví dụ kéo nhầm quy chế của năm 2021 cho sinh viên khóa 2026), hoặc ngữ cảnh chứa bảng biểu bị vỡ cấu trúc, thì dù có sử dụng mô hình LLM mạnh nhất hiện nay (như GPT-4o hay Claude 3.5 Sonnet), mô hình vẫn bắt buộc phải tạo ra một câu trả lời sai lệch nhưng được diễn đạt rất trôi chảy, thuyết phục (ảo giác ngữ cảnh), hoặc từ chối trả lời vì thông tin mâu thuẫn. Ngược lại, nếu ngữ cảnh được cung cấp chính xác 100% đến từng điều khoản và số liệu, ngay cả một mô hình ngôn ngữ nhỏ cục bộ (như LLaMA-7B hay mô hình gọn nhẹ Gemini-1.5-Flash) cũng có thể sinh ra câu trả lời xuất sắc và trích dẫn chuẩn xác. Do đó, LLM không thể cứu vãn một ngữ cảnh sai, nhưng một ngữ cảnh đúng có thể biến mọi LLM thành chuyên viên tư vấn chuẩn mực.
2. Vector Embedding thất bại trước tính kế thừa của văn bản pháp quy: Các mô hình nhúng véc-tơ ngữ nghĩa (như Multilingual-E5, BGE-M3) được huấn luyện để đưa các đoạn văn có ý nghĩa tương đồng lại gần nhau trong không gian véc-tơ nhiều chiều. Nhưng trong văn bản quy chế đại học, một quy định năm 2021 và một quy định năm 2026 về cùng chủ đề "Điều kiện chuyển ngành" thường có tới 80–90% từ ngữ và cấu trúc câu giống hệt nhau. Khoảng cách véc-tơ giữa câu hỏi của sinh viên với văn bản cũ và văn bản mới là tương đương nhau. Thậm chí văn bản cũ có thể có điểm cosine similarity cao hơn văn bản mới chỉ vì độ dài hoặc tần suất từ ngữ trùng khớp ngẫu nhiên. Nếu chỉ dựa vào Vector Embedding, hệ thống hoàn toàn bất lực trong việc chọn ra đúng văn bản đang có hiệu lực.
3.3.3. Luận giải chuyên sâu: Bộ đôi Semantic Parser & Centralized Router — Trục điều phối chất lượng
Semantic Parser và Centralized Router là thành phần quyết định chất lượng kiến trúc vì những lý do then chốt sau:
1. Phá vỡ giới hạn của kiến trúc đường ống đơn nhất (Breaking the Single-Pipeline Paradigm): Mọi hệ thống RAG thất bại trong bài toán học vụ đều do áp dụng một đường ống duy nhất cho mọi dạng thông tin. Kiến trúc FPTUniQA nhận thức sâu sắc rằng dữ liệu học vụ bao gồm hai thế giới bản thể học hoàn toàn khác nhau: Thế giới dữ liệu định lượng (Biểu phí, định mức tín chỉ, điểm sàn) đòi hỏi độ chính xác tuyệt đối 100%, và Thế giới dữ liệu chính sách mở (Quy trình khiếu nại, tiêu chuẩn học bổng, điều kiện tốt nghiệp) đòi hỏi năng lực tìm kiếm ngữ nghĩa linh hoạt. Semantic Parser & Router chính là thành phần duy nhất trong hệ thống có năng lực phân loại bản thể học này: bóc tách chính xác intent và các slots để điều hướng câu hỏi số liệu sang đường ống tra cứu CSDL xác định (StructuredRoute), và điều hướng câu hỏi chính sách sang đường ống tìm kiếm lai (HybridRAGRoute). Quyết định phân luồng này triệt tiêu tận gốc 100% nguy cơ ảo giác số học — điều mà không một kỹ thuật prompt engineering nào có thể đảm bảo được.
2. Chuẩn hóa giao diện dữ liệu qua Contract 3: Semantic Parser chuẩn hóa toàn bộ sự biến thiên phức tạp của ngôn ngữ tự nhiên thành một cấu trúc ParsedQuery tường minh. Nhờ có cấu trúc này, các tầng phía sau không phải phỏng đoán ý định người dùng. Đặc biệt, việc bóc tách thành công các slot trọng yếu (cohort, campus, academic_year) tạo tiền đề tiên quyết cho Bộ lọc siêu dữ liệu hoạt động.
3. Đảm bảo tính sẵn sàng cao thông qua Fallback Protection: Nếu Semantic Parser bị sập mà không có cơ chế kiến trúc tương ứng, toàn bộ hệ thống sẽ ngừng hoạt động. Nhưng nhờ kiến trúc hội tụ về Router duy nhất với sự hỗ trợ của Regex Fallback, chất lượng dịch vụ của FPTUniQA luôn được duy trì ổn định, minh chứng cho một thiết kế kiến trúc trưởng thành và đáng tin cậy.
3.3.4. Luận giải chuyên sâu: Metadata Hard Pre-filter — Chốt chặn bảo toàn tính đúng đắn theo khóa học
Nếu Semantic Parser & Router đóng vai trò phân luồng giải pháp, thì Metadata Hard Pre-filter chính là thành phần quyết định tính đúng đắn pháp lý của nội dung được truy xuất:
1. Giải quyết triệt để bài toán phụ thuộc khóa học (Cohort Dependency): Tại Trường Đại học FPT cũng như các trường đại học đào tạo theo tín chỉ, quy định học phí và lộ trình đào tạo được ban hành theo từng khóa tuyển sinh (ví dụ: K20, K21, K22). Sinh viên nhập học năm nào sẽ áp dụng biểu phí và khung quy chế của khóa đó trong suốt toàn bộ khóa học. Khi người dùng hỏi: "Học phí kỳ chuyên ngành ngành AI là bao nhiêu?", nếu hệ thống không biết sinh viên thuộc khóa nào hoặc không áp dụng bộ lọc khóa học, hệ thống sẽ kéo về biểu phí của bất kỳ khóa nào mà nó tìm thấy đầu tiên. Metadata Hard Pre-filter sử dụng slot cohort (được trích xuất từ Semantic Parser hoặc từ ngữ cảnh hội thoại) để thiết lập một bức tường lửa cách ly: toàn bộ văn bản của các khóa khác bị loại bỏ ngay lập tức trước khi BM25 và FAISS tính điểm.
2. Tối ưu hóa không gian tìm kiếm và chi phí tính toán: Việc lọc cứng trước khi tìm kiếm (Pre-filtering) giảm kích thước không gian tìm kiếm từ 3,931 chunks xuống chỉ còn một tập nhỏ liên quan trực tiếp. Điều này mang lại lợi ích kép về mặt kiến trúc: Tăng mạnh độ chính xác (Precision) bằng cách triệt tiêu hoàn toàn các tài liệu gây nhiễu tiềm tàng, đồng thời giảm đáng kể độ trễ truy xuất do chỉ mục BM25 và FAISS chỉ phải duyệt qua tập dữ liệu tinh gọn.
3.3.5. Sự cộng hưởng kiến trúc (Architectural Synergy) và kết luận
Chất lượng vượt trội của hệ thống FPTUniQA không đến từ một thuật toán đơn lẻ, mà đến từ sự cộng hưởng kiến trúc (Architectural Synergy) hoàn hảo giữa các thành phần then chốt:
[ Câu hỏi người dùng ]
         │
         ▼
[ Context Rewriter ] ──────────▶ Khôi phục thực thể ẩn trong hội thoại đa lượt
         │
         ▼
[ Semantic Parser & Router ] ──▶ (QUYẾT ĐỊNH 1) Phân tách thế giới: Định lượng vs. Chính sách mở
         │                                       Bóc tách slot: cohort, campus, program
         ├──────────────────────────────────────┐
         │ (Nhánh Số liệu)                      │ (Nhánh Chính sách)
         ▼                                      ▼
[ Structured Lookup ]                 [ Metadata Pre-filter ] ──▶ (QUYẾT ĐỊNH 2) Khóa chặt niên khóa hợp lệ
(Chính xác 100% số liệu)                        │
                                                ▼
                                      [ Hybrid Retrieval (BM25 + FAISS + RRF) ]
                                                │
                                                ▼
                                      [ Cross-Encoder Reranker ]
                                                │
         ┌──────────────────────────────────────┘
         ▼
[ Ngữ cảnh tinh hoa & chuẩn xác tuyệt đối ]
         │
         ▼
[ LLM Generator & Citation Enforcer ] ─▶ Diễn giải ngôn ngữ tự nhiên & Trích dẫn minh bạch


Tóm lại, trong kiến trúc FPTUniQA:
Semantic Parser & Centralized Router quyết định ĐI ĐÚNG ĐƯỜNG (chọn đúng phương pháp giải quyết cho từng loại tri thức).
Metadata Hard Pre-filter quyết định LẤY ĐÚNG ĐÍCH (chọn đúng văn bản hợp lệ theo niên khóa và thời gian).
Chính hai thành phần này đã định hình nên chất lượng, độ tin cậy và sự thành công của toàn bộ kiến trúc hệ thống, biến FPTUniQA trở thành một giải pháp chuẩn mực cho bài toán hỏi đáp quy chế học vụ đại học tiếng Việt nhận biết ngữ cảnh.


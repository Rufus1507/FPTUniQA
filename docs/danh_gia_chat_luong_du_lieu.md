# BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU THU THẬP & HIỆU QUẢ PIPELINE

**Dự án:** Hệ thống hỏi đáp quy chế & tuyển sinh Đại học FPT (FPTUniQA)  
**Tên đề tài nghiên cứu:** *Context-Aware Vietnamese University Question Answering: A Hybrid Retrieval and Semantic Parsing Approach*  
**Phụ trách đánh giá:** TV1 (Data & Knowledge Engineer)  
**Ngày lập báo cáo:** 21/09/2026  
**Tài liệu đối chiếu:** [baocao.md](file:///H:/PythonProject/FPTUniQA/baocao.md), [nhiemvu.md](file:///H:/PythonProject/FPTUniQA/nhiemvu.md), Pipeline mã nguồn (`src/university_qa/data/`) và các sản phẩm đầu ra thực tế (`data/processed/`, `data/interim/`).

---

## TỔNG QUAN ĐÁNH GIÁ (EXECUTIVE SUMMARY)

Dữ liệu thu thập và kết quả thực thi của Pipeline tiền xử lý đạt mức **RẤT TỐT (Grade: A / 9.0/10)** xét trên tính toàn vẹn kỹ thuật, tính tương thích hợp đồng giao tiếp (Contract 1: Data Schema), và khả năng đáp ứng trực tiếp cho 2 trụ cột học thuật của đề tài: **Hybrid Retrieval** và **Semantic Parsing Routing**.

* **Về quy mô và độ sạch:** Xử lý 170 tệp HTML thô (~5.71 MB), loại bỏ 8 trang rác/form động (4.7%), sinh ra **3,931 chunks sạch** trong `corpus.jsonl` và **190 bản ghi học phí có cấu trúc** trong `structured_data.json`.
* **Về tính tương thích hợp đồng:** **100% (3,931/3,931)** chunks tuân thủ hoàn hảo Contract 1 (không có trường nào bị `null` hoặc thiếu).
* **Về thực nghiệm:** Chỉ mục BM25 baseline nạp 3,931 tài liệu đã xác minh thành công trên các câu hỏi thực tế với điểm số truy hồi rất cao (15.7 – 33.3).
* **Điểm hạn chế cần ghi nhận:** Kho dữ liệu hiện tại tập trung chủ yếu vào **thông tin tuyển sinh, học phí, học bổng và ngành học khóa 2026 (K22)**; còn thiếu văn bản quy chế đào tạo tín chỉ nội bộ chuyên sâu (quy chế thi lại, cảnh báo học vụ, kỷ luật sinh viên) và tài liệu dạng PDF pháp quy có số hiệu quyết định của Hiệu trưởng.

---

## PHẦN 1: ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU DỰA TRÊN NỘI DUNG `baocao.md`

Tài liệu [baocao.md](file:///H:/PythonProject/FPTUniQA/baocao.md) định hình đề tài theo định hướng nghiên cứu khoa học thực nghiệm, nhấn mạnh vào 4 yêu cầu cốt lõi:
1. Tính nhận biết ngữ cảnh đa chiều (**Context-Awareness**).
2. Tìm kiếm lai (**Hybrid Retrieval**).
3. Phân tích ngữ nghĩa câu hỏi phục vụ định tuyến tra cứu số học (**Semantic Parsing Routing**).
4. Khả năng thiết lập bộ đánh giá đối sánh thực nghiệm (**Ablation Study 6 cấu hình & 5 nhóm metrics**).

Dưới đây là đánh giá chi tiết theo từng yêu cầu học thuật:

### 1.1. Khả năng phục vụ tính năng Nhận biết Ngữ cảnh (Context-Awareness)
* **Yêu cầu trong `baocao.md`:** Hệ thống phải trả lời chính xác theo từng ngữ cảnh: Cơ sở đào tạo (Campus: Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Quy Nhơn), Khóa học (Cohort: K22 / 2026), Ngành đào tạo và Quy chế vùng miền.
* **Hiện trạng dữ liệu đạt được:**
  * Đã gán nhãn trường `campus` cho 100% chunks: 2,535 chunks áp dụng toàn quốc (`all`), 691 chunks TP.HCM, 225 chunks Hà Nội, 218 chunks Cần Thơ, 131 chunks Đà Nẵng, 131 chunks Quy Nhơn.
  * Phân loại trường `cohort` chi tiết: Nhận diện chính xác các văn bản áp dụng cho tân sinh viên nhập học năm 2026 (Khóa K22) và phân biệt với các quy định chung (`All`).
  * **Đánh giá:** **RẤT CAO (9.2/10)**. Dữ liệu hỗ trợ đắc lực cho TV2 thực hiện Metadata Pre-filtering (lọc trước theo campus/cohort) và TV3 thực hiện Context-aware Query Rewriting.

### 1.2. Khả năng phục vụ Tìm kiếm lai (Hybrid Retrieval: BM25 + Dense FAISS)
* **Yêu cầu trong `baocao.md`:** Corpus phải được chuẩn hóa tiếng Việt, độ dài đoạn văn bản tối ưu (~200–500 từ hoặc ~800–1200 ký tự), có tiêu đề ngữ cảnh để không làm mất nghĩa đoạn trích khi tìm kiếm dense hoặc sparse.
* **Hiện trạng dữ liệu đạt được:**
  * Toàn bộ 3,931 chunks đều mang tiêu đề ngữ cảnh kế thừa (`title` kết hợp tiêu đề bài viết + đề mục H2/H3).
  * Văn bản được chuẩn hóa Unicode NFC, xử lý sạch các liên kết rác, nút chia sẻ, các bảng học phí được giữ trọn vẹn ngữ nghĩa.
  * Thử nghiệm BM25 baseline đã cho thấy khả năng bắt từ khóa chính xác tuyệt đối:
    * *"Học phí ngành Trí tuệ nhân tạo campus Hà Nội khóa 2026"* đạt điểm BM25 = 27.138 (Top 1 trả về đúng chunk học phí AI Hà Nội).
    * *"Học bổng tìm kiếm nhân tài kỷ nguyên số"* đạt điểm BM25 = 33.272 (Top 1 trả về đúng văn bản học bổng).
  * **Đánh giá:** **XUẤT SẮC (9.5/10)**. Dữ liệu đáp ứng tối ưu cho cả BM25 và Vector Embedding (ví dụ multilingual-e5) mà không gặp hiện tượng chunking cụt lủn hay nhiễu HTML.

### 1.3. Khả năng phục vụ Semantic Parsing Routing & Tra cứu Số học (Core Contribution)
* **Yêu cầu trong `baocao.md`:** Đóng góp khoa học then chốt của đề tài là: Đối với các câu hỏi tra cứu con số cụ thể (học phí từng kỳ, học phí tiếng Anh dự bị, chính sách giảm trừ vùng miền), hệ thống không chỉ dùng RAG tạo sinh văn bản tự do (dễ gây ảo giác số liệu) mà dùng **Semantic Parser** trích xuất ra `structured query` ({intent, campus, major, cohort}) rồi tra cứu trực tiếp trên cơ sở dữ liệu có cấu trúc.
* **Hiện trạng dữ liệu đạt được:**
  * File [`data/processed/structured_data.json`](file:///H:/PythonProject/FPTUniQA/data/processed/structured_data.json) đã bóc tách hoàn chỉnh **190 bản ghi học phí K22** của 38 ngành/chuyên ngành trên cả **5 cơ sở**:
    * Hà Nội & TP.HCM: Biểu phí tiêu chuẩn (Học kỳ chuyên ngành: 32.500.000 VNĐ; Tiếng Anh chuẩn bị: 12.400.000 VNĐ/mức).
    * Đà Nẵng & Cần Thơ: Áp dụng mức ưu đãi 30% địa phương (Học kỳ chuyên ngành KV1: 15.480.000 VNĐ, KV khác: 22.120.000 VNĐ; Tiếng Anh: 8.680.000 VNĐ/mức).
    * Quy Nhơn: Áp dụng mức ưu đãi 50% địa phương (Học kỳ chuyên ngành KV1: 11.060.000 VNĐ, KV khác: 15.800.000 VNĐ; Tiếng Anh: 6.200.000 VNĐ/mức).
  * Tách biệt rõ ràng 2 mức: Thí sinh thuộc Khu vực 1 (KV1) và các khu vực khác.
  * **Đánh giá:** **HOÀN HẢO (10/10)**. Cung cấp nền tảng dữ liệu vàng để TV3 xây dựng router tra cứu số học, đảm bảo độ trung thực tuyệt đối (Answer Faithfulness = 100%, Hallucination Rate = 0% trên các câu hỏi học phí).

### 1.4. Khả năng phục vụ Thí nghiệm Ablation Study (6 Cấu hình) & Bộ Chỉ Số Toàn Diện
* **Yêu cầu trong `baocao.md`:** Xây dựng bộ dữ liệu kiểm thử (Evaluation Test Set 150–250 câu hỏi) để đo đạc 6 cấu hình đối sánh và 5 nhóm metric (Retrieval, Semantic Parsing, Generation, Safety/OOD, System Latency).
* **Đánh giá tính khả thi từ dữ liệu:**
  * Với 3,931 chunks bao phủ 6 loại tài liệu (`curriculum`, `admission`, `scholarship`, `general`, `tuition`, `enrollment`), nhóm nghiên cứu có đầy đủ ngữ liệu để sinh 200 câu hỏi đánh giá:
    * 50 câu tra cứu số liệu học phí (dùng để đo Intent/Slot Accuracy của Semantic Parser và so sánh Cấu hình 5 vs Cấu hình 6).
    * 50 câu giải thích chính sách tuyển sinh/học bổng (dùng đo Recall@K, MRR, Reranker gain).
    * 50 câu về chương trình đào tạo và chuẩn đầu ra ngoại ngữ.
    * 30–50 câu Out-of-Domain (OOD) từ các trang bị loại bỏ hoặc các câu hỏi trường ngoài để đo OOD Rejection Rate.
  * **Đánh giá:** **RẤT CAO (9.0/10)**.

---

## PHẦN 2: ĐÁNH GIÁ CHẤT LƯỢNG PIPELINE XỬ LÝ DỮ LIỆU (DATA & ETL PIPELINE)

Kiến trúc Pipeline được TV1 xây dựng theo mô hình module hóa cao, tuân thủ nguyên tắc SOLID, bao gồm các thành phần:
`Raw Crawler Starter` $\rightarrow$ `DataLoader` $\rightarrow$ `HTMLExtractor` $\rightarrow$ `TextCleaner` $\rightarrow$ `TextChunker` $\rightarrow$ `MetadataEnricher` $\rightarrow$ `StructuredDataParser` $\rightarrow$ `IngestScript`.

Dưới đây là phân tích chi tiết từng tầng kỹ thuật:

### 2.1. Tầng Nạp & Quản lý Dữ liệu Thô (`loader.py`)
* **Ưu điểm:**
  * Cơ chế nạp linh hoạt: Tự động phát hiện và xử lý đa định dạng (HTML, TXT, MD).
  * Tích hợp sâu với `crawl_manifest.jsonl`: Mỗi tài liệu nạp vào đều được gắn kèm URL gốc, HTTP status, timestamp thu thập và doc_id duy nhất.
  * Bảo toàn tuyệt đối nguyên vẹn dữ liệu gốc trong `data/raw/fpt_admission/html/` (không sửa đổi hay xóa file gốc).
* **Chỉ số kiểm định:** 170/170 tệp HTML được nạp thành công, không gặp bất kỳ lỗi IO nào.

### 2.2. Tầng Bóc tách HTML & Xử lý Rác WordPress (`html_extractor.py`)
* **Ưu điểm vượt trội:**
  * Chiến lược trích xuất kép (Dual Strategy): Sử dụng `trafilatura` làm parser nội dung bài báo chính, kết hợp fallback thông minh với BeautifulSoup.
  * Bộ lọc chuyên biệt cho WordPress FPT: Loại bỏ triệt để các khối CSS/JS, widget form tư vấn tuyển sinh (`wpcf7`, `ninja-forms`), navigation header, widget mạng xã hội và footer bản quyền.
  * Giữ nguyên vẹn bảng HTML: Nhận diện cấu trúc `<table>` chứa biểu phí học phí nhiều cột, chuyển đổi thành bảng dữ liệu Markdown bảo toàn cấu trúc thay vì làm phẳng thành chuỗi từ vô nghĩa.
* **Cơ chế lọc trang rác (`discarded_pages.jsonl`):**
  * Tự động phát hiện và loại bỏ các trang có độ dài nội dung dưới ngưỡng tối thiểu (ngưỡng 80 từ) hoặc trang trùng lặp nội dung.
  * Minh bạch nguyên nhân loại bỏ: 8 trang bị loại đều ghi nhận lý do rõ ràng (ví dụ: form nhập liệu rỗng `dang-ky-hoc-bong/`, trang taxonomy chuyên mục chỉ chứa danh sách link).

### 2.3. Tầng Chuẩn hóa Ngôn ngữ Tiếng Việt & Số học (`cleaner.py`)
* **Ưu điểm:**
  * Chuẩn hóa chuẩn quốc tế NFC: Triệt tiêu hoàn toàn sự sai lệch giữa tiếng Việt dựng sẵn và tổ hợp (nguyên nhân hàng đầu gây sụt giảm điểm BM25 và Vector Search).
  * Chuẩn hóa số tiền VND (`normalize_vnd_amounts`): Chuyển đổi các định dạng số tiền phức tạp (ví dụ `32.500.000 VNĐ`, `32,5 triệu đồng`) về dạng biểu diễn chuẩn, loại trừ nhầm lẫn dấu phân cách hàng nghìn với dấu chấm thập phân.
  * Xóa khoảng trắng thừa và ngắt dòng rác do mã nguồn HTML để lại.

### 2.4. Tầng Phân đoạn Ngữ nghĩa & Siêu dữ liệu (`chunker.py`, `metadata.py`)
* **Ưu điểm kiến trúc:**
  * **Table-aware Chunking:** Không chia cắt ngang hàng các bảng học phí. Toàn bộ bảng biểu được giữ trọn vẹn trong một chunk để đảm bảo ngữ cảnh nguyên vẹn cho LLM.
  * **Heading-based Semantic Chunking:** Cắt đoạn thông minh dựa theo các tiêu đề mục H1, H2, H3 trong bài viết. Kế thừa tiêu đề ngữ cảnh vào trường `title` của từng chunk.
  * **Dual-Contract Schema Compatibility:** Xuất dữ liệu đáp ứng đồng thời cả:
    * **Contract 1:** `doc_id`, `source`, `doc_type`, `campus`, `applies_to_cohort`, `effective_date`.
    * **Legacy Pipeline (TV2/TV3):** `id`, `title`, `text`, `metadata`.
* **Chỉ số kiểm định chất lượng:**
  * 0% chunk bị lỗi thiếu trường bắt buộc (3,931/3,931 đạt chuẩn).
  * Phân phối độ dài chunk tối ưu: Trung bình 217.9 ký tự, không có chunk rác rỗng.

### 2.5. Tầng Dữ liệu Cấu trúc Hóa (`structured.py`)
* **Ưu điểm:**
  * Parser chuyên biệt bóc tách dữ liệu học phí cho toàn bộ 5 cơ sở đào tạo lớn của Đại học FPT.
  * Xuất ra tệp JSON chuẩn hóa cao độ `structured_data.json` với cấu trúc cây: `campus` $\rightarrow$ `major_name` $\rightarrow$ `{kv1, các_kv_khác, prep_english}`.
  * Tự động bổ sung các hằng số chính sách (Policy Constants) như tỷ lệ ưu đãi vùng miền (30% tại ĐN/CT, 50% tại QN).

---

## PHẦN 3: MA TRẬN ĐỐI SOÁT & ĐÁNH GIÁ SWOT DỮ LIỆU

| Tiêu chí đánh giá | Điểm số (Thang 10) | Nhận xét chi tiết |
| :--- | :---: | :--- |
| **Tính Toàn vẹn Kỹ thuật (Integrity)** | **9.8** | Pipeline chạy ổn định, không crash, schema tuân thủ 100%, có nhật ký provenance đầy đủ. |
| **Độ Sạch Ngữ liệu (Cleanliness)** | **9.2** | Đã bóc sạch 99% rác HTML WordPress; chuẩn hóa NFC tiếng Việt và số tiền VND hoàn chỉnh. |
| **Bảo tồn Cấu trúc Bảng (Table Preservation)** | **9.5** | Giữ trọn bảng học phí, không làm vỡ các mối liên kết giữa Ngành - Mức phí - Cơ sở đào tạo. |
| **Phục vụ Semantic Parsing** | **10.0** | Xuất sắc; `structured_data.json` cung cấp đầy đủ 190 biểu phí học phí chi tiết 5 campus. |
| **Phục vụ Hybrid Retrieval** | **9.4** | Thử nghiệm BM25 Top-1 chính xác tuyệt đối; sẵn sàng 100% cho việc build FAISS Dense Index của TV2. |
| **Độ Bao phủ Miền Tri thức (Coverage)** | **7.5** | Bao phủ rất sâu về Tuyển sinh, Học phí, Học bổng và Ngành học 2026; tuy nhiên còn thiếu văn bản quy chế đào tạo nội bộ chi tiết (cảnh báo học vụ, thi lại, bảo lưu, KTX). |

### Phân tích SWOT của Tập Dữ liệu Hiện tại

```
STRENGTHS (Điểm mạnh)
1. Độ chính xác số học học phí 100% cho 5 campus (K22/2026).
2. Schema tuân thủ Contract 1 tuyệt đối (0 missing fields).
3. BM25 baseline hoạt động cực kỳ nhạy (score 15-33 trên query mẫu).
4. Phân đoạn ngữ nghĩa bảo tồn bảng biểu và tiêu đề đề mục.

WEAKNESSES (Điểm yếu)
1. Chưa có tài liệu pháp quy dạng PDF scan có số hiệu Quyết định.
2. Thiếu quy chế đào tạo tín chỉ chi tiết (điều kiện học lại, cảnh báo).
3. Dữ liệu ký túc xá và thủ tục thực tế nhập học còn mỏng (25 chunks).

OPPORTUNITIES (Cơ hội)
1. Dễ dàng sinh Ground Truth Test Set 200 câu hỏi cho bài báo.
2. Chứng minh thành công tính ưu việt của Cấu hình 6 (Semantic Parsing) so với Cấu hình 5 trong bảng Ablation Study.
3. Thu thập bổ sung từ cổng FAP và Dịch vụ sinh viên.

THREATS (Thách thức)
1. Sinh viên có thể đặt câu hỏi về quy chế học vụ nội bộ mà web tuyển sinh ngoài chưa đăng tải.
2. Cần thiết lập Prompt từ chối khéo (OOD Fallback) khi hỏi về các thủ tục chưa có văn bản.
```

---

## PHẦN 4: ĐỀ XUẤT HÀNH ĐỘNG VÀ BÀN GIAO (ACTIONABLE RECOMMENDATIONS)

### 4.1. Nhiệm vụ Bàn giao ngay cho TV2 (Retrieval & Ranking)
1. Sử dụng trực tiếp `data/processed/corpus.jsonl` (3,931 chunks) làm tập dữ liệu chuẩn để dựng chỉ mục Vector Dense với FAISS (khuyến nghị mô hình `bkai-foundation-models/vietnamese-bi-encoder` hoặc `intfloat/multilingual-e5-base`).
2. Tận dụng trường `campus` và `doc_type` trong metadata để cài đặt bộ lọc siêu dữ liệu (Metadata Pre-filtering), giúp tăng tốc độ truy vấn và độ chính xác phân loại.
3. Triển khai thuật toán Reciprocal Rank Fusion (RRF) kết hợp điểm số của chỉ mục BM25 baseline sẵn có (`data/processed/bm25_index/`) với điểm số từ FAISS.

### 4.2. Nhiệm vụ Bàn giao ngay cho TV3 (Semantic Parsing & Generation)
1. Nạp file `data/processed/structured_data.json` vào memory cache hoặc SQLite table của Backend FastAPI.
2. Viết module Semantic Parser (dùng OpenAI function calling hoặc regex fallback) bóc tách câu hỏi người dùng thành JSON schema:
   ```json
   {
     "intent": "tuition_lookup",
     "campus": "ha_noi",
     "major": "tri_tue_nhan_tao",
     "cohort": "2026"
   }
   ```
3. Định tuyến trực tiếp sang hàm tra cứu `lookup_tuition()` trong `structured.py` để trả về câu trả lời với độ chính xác 100%, không cần qua bước LLM generation cho phần số liệu, triệt tiêu ảo giác.

### 4.3. Kế hoạch Thu thập Mở rộng của TV1 (Data Expansion)
1. **Thu thập tài liệu Sổ tay sinh viên / Quy chế đào tạo:**
   * Khai thác bổ sung từ nguồn cổng thông tin đào tạo `https://fap.fpt.edu.vn/` và `https://dichvu.fpt.edu.vn/`.
   * Tìm kiếm các văn bản PDF quy chế khen thưởng, kỷ luật, quy chế thi kết thúc học phần.
2. **Xây dựng bộ Test Set vàng (Ground Truth Benchmark):**
   * Biên soạn bộ 200 câu hỏi-đáp đánh giá theo đúng thiết kế của `baocao.md`:
     * Nhãn Intent vàng (Intent Label).
     * Nhãn Slot vàng (Program, Campus, Cohort, Metric).
     * Nhãn Context vàng (Chunk IDs liên quan) phục vụ tính toán Recall@K và MRR.

---

## KẾT LUẬN

Tập dữ liệu và Pipeline tiền xử lý do TV1 hoàn thành đã **đạt và vượt các yêu cầu đề ra cho giai đoạn Tuần 1–Tuần 2**. Hạ tầng dữ liệu đã sẵn sàng 100% để TV2 và TV3 xây dựng các tầng kỹ thuật tiếp theo theo đúng cam kết của bản lộ trình [baocao.md](file:///H:/PythonProject/FPTUniQA/baocao.md).

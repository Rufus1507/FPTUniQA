# BÁO CÁO KIỂM KÊ DỮ LIỆU & BÀN GIAO TIỀN XỬ LÝ (TV1 DATA AUDIT & HANDOFF REPORT)

**Dự án:** Hệ thống hỏi đáp quy chế & thông tin tuyển sinh Đại học FPT (FPTUniQA)  
**Phụ trách:** TV1 (Data & Knowledge Engineer)  
**Ngày thực hiện:** 21/09/2026  
**Trạng thái:** Đã hoàn thành toàn bộ Pipeline ETL, Chuẩn hóa, Chunking và Lập chỉ mục sơ bộ  

---

## 1. TỔNG QUAN VÀ MỤC TIÊU CÔNG VIỆC

Tuân thủ nghiêm ngặt chỉ dẫn tại `nhiemvu.md`, nguyên tắc **Contract 1: Data Schema**, cùng tài liệu kiến trúc hệ thống, TV1 đã hoàn thành việc tiếp nhận gói dữ liệu thô `fptuniqa_raw_data_20260921.zip`, bóc tách sạch, chuẩn hóa văn bản tiếng Việt, phân loại chủ đề/cơ sở/khóa học, chunking ngữ nghĩa bảo toàn cấu trúc bảng, và trích xuất dữ liệu học phí có cấu trúc phục vụ tra cứu số học (Semantic Parsing Routing).

Dữ liệu thô gốc được bảo toàn nguyên vẹn 100% tại `data/raw/fpt_admission/html/` và `data/raw/crawl_manifest.jsonl`.

---

## 2. KẾT QUẢ KIỂM KÊ DỮ LIỆU THÔ (RAW DATA AUDIT)

* **Nguồn thu thập:** Website chính thức của Trường Đại học FPT (`daihoc.fpt.edu.vn`).
* **Tổng số bản ghi trong `crawl_manifest.jsonl`:** 226 bản ghi.
  * **HTTP 200 (Thành công):** 219 bản ghi.
  * **HTTP 404 (Không tìm thấy / Link hỏng):** 7 bản ghi.
  * **Seed URL ban đầu:** 13/13 thành công (100%).
* **Tệp HTML thô thực tế có trong gói:** 170 tệp HTML (dung lượng trung bình ~150–350 KB/tệp).
* **Định dạng:** 100% HTML (chưa có tài liệu PDF pháp quy nội bộ trong đợt crawl này).

---

## 3. QUY TRÌNH TIỀN XỬ LÝ VÀ CHUẨN HÓA (ETL PIPELINE)

Hệ thống module tiền xử lý do TV1 phát triển bao gồm:

1. **`html_extractor.py`**:
   * Sử dụng `trafilatura` làm core extraction engine kết hợp BeautifulSoup fallback.
   * Loại bỏ triệt để các thành phần rác: header, navigation menu, footer WordPress, widget đăng ký form, social share buttons.
   * Xử lý đặc thù các bảng học phí HTML phức tạp, giữ cấu trúc `<table>` hoặc chuyển đổi sang định dạng bảng Markdown để không làm vỡ dữ liệu số.
2. **`cleaner.py`**:
   * Chuẩn hóa Unicode theo chuẩn NFC (tránh lỗi ký tự tiếng Việt dạng tổ hợp).
   * Chuẩn hóa khoảng trắng, dấu ngắt dòng thừa.
   * Chuẩn hóa định dạng tiền tệ VND: chuyển các chuỗi số như `32.500.000 VNĐ` thành biểu diễn chuẩn hóa nhằm loại bỏ sự mơ hồ giữa dấu chấm thập phân và dấu ngăn cách hàng nghìn.
3. **`chunker.py`**:
   * Kết hợp cơ chế phân đoạn theo tiêu đề (H1, H2, H3) và độ dài ngữ nghĩa (semantic window: ~800–1200 ký tự với overlap 150 ký tự).
   * **Đặc biệt:** Cơ chế bảo toàn bảng biểu — không bao giờ chia cắt giữa chừng các hàng trong bảng học phí để đảm bảo tính trọn vẹn khi mô hình RAG hoặc Semantic Parser truy vấn.
   * Tự động kế thừa tiêu đề bài viết và section header vào từng chunk (`title`).
4. **`metadata.py`**:
   * Tự động nhận diện và gán các trường siêu dữ liệu chuẩn:
     * `doc_type`: `admission`, `tuition`, `scholarship`, `curriculum`, `enrollment`, `general`.
     * `campus`: `all`, `ha_noi`, `ho_chi_minh`, `da_nang`, `can_tho`, `quy_nhon`.
     * `cohort`: `K22`, `nhập học năm 2026`, `All`.
     * `effective_date`: Trích xuất ngày ban hành/áp dụng nếu có.
   * Đảm bảo cấu trúc dữ liệu tương thích kép (dual compatibility): hỗ trợ cả Contract 1 (`doc_id`, `source`, `doc_type`, `campus`) và legacy pipeline của TV2/TV3 (`id`, `title`, `text`, `metadata`).
5. **`structured.py`**:
   * Parser chuyên biệt bóc tách toàn bộ bảng học phí K22 của 5 cơ sở đào tạo ra định dạng JSON có cấu trúc (`structured_data.json`).
   * Phân tách rõ ràng giữa biểu phí Khu vực 1 (KV1) và các khu vực khác, học phí tiếng Anh dự bị (Prep English), và chính sách trợ cấp vùng miền (Đà Nẵng/Cần Thơ ưu đãi 30%, Quy Nhơn ưu đãi 50%).

---

## 4. BÁO CÁO CÁC FILE ĐẦU RA VÀ SỐ LIỆU ĐÃ TẠO

| Tệp đầu ra | Vị trí | Số lượng bản ghi / Dung lượng | Mục đích & Mô tả |
| :--- | :--- | :--- | :--- |
| `corpus.jsonl` | `data/processed/corpus.jsonl` | **3,931 chunks** (~4.01 MB) | Corpus văn bản sạch đã đánh chỉ mục đầy đủ metadata, sẵn sàng cho BM25, FAISS và Reranker |
| `structured_data.json` | `data/processed/structured_data.json` | **190 records học phí** (~115 KB) | Bảng tra cứu số học chuẩn xác 100% cho 5 campus (Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Quy Nhơn) |
| `discarded_pages.jsonl` | `data/interim/discarded_pages.jsonl` | **8 trang** (~1.48 KB) | Danh sách các URL/trang thô bị loại bỏ kèm lý do kỹ thuật chi tiết |
| `crawl_manifest.jsonl` | `data/raw/crawl_manifest.jsonl` | **226 bản ghi** (~42.1 KB) | Nhật ký nguồn gốc dữ liệu crawl phục vụ truy vết nguồn gốc (provenance) |
| `bm25_index.pkl` | `data/processed/bm25_index/` | **3,931 tài liệu** | Chỉ mục BM25 Okapi đã được xây dựng và xác minh truy vấn thành công |

---

## 5. BÁO CÁO KIỂM TOÁN CHẤT LƯỢNG (DATA QUALITY & CONTRACT AUDIT)

### 5.1. Tuân thủ hợp đồng dữ liệu (Contract 1 Compliance)
Kiểm tra tự động trên toàn bộ 3,931 chunks trong `corpus.jsonl`:
* `id`: 3,931 / 3,931 hợp lệ (0 missing).
* `title`: 3,931 / 3,931 có tiêu đề rõ ràng (0 missing).
* `text`: 3,931 / 3,931 nội dung sạch, không rỗng (0 missing).
* `doc_id`: 3,931 / 3,931 ánh xạ chính xác file/URL gốc (0 missing).
* `source`: 3,931 / 3,931 chứa URL hoặc đường dẫn gốc (0 missing).
* `doc_type`: 3,931 / 3,931 được phân loại chuẩn (0 missing).
* `campus`: 3,931 / 3,931 được phân bổ cơ sở đào tạo chuẩn (0 missing).

### 5.2. Phân bố theo loại tài liệu (doc_type distribution)
* **Chương trình đào tạo & Ngành học (`curriculum`):** 1,676 chunks (42.6%)
* **Tuyển sinh & Phương thức xét tuyển (`admission`):** 658 chunks (16.7%)
* **Học bổng & Tiêu chí xét học bổng (`scholarship`):** 581 chunks (14.8%)
* **Thông tin chung & Tin tức trường (`general`):** 546 chunks (13.9%)
* **Học phí & Chi phí đào tạo (`tuition`):** 445 chunks (11.3%)
* **Thủ tục nhập học (`enrollment`):** 25 chunks (0.6%)

### 5.3. Phân bố theo cơ sở đào tạo (campus distribution)
* **Chung cho toàn bộ hệ thống (`all`):** 2,535 chunks (64.5%)
* **TP. Hồ Chí Minh (`ho_chi_minh`):** 691 chunks (17.6%)
* **Hà Nội (`ha_noi`):** 225 chunks (5.7%)
* **Cần Thơ (`can_tho`):** 218 chunks (5.5%)
* **Đà Nẵng (`da_nang`):** 131 chunks (3.3%)
* **Quy Nhơn (`quy_nhon`):** 131 chunks (3.3%)

### 5.4. Thống kê độ dài đoạn văn bản (Chunk Size Metrics)
* Độ dài ký tự: Trung bình = **217.9 ký tự** (Ngắn nhất: 2 ký tự đối với các tiêu đề mục con; Dài nhất: 5,991 ký tự đối với các bảng chi tiết biểu phí).
* Độ dài từ (word count): Trung bình = **46.8 từ** (Dài nhất: 1,299 từ).

---

## 6. DANH SÁCH CÁC TRANG BỊ LOẠI BỎ (DISCARDED PAGES) VÀ LÝ DO

Trong 170 trang HTML thô, có **8 trang** bị loại khỏi corpus chính thức:

| URL nguồn | Số từ | Lý do kỹ thuật loại bỏ |
| :--- | :---: | :--- |
| `https://daihoc.fpt.edu.vn/dang-ky-hoc-bong/` | 37 | Trang form nhập liệu đăng ký động, không chứa tri thức chính sách |
| `https://daihoc.fpt.edu.vn/chuyen-muc/hoat-dong-nha-truong/tin-tuc-nganh-quan-tri-kinh-doanh/` | 51 | Trang chuyên mục phân loại (category index/taxonomy listing), chỉ gồm danh sách links |
| `https://daihoc.fpt.edu.vn/chuyen-muc/hoat-dong-nha-truong/tin-tuc-nganh-khoa-hoc-may-tinh/` | 55 | Trang chuyên mục phân loại, không có nội dung bài viết |
| `https://daihoc.fpt.edu.vn/dang-ky-hoc-bong/gioi-thieu-ung-vien` | 72 | Trang form thu thập thông tin người giới thiệu học bổng |
| `https://daihoc.fpt.edu.vn/chuyen-muc/hoat-dong-nha-truong/tin-tuc-nganh-cong-nghe-truyen-thong/` | 56 | Trang chuyên mục phân loại tin tức |
| `https://daihoc.fpt.edu.vn/dang-ky-hoc-bong/nop-ho-so` | 62 | Trang giao diện upload tài liệu đính kèm |
| `https://daihoc.fpt.edu.vn/dang-ky-hoc-bong/` (bản ghi lặp) | 37 | Trùng lặp nội dung với trang form đăng ký |
| `https://daihoc.fpt.edu.vn/chuyen-muc/hoat-dong-nha-truong/tin-tuc-nganh-cong-nghe-thong-tin/` | 60 | Trang chuyên mục tin tức ngành CNTT |

---

## 7. ĐÁNH GIÁ ĐỘ BAO PHỦ DỮ LIỆU (COVERAGE AUDIT)

### 7.1. Các chủ đề đã có dữ liệu đầy đủ và chất lượng cao (Covered)
1. **Quy chế Tuyển sinh năm 2026 (Khóa K22):**
   * Đầy đủ các phương thức tuyển sinh: Xét điểm thi tốt nghiệp THPT, Xét học bạ THPT qua hệ thống SchoolRank/TopSchool, Xét tuyển thẳng, Thí sinh diện tốt nghiệp THPT tại nước ngoài.
   * Điều kiện trúng tuyển theo từng đối tượng cụ thể.
2. **Chính sách Học bổng năm 2026:**
   * Học bổng Tìm kiếm nhân tài kỷ nguyên số 2026 (các mức 100%+ sinh hoạt phí, 100%, 70%, 50%, 30%).
   * Học bổng Tài năng, Học bổng Khuyến học FPT Edu, Học bổng nữ sinh theo học ngành CNTT.
   * Điều kiện nộp hồ sơ, điều kiện duy trì học bổng qua từng học kỳ.
3. **Biểu phí & Học phí K22 toàn diện:**
   * Học phí chuẩn hóa đầy đủ cho 5 cơ sở đào tạo: Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Quy Nhơn.
   * Tách bạch học phí chương trình tiếng Anh dự bị (chuẩn bị tiếng Anh theo 6 mức) và học phí chuyên ngành 9 học kỳ.
   * Chính sách trợ cấp địa phương (học tại Đà Nẵng, Cần Thơ được trợ cấp 30%; học tại Quy Nhơn được trợ cấp 50%).
4. **Chương trình đào tạo và Chuẩn đầu ra:**
   * Chi tiết các khối ngành: Công nghệ thông tin, Quản trị kinh doanh, Công nghệ truyền thông, Ngôn ngữ Anh, Ngôn ngữ Nhật, Ngôn ngữ Hàn, Ngôn ngữ Trung Quốc.
   * Chuẩn đầu ra ngoại ngữ: Bậc 5/6 Khung năng lực ngoại ngữ VN (CEFR C1/B2 tùy ngành), JLPT N2, TopJ, v.v.

### 7.2. Các khoảng trống dữ liệu cần bổ sung (Data Gaps)
1. **Quy chế Đào tạo tín chỉ nội bộ:**
   * Chưa có văn bản pháp quy chi tiết về: Điều kiện cảnh báo học vụ, số lần nợ môn tối đa, quy trình xin bảo lưu kết quả, điều kiện và thủ tục chuyển ngành/chuyển campus, quy định thi lại và học lại.
2. **Ký túc xá và Dịch vụ sinh viên:**
   * Thiếu bảng phí ký túc xá chính thức cho từng campus (Hòa Lạc, Quận 9, An Phú Thịnh, v.v.).
   * Thiếu nội quy lưu trú nội trú KTX.
3. **Thủ tục nhập học thực tế cho tân sinh viên trúng tuyển:**
   * Dữ liệu về nộp hồ sơ gốc, giấy báo trúng tuyển, khám sức khỏe, mua đồng phục/võ phục Vovinam còn ở mức sơ lược (chỉ có 25 chunks `enrollment`).
4. **Quyết định pháp lý chính thức có số hiệu văn bản:**
   * Hiện tại dữ liệu chủ yếu từ các bài viết thông báo/tin tức tuyển sinh trên web; thiếu các file PDF scan Quyết định có chữ ký Hiệu trưởng và số văn bản chính thức (ví dụ: `QĐ số .../QĐ-ĐHFPT`).

---

## 8. ĐỀ XUẤT NGUỒN VÀ URL CẦN THU THẬP THÊM

Để phục vụ tốt nhất cho các kịch bản hỏi đáp chuyên sâu của sinh viên đang theo học, TV1 đề xuất crawl bổ sung từ các nguồn chính thức sau:

1. **Văn bản quy chế đào tạo & dịch vụ sinh viên:**
   * `https://fpt.edu.vn/` (Trang thông tin chung Tập đoàn giáo dục FPT)
   * Cổng thông tin học vụ FAP (FPT Academic Portal): `https://fap.fpt.edu.vn/` (Thu thập các tài liệu công khai về sổ tay sinh viên, quy chế khảo thí).
   * Cổng dịch vụ sinh viên: `https://dichvu.fpt.edu.vn/` (Quy định thủ tục giấy tờ, dịch vụ một cửa).
2. **Trang thông tin từng phân hiệu/cơ sở:**
   * Hà Nội: `https://hanoi.fpt.edu.vn/`
   * TP. Hồ Chí Minh: `https://hcmuni.fpt.edu.vn/`
   * Đà Nẵng: `https://dnuni.fpt.edu.vn/`
   * Cần Thơ: `https://cantho.fpt.edu.vn/`
   * Quy Nhơn: `https://quynhon.fpt.edu.vn/`
3. **Tài liệu PDF gốc (PDF regulations):**
   * Tìm kiếm và nạp các tệp PDF quy chế thi đua, khen thưởng, học bổng, kỷ luật sinh viên ban hành mới nhất (2024–2026).

---

## 9. KẾT LUẬN VÀ KẾ HOẠCH BÀN GIAO TIẾP THEO

* **Bàn giao cho TV2 (Retrieval & Indexing):**
  * Đã chuẩn bị sẵn `data/processed/corpus.jsonl` (3,931 chunks đầy đủ metadata, schema tương thích 100%).
  * Đã build và verify thành công chỉ mục baseline `data/processed/bm25_index/bm25_index.pkl`. TV2 có thể trực tiếp triển khai FAISS Vector Store và Cross-Encoder Reranker mà không cần tiền xử lý lại.
* **Bàn giao cho TV3 (Semantic Parsing & Generation):**
  * Đã bàn giao `data/processed/structured_data.json` chứa cấu trúc 190 biểu phí học phí chi tiết 5 cơ sở phục vụ router tra cứu số học chuẩn xác.
* **Kế hoạch tiếp theo của TV1:**
  * Sẵn sàng hỗ trợ TV2/TV3 trong việc fine-tune metadata filters nếu có yêu cầu chuyên biệt.
  * Chuẩn bị kịch bản crawl bổ sung tài liệu PDF sổ tay sinh viên khi có quyền truy cập nguồn tài liệu nội bộ.

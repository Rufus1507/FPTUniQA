# BỘ KỊCH BẢN KIỂM THỬ THỦ CÔNG GIAO DIỆN UI (FPTUniQA END-TO-END)

Bộ kịch bản này được thiết kế chuyên biệt để kiểm thử giao diện Web Chat (`http://localhost:8000/`) và Streamlit (`http://localhost:8501/`).
Mỗi kịch bản tập trung vào một khía cạnh cốt lõi của hệ sinh thái: **Từ điển học vụ $\rightarrow$ Query Rewriter $\rightarrow$ Semantic Router $\rightarrow$ Retrieval $\rightarrow$ LLM Generator**.

---

## KỊCH BẢN 1: HỘI THOẠI ĐA LƯỢT LIÊN HOÀN (MULTI-TURN ELLIPSIS & COREFERENCE)
> **Mục tiêu:** Kiểm tra khả năng ghi nhớ ngữ cảnh, viết lại câu tỉnh lược (ellipsis) và thay thế thực thể mượt mà qua LLM.

### Lượt 1: Câu hỏi gốc đầy đủ
- **Nhập vào UI:**
  ```text
  Học phí ngành Kỹ thuật phần mềm khóa 2026 tại Hà Nội là bao nhiêu?
  ```
- **Quan sát kỳ vọng:**
  - **Rewritten Query:** Giữ nguyên (hoặc chuẩn hóa khóa 2026 $\rightarrow$ K22, ngành KTPM).
  - **Route:** `structured_lookup`.
  - **Câu trả lời LLM:** Báo đúng mức học phí chính quy: **28.700.000 VNĐ / học kỳ** tại phân hiệu Hà Nội.

### Lượt 2: Tỉnh lược phân hiệu (Ellipsis Campus)
- **Nhập tiếp vào UI (cùng phiên):**
  ```text
  Còn ở phân hiệu Cần Thơ thì sao?
  ```
- **Quan sát kỳ vọng:**
  - **Rewritten Query:** Tự động khôi phục thành *"Học phí ngành Kỹ thuật phần mềm khóa 2026 tại phân hiệu Cần Thơ là bao nhiêu?"*.
  - **Câu trả lời LLM:** Báo đúng học phí tại Cần Thơ: **20.090.000 VNĐ / học kỳ** (áp dụng chính sách ưu đãi phân hiệu).

### Lượt 3: Thay đổi ngành học (Ellipsis Major)
- **Nhập tiếp vào UI (cùng phiên):**
  ```text
  Thế còn ngành Thiết kế vi mạch bán dẫn?
  ```
- **Quan sát kỳ vọng:**
  - **Rewritten Query:** Chuyển ngành sang *Vi mạch bán dẫn*, nhưng vẫn giữ vững địa điểm *Cần Thơ* và khóa *2026/K22*.
  - **Câu trả lời LLM:** Báo học phí ngành Thiết kế vi mạch bán dẫn tại Cần Thơ.

---

## KỊCH BẢN 2: KHỬ ĐA NGHĨA "AI" & BẢO VỆ NGỮ NGHĨA (DISAMBIGUATION GUARD)
> **Mục tiêu:** Đảm bảo hệ thống phân biệt được đại từ nghi vấn hỏi người ("Ai") với ngành Trí tuệ nhân tạo ("AI") và môn học ("môn AI").

### Kịch bản 2.1: Đại từ nhân sự / Người sáng lập
- **Nhập vào UI:**
  ```text
  Ai là người sáng lập Đại học FPT?
  ```
- **Quan sát kỳ vọng:**
  - **Động cơ Từ điển:** Tuyệt đối KHÔNG gán nhãn `MAJOR_AI`.
  - **Route:** `rag_pipeline`.
  - **Câu trả lời LLM:** Trả lời chính xác về TS. Trương Gia Bình và Tập đoàn FPT (không nói về chương trình đào tạo hay học phí ngành AI).

### Kịch bản 2.2: Đại từ trong thủ tục học vụ
- **Nhập vào UI:**
  ```text
  Em cần liên hệ ai để xin cấp bảng điểm và giấy xác nhận sinh viên?
  ```
- **Quan sát kỳ vọng:**
  - **Câu trả lời LLM:** Hướng dẫn liên hệ Phòng Dịch vụ sinh viên (DVSV) hoặc gửi ticket hỗ trợ qua hệ thống nội bộ FPTU.

### Kịch bản 2.3: Định nghĩa ngành Trí tuệ nhân tạo
- **Nhập vào UI:**
  ```text
  AI là gì vậy ad? Có khác gì với Khoa học máy tính không?
  ```
- **Quan sát kỳ vọng:**
  - **Động cơ Từ điển:** Nhận diện đúng `MAJOR_AI` vì câu hỏi có tính chất định nghĩa ("là gì").
  - **Câu trả lời LLM:** Giải thích rõ chuyên ngành Trí tuệ nhân tạo (AI) thuộc khối ngành CNTT tại ĐH FPT.

---

## KỊCH BẢN 3: TIẾNG LÓNG SINH VIÊN, VIẾT TẮT & KHÔNG DẤU (SLANG & DIACRITIC FOLDING)
> **Mục tiêu:** Kiểm tra khả năng chuẩn hóa tự động các từ viết tắt học vụ phổ biến của sinh viên FPTU.

### Test 3.1: Viết tắt phân hiệu & ký túc xá không dấu
- **Nhập vào UI:**
  ```text
  phi ktx o hl la bn tien 1 ky z ad
  ```
- **Quan sát kỳ vọng:**
  - **Chuẩn hóa:** `phi ktx` $\rightarrow$ Phí ký túc xá, `hl` $\rightarrow$ Hòa Lạc (Hà Nội).
  - **Câu trả lời LLM:** Báo đúng mức phí KTX Hòa Lạc là **4.000.000 VNĐ / học kỳ** kèm thông tin đặt cọc.

### Test 3.2: Viết tắt môn học & hình thức thi (PE/EOS)
- **Nhập vào UI:**
  ```text
  mon prf192 thi pe va eos nhu the nao
  ```
- **Quan sát kỳ vọng:**
  - **Chuẩn hóa:** `prf192` $\rightarrow$ Môn Cơ sở lập trình C, `pe` $\rightarrow$ Thi thực hành (Practical Exam), `eos` $\rightarrow$ Thi cuối kỳ (End of Semester).
  - **Câu trả lời LLM:** Giải thích chi tiết cấu trúc đánh giá gồm bài thi thực hành trên máy và bài thi lý thuyết cuối kỳ.

### Test 3.3: Thuật ngữ học tập (OJT / Tín chỉ)
- **Nhập vào UI:**
  ```text
  sv can tich luy bn tin chi de duoc di ojt vay
  ```
- **Quan sát kỳ vọng:**
  - **Chuẩn hóa:** `sv` $\rightarrow$ Sinh viên, `ojt` $\rightarrow$ Thực tập doanh nghiệp, `tin chi` $\rightarrow$ Tín chỉ.
  - **Câu trả lời LLM:** Trích dẫn quy chế đào tạo về điều kiện đi OJT (hoàn thành các môn tiên quyết, tiếng Anh và số tín chỉ tích lũy theo quy định).

---

## KỊCH BẢN 4: ĐỔI CHỦ ĐỀ ĐỘT NGỘT (TOPIC SWITCH DETECTION)
> **Mục tiêu:** Kiểm tra Query Rewriter không bị "ảo giác" bám dính ngữ cảnh cũ khi người dùng hỏi sang việc hoàn toàn khác.

### Lượt 1: Hỏi về học phí
- **Nhập vào UI:**
  ```text
  Học phí ngành Quản trị kinh doanh tại TP.HCM khóa 2026 là bao nhiêu?
  ```
- **Kết quả:** LLM cung cấp biểu phí ngành QTKD tại phân hiệu TP.HCM.

### Lượt 2: Cắt ngang hỏi về Quy chế thi (Topic Switch)
- **Nhập tiếp vào UI (cùng phiên):**
  ```text
  Quy định mang máy tính Casio vào phòng thi như thế nào?
  ```
- **Quan sát kỳ vọng:**
  - **Phát hiện đổi chủ đề:** Hệ thống nhận diện `Topic Switch`.
  - **Rewritten Query:** KHÔNG được ghép "ngành QTKD tại TP.HCM" vào câu hỏi phòng thi. Giữ nguyên ngữ cảnh tra cứu quy chế phòng thi.
  - **Câu trả lời LLM:** Trả lời đúng danh mục máy tính được phép mang vào phòng thi theo quy chế khảo thí.

---

## KỊCH BẢN 5: XỬ LÝ MÔN HỌC & ĐIỀU KIỆN TIÊN QUYẾT (COURSE SYLLABUS & PREREQUISITES)
> **Mục tiêu:** Kiểm tra trích xuất mã môn, tên tiếng Việt và các khía cạnh (aspect) giáo trình/tiên quyết.

### Test 5.1: Tra cứu giáo trình qua tên tiếng Việt
- **Nhập vào UI:**
  ```text
  Giáo trình môn Cơ sở lập trình C là cuốn sách nào?
  ```
- **Quan sát kỳ vọng:**
  - Nhận diện môn học `PRF192`, khía cạnh `course_aspect: textbook`.
  - LLM trích dẫn đúng tên sách giáo trình, tác giả và nhà xuất bản.

### Test 5.2: Tra cứu môn học tiên quyết
- **Nhập vào UI:**
  ```text
  Môn Cấu trúc dữ liệu và giải thuật cần hoàn thành môn nào trước?
  ```
- **Quan sát kỳ vọng:**
  - Nhận diện môn `CSD201`, khía cạnh `course_aspect: prerequisite`.
  - LLM thông báo môn học tiên quyết là `PRF192` (Cơ sở lập trình C) hoặc `PRO192` (Lập trình hướng đối tượng với Java).

---

## KỊCH BẢN 6: TRƯỜNG HỢP BIÊN & DỮ LIỆU TƯƠNG LAI (UNVERIFIED & GUARDRAILS)
> **Mục tiêu:** Đảm bảo hệ thống trung thực, không tự tiện bịa đặt thông tin khi dữ liệu chưa có trong quy chế.

### Test 6.1: Khóa tương lai xa (Chưa có biểu phí chính thức)
- **Nhập vào UI:**
  ```text
  Học phí khóa 2029 ngành Trí tuệ nhân tạo là bao nhiêu tiền?
  ```
- **Quan sát kỳ vọng:**
  - Động cơ từ điển gắn cờ `RAW_YEAR_2029 (verified: False)`.
  - LLM đưa ra câu trả lời cảnh báo thận trọng: Nhà trường chưa công bố biểu phí chính thức cho năm 2029, gợi ý tham khảo biểu phí khóa mới nhất hiện tại (K22 - 2026).

### Test 6.2: Ngành không đào tạo tại ĐH FPT (Out-of-Scope)
- **Nhập vào UI:**
  ```text
  Trường có đào tạo ngành Bác sĩ Y đa khoa không ad?
  ```
- **Quan sát kỳ vọng:**
  - LLM phản hồi rõ ràng: Đại học FPT hiện không đào tạo ngành Y đa khoa, liệt kê ngắn gọn các khối ngành trường đào tạo (Công nghệ thông tin, Quản trị kinh doanh, Công nghệ truyền thông, Ngôn ngữ, Luật).

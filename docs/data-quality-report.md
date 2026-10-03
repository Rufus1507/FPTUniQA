# BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU TV1

**Ngày báo cáo:** 2024-10-XX  
**Người thực hiện:** TV1 - Data & Knowledge  
**Trạng thái:** Đang tiến hành

---

## 1. TỔNG QUAN DỮ LIỆU HIỆN CÓ

### 1.1 Cấu trúc thư mục

```
data/
├── raw/                          # Dữ liệu thô từ crawler
│   ├── crawl_manifest.jsonl      # 226 bản ghi log crawl
│   ├── crawl_manifest_pilot_01.jsonl  # 56 bản ghi pilot
│   ├── crawl_inventory.txt
│   └── fpt_admission/html/       # 170 file HTML thô (~29 MB)
├── interim/                       # Dữ liệu trung gian
│   └── discarded_pages.jsonl     # 8 trang bị loại bỏ
├── processed/                     # Dữ liệu đã xử lý
│   ├── corpus.jsonl              # 3,931 chunks (~4 MB)
│   ├── structured_data.json      # Bảng học phí K22 (115 KB)
│   ├── metadata.json             # Metadata corpus
│   └── bm25_index/               # Index BM25 baseline
└── evaluation/                    # Dữ liệu đánh giá
    ├── questions.jsonl           # 6 câu hỏi test
    ├── golden_answers.jsonl      # 6 đáp án vàng
    └── ood_questions.jsonl      # 5 câu hỏi OOD
```

### 1.2 Thống kê tổng quan

| Chỉ số | Giá trị | Đánh giá |
|---------|---------|----------|
| Tổng HTML files | 170 | ⚠️ Ít |
| Documents trong corpus | 3,931 chunks | ⚠️ Dưới mục tiêu Tuần 6 (150-300) |
| Structured records (học phí) | 190 records | ✅ Tốt cho K22 |
| Evaluation questions | 6 câu | ❌ Rất ít (cần 150-250) |
| OOD test cases | 5 câu | ⚠️ Ít |

---

## 2. ĐÁNH GIÁ CHẤT LƯỢNG THEO KHÍA CẠNH

### 2.1 Đánh giá Corpus văn bản (`corpus.jsonl`)

#### ✅ Điểm mạnh
- **Độ phủ contract schema:** 100% - tất cả 3,931 chunks đều có đủ các trường bắt buộc
- **Cấu trúc phân đoạn:** Tốt - giữ nguyên bảng biểu, phân theo tiêu đề đề mục
- **Phân bố doc_type:** Hợp lý với curriculum chiếm chủ đạo (42.6%)

#### ⚠️ Điểm yếu
- **Độ dài chunk trung bình:** 217.9 ký tự (~46.8 từ) - **QUÁ NGẮN**
  - Tiêu chuẩn thường dùng: 400-500 tokens
  - Chunk ngắn ảnh hưởng đến ngữ cảnh và khả năng trả lời multi-hop
- **Thiếu dữ liệu cohort cũ:** Chỉ có K22 (2026), thiếu K20, K21, K23, K24
- **Thiếu effective_date chuẩn:** Nhiều documents không có ngày hiệu lực rõ ràng

#### Phân bố theo loại tài liệu

| doc_type | Số chunks | Tỷ lệ | Trạng thái |
|----------|-----------|--------|------------|
| curriculum | 1,676 | 42.6% | ⚠️ Cần bổ sung quy chế chi tiết |
| admission | 658 | 16.7% | ✅ Đã tốt |
| scholarship | 581 | 14.8% | ⚠️ Cần thêm điều kiện cụ thể |
| general | 546 | 13.9% | ⚠️ Tin tức ít giá trị QA |
| tuition | 445 | 11.3% | ✅ Đã cấu trúc hóa |
| enrollment | 25 | 0.6% | ❌ Quá ít |

#### Phân bố theo campus

| Campus | Số chunks | Tỷ lệ | Trạng thái |
|--------|-----------|--------|------------|
| all (toàn quốc) | 2,535 | 64.5% | ✅ |
| TP. HCM | 691 | 17.6% | ✅ |
| Hà Nội | 225 | 5.7% | ⚠️ |
| Cần Thơ | 218 | 5.5% | ⚠️ |
| Đà Nẵng | 131 | 3.3% | ⚠️ |
| Quy Nhơn | 131 | 3.3% | ⚠️ |

### 2.2 Đánh giá dữ liệu cấu trúc (`structured_data.json`)

#### ✅ Điểm mạnh
- **Hoàn chỉnh 100%** cho khóa K22 (2026)
- **5 campuses đầy đủ:** Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Quy Nhơn
- **38 ngành/chuyên ngành** được trích xuất
- **Tích hợp chính sách ưu đãi vùng miền**

#### ❌ Điểm yếu
- **Chỉ có duy nhất K22** - thiếu dữ liệu các khóa trước để so sánh
- **Không có bảng tín chỉ** theo ngành (cần cho câu hỏi "bao nhiêu tín chỉ?")
- **Không có dữ liệu học phí theo năm** (tăng giá hàng năm)
- **Không phân biệt học phí hệ chính quy/không chính quy**

### 2.3 Đánh giá bộ dữ liệu đánh giá (`evaluation/`)

| File | Số lượng | Đánh giá |
|------|----------|----------|
| questions.jsonl | 6 câu | ❌ Rất ít (cần 150-250) |
| golden_answers.jsonl | 6 câu | ❌ Rất ít (cần 150-250) |
| ood_questions.jsonl | 5 câu | ⚠️ Ít (cần 30-50) |

#### Phân bố theo category hiện tại
- `dao_tao`: 2 câu
- `tot_nghiep`: 1 câu
- `hoc_bong`: 1 câu
- `ky_luat`: 1 câu
- `hoc_phi`: 1 câu

#### ❌ Thiếu hụt nghiêm trọng
- Không có câu hỏi **Temporal** (theo năm/khóa)
- Không có câu hỏi **Multi-hop** (cần kết hợp nhiều nguồn)
- Không có câu hỏi **Conversational** (hội thoại đa lượt)
- Không có nhãn **structured query vàng** (intent + slots)

### 2.4 Đánh giá crawl data

#### ✅ Điểm mạnh
- **Tỷ lệ thành công:** 219/226 (96.9%)
- **13/13 seed URLs** đều thành công
- **170 HTML files** với nội dung đa dạng

#### ⚠️ Điểm yếu
- **7 HTTP 404** links hỏng
- **8 trang bị loại bỏ** (4 form động + 4 chuyên mục rỗng)
- **Không crawl được robots.txt** - có thể ảnh hưởng đến việc thu thập đầy đủ

---

## 3. PHÂN TÍCH KHE HỞ DỮ LIỆU (DATA GAPS)

### 3.1 Khoảng trống nghiêm trọng (Critical)

| Chủ đề | Trạng thái | Mô tả |
|---------|------------|--------|
| Quy chế đào tạo chi tiết | ⚠️ Thiếu | Không có văn bản quy chế đầy đủ |
| Điều kiện tốt nghiệp | ⚠️ Thiếu | Cần thêm chuẩn đầu ra cụ thể |
| Quy định kỷ luật | ⚠️ Thiếu | Không có văn bản disciplinarian |
| Học phí các khóa cũ | ❌ Thiếu hoàn toàn | Không so sánh được |

### 3.2 Khoảng trống quan trọng (Important)

| Chủ đề | Trạng thái | Mô tả |
|---------|------------|--------|
| Bảng tín chỉ theo ngành | ❌ Thiếu | Cần cho câu hỏi "tổng bao nhiêu tín chỉ?" |
| Chương trình đào tạo cụ thể | ⚠️ Ít | Cần chi tiết từng học phần |
| FAQ tuyển sinh | ⚠️ Ít | Cần thêm câu hỏi thường gặp |
| Hướng dẫn sinh viên | ⚠️ Ít | Quy định học tập chi tiết |

### 3.3 Khoảng trống có thể bổ sung (Optional)

| Chủ đề | Trạng thái | Mô tả |
|---------|------------|--------|
| Tin tức sự kiện | ⚠️ Thừa | 13.9% corpus là tin tức, ít giá trị QA |
| Thông tin cựu sinh viên | ⚠️ Ít | Ngoài phạm vi chính |

---

## 4. MỤC TIÊU THEO LỘ TRÌNH

### Tuần 3-4 (Hiện tại)
- [x] 3,931 chunks corpus ✅
- [x] Bảng học phí K22 ✅
- [ ] **30-50 câu hỏi với structured query vàng** ❌
- [ ] Chuẩn hóa effective_date và cohort ❌

### Tuần 5
- [ ] **30 kịch bản multi-turn** cho conversational QA
- [ ] Bổ sung dữ liệu curriculum chi tiết

### Tuần 6 (Đóng băng)
- [ ] **150-250 documents** trong corpus
- [ ] **150-250 test questions** với nhãn đầy đủ
- [ ] Đóng băng dữ liệu, không thay đổi

### Tuần 7-8
- [ ] Đánh giá độc lập
- [ ] Ablation study

---

## 5. KẾT LUẬN VÀ ĐỀ XUẤT HƯỚNG ĐI TIẾP

### 5.1 Kết luận

| Khía cạnh | Điểm (1-10) | Nhận xét |
|-----------|-------------|----------|
| Độ phủ nội dung | 6/10 | Cần bổ sung quy chế, kỷ luật |
| Chất lượng cấu trúc | 7/10 | Tốt, có structured_data.json |
| Độ chính xác metadata | 5/10 | Thiếu effective_date, cohort |
| Bộ đánh giá | 2/10 | **Rất thiếu** - cần 150-250 câu |
| Độ sẵn sàng TV2/TV3 | 7/10 | Có thể bắt đầu được |

### 5.2 Ưu tiên hành động

#### 🔴 Ưu tiên 1: Xây dựng bộ đánh giá (CRITICAL)
- Tạo 150-250 câu hỏi test phân bố đều các category
- Gán nhãn structured query vàng (intent + slots) cho từng câu
- Tạo bộ OOD questions (30-50 câu)

#### 🟠 Ưu tiên 2: Bổ sung documents thiếu
- Thu thập văn bản quy chế đào tạo chi tiết
- Thu thập quy định kỷ luật sinh viên
- Thu thập điều kiện tốt nghiệp đầy đủ

#### 🟡 Ưu tiên 3: Cải thiện metadata
- Chuẩn hóa effective_date cho tất cả documents
- Gán cohort rõ ràng (K20, K21, K22, K23, K24)
- Bổ sung bảng tín chỉ theo ngành

### 5.3 Đề xuất nguồn thu thập thêm

1. **Quy chế đào tạo:** Trang chủ FPT Edu nội bộ hoặc request trực tiếp
2. **Học phí các khóa cũ:** Archive hoặc yêu cầu từ phòng tài vụ
3. **Quy định kỷ luật:** Thường có trong "Sinh viên" hoặc "Học vụ"
4. **FAQ tuyển sinh:** Có thể thu thập từ trang chính thức

---

## 6. BẢNG GIAO DIỆN VÀ ĐIỀU KIỆN TIÊN QUYẾT

### Điều kiện để TV2 bắt đầu
- ✅ corpus.jsonl với đúng schema (Contract 1)
- ✅ BM25 index đã build
- ✅ Metadata có doc_type và campus

### Điều kiện để TV3 bắt đầu
- ✅ structured_data.json cho tra cứu số liệu
- ❌ Cần bộ questions với structured query vàng (cho semantic parsing evaluation)
- ❌ Cần 30+ multi-turn conversations

### Điều kiện để đánh giá Tuần 7
- ❌ Cần 150-250 test questions
- ❌ Cần Slot Accuracy labels
- ❌ Cần Intent classification labels

---

## 7. PHỤ LỤC

### A. Schema Contract 1 (Document)
```json
{
  "id": "chuẩn hóa UUID",
  "doc_id": "mã tài liệu gốc",
  "title": "tiêu đề",
  "text": "nội dung chunk",
  "source": "URL hoặc mã văn bản",
  "effective_date": "YYYY-MM-DD",
  "applies_to_cohort": ["K22", "K23"],
  "doc_type": "curriculum|admission|scholarship|tuition|enrollment|general",
  "campus": "all|ha_noi|ho_chi_minh|da_nang|can_tho|quy_nhon"
}
```

### B. Schema Contract 3 (Structured Query)
```json
{
  "q_id": "Q001",
  "query": "câu hỏi gốc",
  "category": "dao_tao|hoc_phi|hoc_bong|ky_luat|tot_nghiep",
  "expected_doc_ids": ["doc_001"],
  "golden_answer": "câu trả lời chuẩn",
  "structured_query": {
    "intent": "tra_cuu_so_lieu|giai_thich_chinh_sach",
    "slots": {
      "cohort": "K22",
      "campus": "ha_noi",
      "program": "CNTT"
    }
  }
}
```

---

*Báo cáo này sẽ được cập nhật theo tiến độ thực hiện.*

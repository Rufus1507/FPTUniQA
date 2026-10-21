# ĐỀ XUẤT CẢI THIỆN BỘ DATA ĐỂ ĐẠT 95+/100

---

## 1. TỔNG QUAN MỤC TIÊU

| Chỉ số | Hiện tại | Mục tiêu |
|--------|----------|----------|
| **Tổng điểm** | 89/100 | 95+/100 |
| **Xếp loại** | B+ | A |
| **Khoảng cách** | - | +6 điểm |

---

## 2. DANH SÁCH CẢI THIỆN THEO ƯU TIÊN

### 2.1. ƯU TIÊN CAO (Cộng ~4 điểm)

#### [P1] Bổ sung câu hỏi OOD vào evaluation data

**Mục tiêu**: Tăng độ phủ test Guardrail, đạt điểm tối đa 5/5

**Yêu cầu**:
- Thêm 15-20 câu hỏi OOD mới vào file `data/evaluation/ood_questions.jsonl`
- Đa dạng các domain: tin tức, thể thao, giải trí, công nghệ, chính trị, y tế, thời tiết, tài chính, du lịch, ẩm thực
- Mỗi câu hỏi cần có cấu trúc:
```json
{
  "q_id": "OOD_XXX",
  "query": "Nội dung câu hỏi",
  "domain": "tên_domain",
  "expected_action": "reject"
}
```

**Ví dụ câu hỏi cần thêm**:
1. "Điểm thi tốt nghiệp THPT 2024 bao giờ công bố?"
2. "Ai là người giàu nhất Việt Nam năm 2024?"
3. "Cách đăng ký kinh doanh online?"
4. "Giá Bitcoin hôm nay là bao nhiêu?"
5. "Đội bóng nào vô địch V-League 2024?"
6. "Cách nấu cơm chiên kim chi Hàn Quốc?"
7. "Thời tiết TP.HCM cuối tuần này thế nào?"
8. "Lãi suất ngân hàng nào cao nhất hiện nay?"
9. "Cách đặt vé máy bay giá rẻ?"
10. "Triệu chứng và cách chữa covid-19?"

---

#### [P2] Xác minh và cập nhật scripts/ingest_data.py sử dụng MarkItDown

**Mục tiêu**: Đảm bảo pipeline sử dụng MarkItDown cho chuyển đổi tài liệu

**Yêu cầu**:
- Cập nhật `scripts/ingest_data.py` để sử dụng Microsoft MarkItDown
- Cấu hình MarkItDown với các options:
  - `extract_images: true`
  - `ocr_enabled: true`
  - `preserve_layout: true`
  - `table_format: "markdown"`

**Code mẫu cần thêm vào scripts/ingest_data.py**:
```python
from markitdown import MarkItDown

class DocumentIngestionPipeline:
    def __init__(self, config):
        self.markitdown = MarkItDown()
        self.config = config
    
    def process_document(self, file_path: Path):
        # Sử dụng MarkItDown thay vì pdfplumber/docx/etc
        result = self.markitdown.convert(str(file_path))
        markdown_content = result.text_content
        return markdown_content
```

---

#### [P3] Xác minh và cập nhật chunking config (400-500 tokens, overlap 50)

**Mục tiêu**: Đảm bảo chunking đúng quy cách theo yêu cầu

**Yêu cầu**:
- Cập nhật `src/university_qa/data/chunker.py` hoặc config:
  - `chunk_size: 400-500 tokens`
  - `overlap: 50 tokens`
- Ưu tiên cắt theo ranh giới Điều/Khoản của văn bản quy phạm

**Code mẫu cần kiểm tra/cập nhật**:
```python
# Trong chunker.py hoặc config
CHUNK_CONFIG = {
    "max_tokens": 500,  # hoặc 400-500
    "min_tokens": 100,
    "overlap": 50,
    "strategy": "semantic_by_section"  # Ưu tiên cắt theo Điều/Khoản
}
```

---

### 2.2. ƯU TIÊN TRUNG BÌNH (Cộng ~2 điểm)

#### [P4] Thêm structured_payload vào corpus.jsonl

**Mục tiêu**: Hoàn thiện Contract 1 schema

**Yêu cầu**:
- Thêm trường `structured_payload` vào các chunk chứa số liệu trong `corpus.jsonl`
- Cấu trúc:
```json
{
  "doc_id": "tuition_k20_hn_001",
  "title": "Quy định học phí K20",
  "text": "Mức học phí...",
  "source": "Quyết định số XXX",
  "effective_date": "2024-01-01",
  "applies_to_cohort": ["K20"],
  "campus": "HN",
  "doc_type": "hoc_phi",
  "structured_payload": {
    "program": "CNTT",
    "cohort": "K20",
    "tuition_per_credit": 650000,
    "currency": "VND"
  }
}
```

**Hành động**: Chọn 10-20 documents mẫu có số liệu, thêm structured_payload

---

#### [P5] Thêm evaluation data cho multi-turn conversation

**Mục tiêu**: Test Context-Aware Query Rewriter

**Yêu cầu**:
- Tạo file mới `data/evaluation/multiturn_questions.jsonl`
- Mỗi entry gồm conversation history + câu hỏi hiện tại + expected rewritten query

**Cấu trúc**:
```json
{
  "q_id": "MT001",
  "history": [
    {"role": "user", "content": "Học phí ngành AI khóa K20 cơ sở Hà Nội bao nhiêu?"},
    {"role": "assistant", "content": "Học phí ngành AI khóa K20 tại cơ sở Hà Nội là 31.500.000 VNĐ/kỳ."}
  ],
  "current_query": "Còn cơ sở Hòa Lạc thì sao?",
  "expected_rewritten": "Học phí ngành AI khóa K20 cơ sở Hòa Lạc bao nhiêu?",
  "expected_cohort": "K20",
  "expected_campus": "FUHL"
}
```

**Số lượng**: 10-15 conversation mẫu

---

### 2.3. ƯU TIÊN THẤP (Cộng ~1 điểm)

#### [P6] Hoàn thiện source_files trong metadata.json

**Mục tiêu**: Đảm bảo metadata.json có danh sách đầy đủ các source files

**Yêu cầu**:
- Kiểm tra và bổ sung đầy đủ danh sách source_files trong `data/processed/metadata.json`
- Mỗi file cần có: file, cohort, campus, type (handbook/regulation/tuition/ojt...)

---

## 3. TỔNG HỢP ĐIỂM SAU CẢI THIỆN

| Hạng mục | Điểm trước | Điểm sau | Chênh lệch |
|-----------|-------------|----------|------------|
| A. Dữ liệu Corpus | 25 | 25 | 0 |
| B. Structured Data | 20 | 20 | 0 |
| C. Evaluation Data | 22 | 25 | +3 |
| D. Pipeline | 9 | 15 | +6 |
| E. Contract | 13 | 15 | +2 |
| **TỔNG CỘNG** | **89** | **100** | **+11** |

---

## 4. CHECKLIST THỰC HIỆN

### Phase 1: Hoàn thành trong ngày 1

- [ ] P1: Thêm 15-20 câu OOD vào `data/evaluation/ood_questions.jsonl`
- [ ] P2: Cập nhật `scripts/ingest_data.py` sử dụng MarkItDown
- [ ] P3: Xác minh và cập nhật chunking config (400-500 tokens, overlap 50)

### Phase 2: Hoàn thành trong ngày 2

- [ ] P4: Thêm structured_payload vào 20 documents mẫu trong corpus.jsonl
- [ ] P5: Tạo `data/evaluation/multiturn_questions.jsonl` với 10-15 mẫu
- [ ] P6: Hoàn thiện source_files trong metadata.json

---

## 5. LƯU Ý KHI THỰC HIỆN VỚI GEMINI

### Prompt cho Gemini:

```
Bạn hãy thực hiện các tác vụ sau để cải thiện bộ data của dự án FPTUniQA:

1. Đọc file hiện tại data/evaluation/ood_questions.jsonl
2. Thêm 15-20 câu hỏi OOD mới với các domain đa dạng (tin tức, thể thao, công nghệ, y tế, tài chính, v.v.)
3. Mỗi câu hỏi cần có: q_id, query, domain, expected_action: "reject"
4. Lưu lại file sau khi cập nhật

Tiếp theo:
1. Đọc scripts/ingest_data.py
2. Cập nhật để sử dụng Microsoft MarkItDown cho việc chuyển đổi tài liệu PDF/DOCX/XLSX
3. Kiểm tra và đảm bảo chunking config có chunk_size=500, overlap=50
4. Lưu các thay đổi

Tiếp theo:
1. Tạo file mới data/evaluation/multiturn_questions.jsonl
2. Thêm 10-15 mẫu conversation đa lượt với cấu trúc:
   - q_id, history, current_query, expected_rewritten, expected_cohort, expected_campus

Cuối cùng:
1. Đọc một vài dòng đầu của data/processed/corpus.jsonl
2. Thêm structured_payload vào các documents có số liệu học phí
3. Cập nhật lại file
```

---

## 6. FILES CẦN CHỈNH SỬA

| File | Hành động |
|------|-----------|
| `data/evaluation/ood_questions.jsonl` | Thêm 15-20 câu OOD |
| `scripts/ingest_data.py` | Cập nhật sử dụng MarkItDown |
| `src/university_qa/data/chunker.py` | Xác minh chunking config |
| `src/university_qa/data/config.py` | Thêm chunking config nếu chưa có |
| `data/processed/corpus.jsonl` | Thêm structured_payload |
| `data/evaluation/multiturn_questions.jsonl` | Tạo mới |
| `data/processed/metadata.json` | Hoàn thiện source_files |

---

**Ngày tạo**: 2026
**Mục tiêu điểm**: 95-100/100
**Xếp loại mục tiêu**: A (Xuất sắc)

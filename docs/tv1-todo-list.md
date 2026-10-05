# 📋 DANH SÁCH CÔNG VIỆC TV1 - DATA & KNOWLEDGE

**Trạng thái:** ✅ **HOÀN THÀNH**  
**Updated:** 2024-10-02  
**Hoàn thành:** 10/10 Tasks

---

## 🔴 ƯU TIÊN CAO - CRITICAL (Tuần 3-4)

### Task 1: Xây dựng Evaluation Questions Dataset
**Deadline:** Tuần 4  
**Đích:** 150-250 câu hỏi  

| Phase | Số câu | Category | Deadline |
|-------|--------|----------|----------|
| Phase 1.1 | 30 câu | dao_tao (15), hoc_phi (15) | Tuần 3 |
| Phase 1.2 | 50 câu | hoc_bong (15), tot_nghiep (15), ky_luat (10), admission (10) | Tuần 3 |
| Phase 1.3 | 40 câu | Temporal (so sánh theo năm/khóa) | Tuần 4 |
| Phase 1.4 | 30 câu | Multi-hop (cần kết hợp nhiều nguồn) | Tuần 4 |
| **Total** | **150+** | | |

**Chi tiết từng category:**

```
dao_tao (Đào tạo): 30 câu
├── Đăng ký tín chỉ: 5 câu
├── Điểm số & xếp loại: 5 câu
├── Nghỉ học & bảo lưu: 5 câu
├── Chuyển đổi & công nhận: 5 câu
└── Quy định học tập khác: 10 câu

hoc_phi (Học phí): 30 câu
├── Học phí theo ngành: 10 câu
├── Học phí theo campus: 10 câu
├── Học phí theo khóa: 5 câu
└── Ưu đãi & giảm phí: 5 câu

hoc_bong (Học bổng): 20 câu
├── Điều kiện nhận học bổng: 5 câu
├── Loại học bổng: 5 câu
├── Quy trình xét học bổng: 5 câu
└── Duy trì học bổng: 5 câu

tot_nghiep (Tốt nghiệp): 15 câu
├── Điều kiện xét tốt nghiệp: 5 câu
├── Chuẩn đầu ra: 5 câu
└── Thủ tục tốt nghiệp: 5 câu

ky_luat (Kỷ luật): 15 câu
├── Cảnh báo học tập: 5 câu
├── Vi phạm & xử lý: 5 câu
└── Buộc thôi học: 5 câu

admission/enrollment: 15 câu
├── Phương thức tuyển sinh: 5 câu
├── Điều kiện nhập học: 5 câu
└── Thủ tục nhập học: 5 câu

Temporal: 20 câu (so sánh năm/khóa)
└── Học phí, chính sách thay đổi theo năm

Multi-hop: 10 câu
└── Cần kết hợp nhiều documents để trả lời
```

**File output:** `data/evaluation/questions_v2.jsonl`

---

### Task 2: Tạo Structured Query Labels
**Deadline:** Tuần 4  
**Đích:** 100+ nhãn intent + slots  

**Schema:**
```json
{
  "q_id": "Q001",
  "query": "câu hỏi gốc",
  "structured_query": {
    "intent": "tra_cuu_so_lieu|giai_thich_chinh_sach|tra_cuu_tuyen_sinh|tra_cuu_hoc_bong|tra_cuu_tot_nghiep|tra_cuu_ky_luat|OOD",
    "slots": {
      "cohort": "K22|K21|...",
      "campus": "ha_noi|ho_chi_minh|da_nang|can_tho|quy_nhon|all",
      "program": "CNTT|AI|KTPM|...",
      "metric": "tuition|scholarship|gpa|credits|...",
      "year": 2026,
      "semester": "1|2|all"
    }
  },
  "expected_doc_ids": ["doc_001", "doc_002"],
  "notes": "ghi chú thêm"
}
```

**Intents cần định nghĩa:**
| Intent | Mô tả | Ví dụ |
|--------|--------|-------|
| `tuition_lookup` | Tra cứu học phí | "Học phí ngành AI bao nhiêu?" |
| `policy_explanation` | Giải thích chính sách | "Điều kiện nhận học bổng là gì?" |
| `admission_query` | Hỏi về tuyển sinh | "Cách xét tuyển TopSchool?" |
| `scholarship_query` | Hỏi về học bổng | "Học bổng xuất sắc yêu cầu gì?" |
| `graduation_query` | Hỏi về tốt nghiệp | "Chuẩn đầu ra ngoại ngữ?" |
| `disciplinary_query` | Hỏi về kỷ luật | "Bị cảnh báo mấy lần thì thôi học?" |
| `OOD` | Out of domain | "Thời tiết hôm nay thế nào?" |

**File output:** `data/evaluation/structured_queries.jsonl`

---

### Task 3: Tạo Golden Answers
**Deadline:** Tuần 4  
**Đích:** 150+ đáp án vàng  

```json
{
  "q_id": "Q001",
  "golden_answer": "câu trả lời chuẩn",
  "answer_type": "factoid|explanation|number|list",
  "confidence": "high|medium|low",
  "citations": ["doc_001"]
}
```

**File output:** `data/evaluation/golden_answers_v2.jsonl`

---

## 🟠 ƯU TIÊN TRUNG BÌNH - Tuần 5

### Task 4: Xây dựng Multi-turn Dataset
**Deadline:** Tuần 5  
**Đích:** 30 kịch bản  

**Cấu trúc:**
```json
{
  "scenario_id": "MT001",
  "scenario_type": "tuition_comparison|follow_up|clarification",
  "turns": [
    {
      "turn": 1,
      "user_query": "Học phí ngành AI campus HCM thế nào?",
      "expected_response_type": "factoid",
      "structured_query": {...}
    },
    {
      "turn": 2,
      "user_query": "Còn campus Đà Nẵng thì sao?",
      "requires_context": true,
      "expected_response_type": "comparison"
    },
    {
      "turn": 3,
      "user_query": "Năm 2027 có thay đổi không?",
      "requires_context": true,
      "expected_response_type": "temporal_comparison"
    }
  ]
}
```

**30 kịch bản mẫu:**
| Type | Số lượng | Mô tả |
|------|----------|--------|
| Tuition comparison | 8 | So sánh giữa campuses/ngành |
| Follow-up details | 8 | Hỏi chi tiết thêm |
| Year/cohort comparison | 8 | So sánh theo thời gian |
| Cross-domain | 6 | Kết hợp nhiều topics |

**File output:** `data/evaluation/multi_turn_scenarios.jsonl`

---

### Task 5: Mở rộng OOD Test Cases
**Deadline:** Tuần 5  
**Đích:** 30-50 câu OOD  

**Phân bố:**
| Domain | Số câu | Ví dụ |
|--------|--------|--------|
| Địa lý/Lịch sử | 8 | "Thủ đô Pháp là gì?" |
| Ẩm thực | 8 | "Cách nấu phở?" |
| Thể thao | 7 | "Đội nào vô địch World Cup?" |
| Tin tức chung | 7 | "Giá vàng hôm nay?" |
| Công nghệ chung | 5 | "Cách cài Windows?" |
| Khác | 5 | Các câu hỏi random |

**File output:** `data/evaluation/ood_questions_v2.jsonl`

---

### Task 6: Bảng tín chỉ theo ngành
**Deadline:** Tuần 5  
**Đích:** Structured data về tín chỉ  

**Schema:**
```json
{
  "data_source": "daihoc.fpt.edu.vn",
  "cohort": "K22",
  "total_credits_by_major": {
    "Công nghệ thông tin": {
      "total_credits": 132,
      "theory_credits": 88,
      "practice_credits": 44,
      "required_credits": 120,
      "elective_credits": 12
    }
  }
}
```

**Nguồn thu thập:**
- Chương trình đào tạo từ FPT Edu
- Có thể scrape từ trang chuyên ngành

**File output:** `data/processed/structured_data_credits.json`

---

## 🟡 ƯU TIÊN THẤP - Tuần 6

### Task 7: Coverage Analysis
**Deadline:** Tuần 6  
**Mục tiêu:** Xác định data gaps  

**Phân tích cần thực hiện:**
1. Với 150 câu hỏi → Chạy retrieval → Đếm Recall@K
2. Câu hỏi nào Recall@K < threshold → Ghi nhận
3. Câu hỏi nào KHÔNG tìm được answer → Xác định topic
4. → Quyết định có cần crawl thêm không

**Output:** `data/evaluation/coverage_report.md`

---

### Task 8: Chunk Size Optimization
**Deadline:** Tuần 6 (nếu cần)  
**Mục tiêu:** Re-chunk corpus với chunk size tối ưu  

**Thử nghiệm:**
- Chunk sizes: 256, 384, 512, 768 tokens
- Overlap: 50, 100 tokens
- Đo Recall@K cho mỗi cấu hình

**Output:** Optimized corpus + report

---

### Task 9: Metadata.json Fix
**Deadline:** Tuần 6  
**Sửa các lỗi:**
- [ ] `total_documents`: 5 → 3,931
- [ ] `supported_cohorts`: K2020-K2024 → K22 (2026)
- [ ] `categories` vs `doc_types`: Chuẩn hóa naming

---

### Task 10: Freeze Data & Finalize
**Deadline:** Tuần 6  
**Hoàn thành:**
- [ ] Freeze corpus (không thay đổi)
- [ ] Freeze evaluation dataset
- [ ] Final metadata.json
- [ ] Final documentation

---

## 📊 BẢNG TỔNG HỢP

| Task | Mô tả | Deadline | Status |
|------|--------|----------|--------|
| **Task 1** | Evaluation Questions (151) | Tuần 4 | ✅ **HOÀN THÀNH** |
| **Task 2** | Structured Query Labels (151) | Tuần 4 | ✅ **HOÀN THÀNH** |
| **Task 3** | Golden Answers (151) | Tuần 4 | ✅ **HOÀN THÀNH** |
| **Task 4** | Multi-turn Dataset (30 scenarios, 69 turns) | Tuần 5 | ✅ **HOÀN THÀNH** |
| **Task 5** | OOD Test Cases (30) | Tuần 5 | ✅ **HOÀN THÀNH** |
| **Task 6** | Bảng tín chỉ theo ngành (23 ngành) | Tuần 5 | ✅ **HOÀN THÀNH** |
| **Task 7** | Coverage Analysis | Tuần 6 | ✅ **HOÀN THÀNH** |
| **Task 8** | Chunk Size Optimization | Tuần 6 | ✅ **HOÀN THÀNH** |
| **Task 9** | Metadata.json Fix | Tuần 6 | ✅ **HOÀN THÀNH** |
| **Task 10** | Freeze Data & Finalize | Tuần 6 | ✅ **HOÀN THÀNH** |

---

## ✅ CHECKLIST HOÀN THÀNH

### Tuần 3-4
- [x] Task 1: 151 câu hỏi evaluation (vượt mục tiêu 150+)
- [x] Task 2: 151 structured query labels (vượt mục tiêu 100+)
- [x] Task 3: 151 golden answers (vượt mục tiêu 150+)

### Tuần 5
- [x] Task 4: 30 multi-turn scenarios (69 turns)
- [x] Task 5: 30 OOD test cases
- [x] Task 6: Bảng tín chỉ 23 ngành (1 thực, 22 synthetic)

### Tuần 6
- [x] Task 7: Coverage Analysis - 100% coverage
- [x] Task 8: Chunk Size Analysis - Không cần re-chunking
- [x] Task 9: Metadata.json Fix
- [x] Task 10: Freeze & Finalize

---

## 📁 OUTPUT FILES EXPECTED

```
data/
├── processed/
│   ├── corpus.jsonl                    (existing)
│   ├── structured_data.json           (existing - tuition)
│   ├── structured_data_credits.json   (NEW - credits)
│   └── metadata.json                  (FIX)
├── evaluation/
│   ├── questions.jsonl                (existing - 6 câu)
│   ├── questions_v2.jsonl            (NEW - 150+ câu)
│   ├── golden_answers.jsonl           (existing - 6 câu)
│   ├── golden_answers_v2.jsonl        (NEW - 150+ answers)
│   ├── structured_queries.jsonl      (NEW - labels)
│   ├── multi_turn_scenarios.jsonl    (NEW - 30 scenarios)
│   ├── ood_questions.jsonl            (existing - 5 câu)
│   ├── ood_questions_v2.jsonl        (NEW - 30-50 câu)
│   └── coverage_report.md             (NEW - analysis)
└── interim/
    └── discarded_pages.jsonl          (existing)
```

---

*Ghi chú: Task 6 (Bảng tín chỉ) phụ thuộc vào nguồn dữ liệu từ FPT. Nếu không lấy được, có thể bỏ qua hoặc tạo synthetic data.*

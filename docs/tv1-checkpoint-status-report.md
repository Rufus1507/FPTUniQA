# BÁO CÁO ĐỐI CHIẾU CHECKPOINT & HƯỚNG ĐI TIẾP THEO CHO TV1

**Ngày báo cáo:** 2024-10-02  
**Người thực hiện:** TV1 - Data & Knowledge  
**Nguồn tham chiếu:** `baocao.md`, `baocao2.md`, `docs/README.handoff_tv2_tv3.md`

---

## 1. TỔNG HỢP CHECKPOINT THEO KẾ HOẠCH

### 1.1 Bảng đối chiếu lộ trình 8 tuần

| Tuần | Mục tiêu | TV1 Deliverables | Trạng thái | Checkpoint thực tế |
|------|-----------|-----------------|------------|-------------------|
| **Tuần 1** | Skeleton Pipeline, BM25 Baseline, Data Contract | 20-30 docs, preprocessing script, BM25 | ✅ **HOÀN THÀNH** | 3,931 chunks, BM25 index ✅ |
| **Tuần 2** | Vertical Slice End-to-End Demo | 50 docs, 15 câu hỏi GT | ✅ **HOÀN THÀNH** | 3,931 chunks ✅, 6 câu hỏi ❌ |
| **Tuần 3** | FAISS Dense Index, Semantic Parsing bản nháp | Chuẩn hóa effective_date, 30-50 câu structured query vàng | ❌ **CHƯA XONG** | Cần bổ sung |
| **Tuần 4** | Cross-Encoder Reranker, Semantic Parser hoàn thiện | 100+ câu structured query vàng, bảng tín chỉ | ❌ **CHƯA XONG** | Cần bổ sung |
| **Tuần 5** | Context-Aware Query Rewriting, Multi-turn | 30 kịch bản multi-turn | ❌ **CHƯA XONG** | Cần bổ sung |
| **Tuần 6** | Guardrails/OOD, Freeze tính năng | 150-250 docs, 150-250 câu hỏi | ❌ **CHƯA XONG** | Cần bổ sung |
| **Tuần 7** | Ablation Study | Bộ test đa dạng 5 nhóm | ❌ **CHƯA XONG** | Cần bổ sung |
| **Tuần 8** | Báo cáo, bảo vệ | Error analysis, documentation | ❌ **CHƯA XONG** | Cần bổ sung |

---

## 2. PHÂN TÍCH CHI TIẾT TRẠNG THÁI HIỆN TẠI

### 2.1 Corpus (`data/processed/corpus.jsonl`)

| Chỉ số | Giá trị theo kế hoạch | Giá trị thực tế | Đánh giá |
|---------|----------------------|-----------------|----------|
| Số lượng chunks | 150-300 (Tuần 6) | **3,931** | ✅ **VƯỢT MỤC TIÊU** |
| Schema contract compliant | 100% | 100% | ✅ Hoàn thành |
| BM25 Index | Cần build | ✅ Đã build & verify | ✅ Hoàn thành |

**Phân bố theo doc_type:**
| doc_type | Số chunks | Tỷ lệ | Trạng thái |
|----------|-----------|--------|------------|
| curriculum | 1,676 | 42.6% | ✅ |
| admission | 658 | 16.7% | ✅ |
| scholarship | 581 | 14.8% | ✅ |
| general | 546 | 13.9% | ⚠️ Có thể loại bỏ |
| tuition | 445 | 11.3% | ✅ |
| enrollment | 25 | 0.6% | ❌ Thiếu nghiêm trọng |

**Phân bố theo campus:**
| Campus | Số chunks | Tỷ lệ | Trạng thái |
|--------|-----------|--------|------------|
| all (toàn quốc) | 2,535 | 64.5% | ✅ |
| ho_chi_minh | 691 | 17.6% | ✅ |
| ha_noi | 225 | 5.7% | ⚠️ |
| can_tho | 218 | 5.5% | ⚠️ |
| da_nang | 131 | 3.3% | ⚠️ |
| quy_nhon | 131 | 3.3% | ⚠️ |

### 2.2 Structured Data (`data/processed/structured_data.json`)

| Chỉ số | Giá trị theo kế hoạch | Giá trị thực tế | Đánh giá |
|---------|----------------------|-----------------|----------|
| Số records | Đủ cho K22 | **190 records** | ✅ Hoàn thành |
| Số campuses | 5 | **5** (HN, HCM, DN, CT, QN) | ✅ Hoàn thành |
| Số ngành | 38 ngành | **38 ngành** | ✅ Hoàn thành |
| Cohort | K22 (2026) | **K22 (2026)** | ⚠️ Chỉ có K22 |
| Bảng tín chỉ theo ngành | Cần có | ❌ **Không có** | ❌ Thiếu |
| Dữ liệu các khóa cũ | Cần cho so sánh | ❌ **Không có** | ❌ Thiếu |

### 2.3 Evaluation Data (`data/evaluation/`)

| File | Kế hoạch | Thực tế | Đánh giá |
|------|----------|---------|----------|
| questions.jsonl | 15 (Tuần 2) → 150-250 (Tuần 6) | **6 câu** | ❌ **THIẾU NGHIÊM TRỌNG** |
| golden_answers.jsonl | 15 (Tuần 2) → 150-250 (Tuần 6) | **6 câu** | ❌ **THIẾU NGHIÊM TRỌNG** |
| ood_questions.jsonl | 30-50 (Tuần 5) | **5 câu** | ❌ **THIẾU** |
| Multi-turn conversations | 30 (Tuần 5) | **0** | ❌ **CHƯA BẮT ĐẦU** |
| Structured query labels | 30-50 (Tuần 3) → 100+ (Tuần 4) | **0** | ❌ **CHƯA CÓ** |

### 2.4 Metadata (`data/processed/metadata.json`)

| Trường | Giá trị trong file | Thực tế corpus | Đánh giá |
|---------|---------------------|-----------------|----------|
| total_documents | 5 | 3,931 chunks | ❌ **Không khớp** |
| supported_cohorts | K2020-K2024 | K22 (2026) | ❌ **Lỗi thông tin** |
| categories | 5 categories | 6 doc_types | ⚠️ Không khớp |

> ⚠️ **Cảnh báo:** File `metadata.json` chứa thông tin không chính xác, cần được cập nhật.

---

## 3. ĐÁNH GIÁ TỔNG HỢP

### 3.1 Ma trận đánh giá theo module

| Module | Kế hoạch | Thực hiện | Tỷ lệ | Ưu tiên |
|--------|----------|-----------|-------|---------|
| **Corpus (số lượng)** | 150-300 docs | 3,931 chunks | 1310% | ✅ Hoàn thành |
| **Corpus (chất lượng)** | 400-500 tokens/chunk | ~217 ký tự/chunk | 43% | ⚠️ Chunk ngắn |
| **Structured Data (học phí)** | Đầy đủ K22 | 190 records, 5 campuses | 100% | ✅ Hoàn thành |
| **Structured Data (tín chỉ)** | Bảng tín chỉ | Không có | 0% | ❌ Cần bổ sung |
| **Evaluation Questions** | 150-250 câu | 6 câu | 4% | ❌ **CRITICAL** |
| **Structured Query Labels** | 100+ labels | 0 labels | 0% | ❌ **CRITICAL** |
| **Multi-turn Dataset** | 30 scenarios | 0 | 0% | ❌ Cần bắt đầu |
| **OOD Test Cases** | 30-50 câu | 5 câu | 17% | ❌ Cần bổ sung |

### 3.2 Phân tích SWOT

| | **Positive** | **Negative** |
|---|---|---|
| **Internal** | **Strengths (Điểm mạnh)** | **Weaknesses (Điểm yếu)** |
| | ✅ Corpus vượt mục tiêu 13x | ❌ Không có structured query labels |
| | ✅ BM25 index đã verify | ❌ Evaluation data rất ít (6 câu) |
| | ✅ Structured data học phí hoàn chỉnh | ❌ Chunk quá ngắn (~217 ký tự) |
| | ✅ Schema 100% compliant | ❌ Không có bảng tín chỉ |
| | | ❌ Metadata.json lỗi thông tin |
| **External** | **Opportunities (Cơ hội)** | **Threats (Thách thức)** |
| | 🎯 TV2/TV3 đã bắt đầu phát triển | ⏰ Tuần 3-4 deadline gần |
| | 🎯 Có thể thu thập thêm từ FPT | ⚠️ Phụ thuộc nguồn cấp (quy chế) |
| | 🎯 Ablation study có thể đo lường | ⚠️ Thiếu ground truth cho evaluation |

---

## 4. BẢNG GIAO DIỆN - TRẠNG THÁI SẴN SÀNG

### 4.1 Điều kiện cho TV2

| Yêu cầu TV2 | Trạng thái | Chi tiết |
|--------------|-------------|----------|
| corpus.jsonl với Contract 1 schema | ✅ Sẵn sàng | 3,931 chunks, đầy đủ fields |
| BM25 Index | ✅ Sẵn sàng | Đã build & verify |
| Metadata (doc_type, campus) | ✅ Sẵn sàng | Có phân bố đầy đủ |
| Effective_date standardization | ⚠️ Cần cải thiện | Còn thiếu cho nhiều docs |

### 4.2 Điều kiện cho TV3

| Yêu cầu TV3 | Trạng thái | Chi tiết |
|--------------|-------------|----------|
| structured_data.json | ✅ Sẵn sàng | 190 records K22 |
| corpus.jsonl | ✅ Sẵn sàng | 3,931 chunks |
| Evaluation questions | ❌ **Chưa sẵn sàng** | Chỉ 6 câu |
| Structured query labels | ❌ **Chưa sẵn sàng** | 0 labels |
| Multi-turn dataset | ❌ **Chưa sẵn sàng** | 0 scenarios |

### 4.3 Điều kiện cho Ablation Study (Tuần 7)

| Yêu cầu | Trạng thái | Chi tiết |
|----------|-------------|----------|
| 150-250 test questions | ❌ **Thiếu nghiêm trọng** | Chỉ 6 câu |
| Intent labels | ❌ Không có | Cần tạo |
| Slot labels | ❌ Không có | Cần tạo |
| OOD test cases (30-50) | ❌ Thiếu | Chỉ 5 câu |

---

## 5. KẾ HOẠCH HÀNH ĐỘNG TIẾP THEO

### 5.1 Ưu tiên cao (Tuần 3 - Ngay lập tức)

#### 🔴 Task 1: Xây dựng bộ Evaluation Questions (CRITICAL)
```
Mục tiêu: 150-250 câu hỏi test phân bố đều các category
Deadline: Trước Tuần 7

Phân bố mục tiêu:
- dao_tao: 40 câu (27%)
- hoc_phi: 40 câu (27%)
- hoc_bong: 25 câu (17%)
- tot_nghiep: 20 câu (13%)
- ky_luat: 15 câu (10%)
- admission/enrollment: 10 câu (6%)
```

#### 🔴 Task 2: Tạo Structured Query Labels
```
Mục tiêu: Nhãn intent + slots cho 100+ câu hỏi
Schema: {intent, slots: {cohort, campus, program, metric}}

Intents:
- tuition_lookup: tra cứu học phí
- policy_explanation: giải thích chính sách
- admission_query: hỏi về tuyển sinh
- scholarship_query: hỏi về học bổng
- graduation_query: hỏi về tốt nghiệp
- disciplinary_query: hỏi về kỷ luật
- OOD: out of domain
```

### 5.2 Ưu tiên trung bình (Tuần 4-5)

#### 🟠 Task 3: Bổ sung bảng tín chỉ theo ngành
```
Mục tiêu: Tạo structured_data_credits.json
Nội dung: Số tín chỉ cho từng ngành, tổng tín chỉ tốt nghiệp
Nguồn: Cần thu thập từ chương trình đào tạo
```

#### 🟠 Task 4: Xây dựng Multi-turn Dataset
```
Mục tiêu: 30 kịch bản hội thoại đa lượt
Cấu trúc: [context, query, expected_response, structured_query]
Ví dụ:
- Turn 1: "Học phí ngành AI thế nào?" → {intent: tuition_lookup, slots: {program: AI}}
- Turn 2: "Còn năm 2027 thì sao?" → {intent: tuition_lookup, slots: {program: AI, cohort: 2027}}
```

#### 🟠 Task 5: Mở rộng OOD Test Cases
```
Mục tiêu: 30-50 câu hỏi OOD
Phân bố domains:
- Địa lý/Lịch sử: 10 câu
- Ẩm thực/Nấu ăn: 10 câu
- Thể thao/Giải trí: 10 câu
- Tin tức chung: 10 câu
```

### 5.3 Ưu tiên thấp (Tuần 6+)

#### 🟡 Task 6: Cải thiện chunk size
```
Mục tiêu: Tăng chunk size lên 400-500 tokens
Cách thực hiện: Re-chunk corpus với overlap hợp lý
```

#### 🟡 Task 7: Cập nhật metadata.json
```
Mục tiêu: Sửa thông tin sai trong metadata.json
Nội dung: total_documents, supported_cohorts, categories
```

---

## 6. BẢNG TIMELINE ĐỀ XUẤT

| Tuần | Tasks | Deliverables | Trạng thái |
|------|-------|--------------|------------|
| **Tuần 3** | Task 1, Task 2 | 50 câu hỏi + labels | 🔲 Cần thực hiện |
| **Tuần 4** | Task 2, Task 3 | 100 câu hỏi + labels + tín chỉ | 🔲 |
| **Tuần 5** | Task 4, Task 5 | 30 multi-turn + 30 OOD | 🔲 |
| **Tuần 6** | Task 1 (hoàn thiện), Task 6, Task 7 | 150-250 câu + freeze | 🔲 |

---

## 7. CHECKLIST GIAO NỘP

### 7.1 Đã hoàn thành (✅)

- [x] Corpus 3,931 chunks với Contract 1 schema
- [x] BM25 Index đã build & verify
- [x] Structured data học phí K22 (190 records, 5 campuses)
- [x] Nhật ký crawl (226 bản ghi)
- [x] Trang bị loại bỏ (8 trang)
- [x] Báo cáo handoff cho TV2 & TV3
- [x] Documentation đầy đủ trong docs/

### 7.2 Đang thiếu (❌)

- [ ] **Evaluation questions: 6/150-250** (4%)
- [ ] **Structured query labels: 0/100+** (0%)
- [ ] **Multi-turn dataset: 0/30** (0%)
- [ ] **OOD test cases: 5/30-50** (17%)
- [ ] Bảng tín chỉ theo ngành
- [ ] Dữ liệu cohort cũ (K20-K24)
- [ ] Chunk size chuẩn (400-500 tokens)

---

## 8. KẾT LUẬN

### 8.1 Tổng điểm hoàn thành TV1

| Component | Weight | Completion | Score |
|-----------|--------|------------|-------|
| Corpus (số lượng) | 15% | 1310% | 15/15 |
| Corpus (chất lượng) | 10% | 43% | 4.3/10 |
| Structured Data (học phí) | 15% | 100% | 15/15 |
| Structured Data (tín chỉ) | 10% | 0% | 0/10 |
| Evaluation Data | 25% | 4% | 1/25 |
| Structured Labels | 15% | 0% | 0/15 |
| Multi-turn Dataset | 10% | 0% | 0/10 |
| **Tổng** | 100% | — | **35.3/100** |

### 8.2 Nhận định

| Khía cạnh | Nhận xét |
|-----------|----------|
| **Điểm mạnh** | Corpus vượt mục tiêu, structured data học phí tốt, BM25 hoạt động |
| **Điểm yếu nghiêm trọng** | Evaluation data gần như bằng 0, không có structured labels |
| **Rủi ro** | Không thể đánh giá Tuần 7 nếu không có evaluation data |
| **Hướng giải quyết** | Tập trung 80% effort vào xây dựng evaluation dataset |

### 8.3 Lời khuyên

1. **Ưu tiên tuyệt đối:** Xây dựng evaluation questions (150-250 câu)
2. **Song song:** Tạo structured query labels cho các câu hỏi đó
3. **Bổ sung dần:** Multi-turn và OOD cases có thể làm sau
4. **Không delay:** Tuần 3-4 cần hoàn thành Task 1 và Task 2

---

*Báo cáo này được tạo tự động để đối chiếu checkpoint. Cần cập nhật theo tiến độ thực tế.*

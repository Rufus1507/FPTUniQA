# 📋 Hợp Đồng Dữ Liệu (Data Schema Contract)

> Chi tiết yêu cầu chuẩn mực xem tại: [Quy Chuẩn Yêu Cầu Bộ Data Cần & Đủ](file:///h:/PythonProject/FPTUniQA/docs/yeu_cau_bo_data.md)

## 1. Schema của `corpus.jsonl` (Contract 1 Hybrid)
Mỗi dòng trong `data/processed/corpus.jsonl` là một đối tượng JSON đại diện cho một chunk tài liệu quy chế:

```json
{
  "id": "doc_fpt_k19_0042",
  "doc_id": "doc_fpt_k19_0042",
  "title": "Quy định tài chính K19 - Học phí chuyên ngành và lệ phí học lại",
  "text": "Nội dung điều khoản chi tiết...",
  "source": "Hướng dẫn Tài chính Sinh viên K19",
  "effective_date": "2023-09-01",
  "applies_to_cohort": ["K19"],
  "campus": "ALL",
  "doc_type": "finance_regulation",
  "metadata": {
    "doc_id": "doc_fpt_k19_0042",
    "section": "Mục 2: Lệ phí học lại và thi lại",
    "cohort": "K19",
    "campus": "ALL",
    "effective_date": "2023-09-01",
    "category": "hoc_phi"
  }
}
```

## 2. Schema của `structured_data.json`
Chứa các bảng biểu số học cần tra cứu chính xác 100% (Zero Hallucination):
```json
{
  "academic_years": ["2023-2024", "2024-2025", "2025-2026"],
  "tuition_table": [
    {
      "cohort": "K19",
      "campus": "HN",
      "program": "Kỹ thuật phần mềm",
      "prep_english_per_level_vnd": 11300000,
      "prep_english_levels": 6,
      "specialized_term_tuition_vnd": 28700000,
      "total_specialized_terms": 9,
      "ojt_term_tuition_vnd": 0,
      "retake_exam_fee_vnd": 300000,
      "relearn_per_credit_vnd": 650000
    }
  ],
  "dormitory_fees": [
    {
      "campus": "FUHL",
      "room_type": "Phòng 4 người",
      "fee_per_term_vnd": 4000000
    }
  ]
}
```


## 3. Schema của `structured_data_courses.json` (Curriculum Knowledge Base)
Chứa tri thức về mã môn học, ngành đào tạo, lộ trình học tập, nội dung đào tạo (`syllabus`) và giáo trình (`textbook`):
```json
{
  "courses": [
    {
      "course_code": "PRF192",
      "course_name": "C Programming Fundamentals",
      "vietnamese_name": "Cơ sở lập trình C",
      "program": "Kỹ thuật phần mềm",
      "programs": ["Kỹ thuật phần mềm", "Trí tuệ nhân tạo", "An toàn thông tin", "Khoa học máy tính", "Hệ thống thông tin"],
      "category": "core",
      "credits": 3,
      "semester": 1,
      "prerequisites": [],
      "assessment": {"practical_exam": true, "eos": true, "project": false, "assignment": true},
      "syllabus": [
        "Cơ bản về biến, kiểu dữ liệu, toán tử trong C",
        "Cấu trúc rẽ nhánh (if-else, switch-case) và vòng lặp",
        "Hàm (Functions), truyền tham số và phạm vi biến",
        "Mảng và xử lý chuỗi ký tự (String)",
        "Con trỏ (Pointers), cấp phát bộ nhớ động",
        "Kiểu dữ liệu có cấu trúc (struct, union)",
        "Thao tác tệp tin (File I/O)"
      ],
      "textbook": {
        "main": "The C Programming Language (2nd Edition)",
        "author": "Brian W. Kernighan, Dennis M. Ritchie",
        "publisher": "Prentice Hall",
        "references": ["C How to Program (Paul Deitel, Harvey Deitel)"]
      }
    }
  ]
}
```

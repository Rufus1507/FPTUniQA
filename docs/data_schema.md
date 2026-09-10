# 📋 Hợp Đồng Dữ Liệu (Data Schema Contract)

## 1. Schema của `corpus.jsonl`
Mỗi dòng trong `data/processed/corpus.jsonl` là một đối tượng JSON đại diện cho một chunk tài liệu:

| Trường | Kiểu dữ liệu | Bắt buộc | Mô tả |
| :--- | :--- | :---: | :--- |
| `id` | `string` | Có | Định danh duy nhất của chunk (ví dụ: `doc_0001`) |
| `title` | `string` | Có | Tiêu đề văn bản hoặc tiêu đề điều khoản quy chế |
| `text` | `string` | Có | Nội dung đoạn văn bản đã được làm sạch |
| `metadata` | `object` | Có | Siêu dữ liệu bổ trợ phục vụ lọc và trích dẫn |

### Cấu trúc chi tiết của trường `metadata`:
```json
{
  "doc_id": "QC-2023-01",
  "section": "Điều 12: Đăng ký học phần",
  "cohort": "K2020-K2024",
  "effective_date": "2023-09-01",
  "category": "dao_tao"
}
```

## 2. Schema của `structured_data.json`
Chứa các bảng biểu có cấu trúc cần tra cứu số học chính xác (học phí, tín chỉ):
```json
{
  "academic_year": "2023-2024",
  "tuition_rates": [
    {
      "faculty": "Công nghệ Thông tin",
      "major_code": "7480201",
      "major_name": "Khoa học Máy tính",
      "credit_price_vnd": 650000,
      "standard_credits_per_term": 16,
      "estimated_term_tuition_vnd": 10400000
    }
  ]
}
```

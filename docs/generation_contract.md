# ✍️ Hợp Đồng Đầu Ra Tầng Sinh & Context (Generation Contract)

## 1. Mục tiêu
Quy định cấu trúc trả lời của mô hình ngôn ngữ lớn, nguyên tắc trích dẫn chứng cứ và cách xử lý khi thiếu thông tin.

## 2. Quy chuẩn Trích dẫn (Citations)
- Mọi câu trả lời chứa thông tin cụ thể (số tín chỉ, điểm số, mức tiền, điều kiện) phải đi kèm trích dẫn thẻ `[doc_id]` hoặc tên Điều khoản quy chế.
- Ví dụ:
  > Theo quy chế, sinh viên được đăng ký tối đa 24 tín chỉ mỗi học kỳ chính [doc_001].

## 3. Quy chuẩn chống ảo giác (Hallucination Policy)
- Nếu câu hỏi nằm ngoài phạm vi tài liệu tra cứu: Phải thẳng thắn thông báo chưa có dữ liệu và hướng dẫn liên hệ phòng ban chức năng.
- Tuyệt đối không tự suy luận các mốc thời gian hoặc con số không có trong ngữ cảnh.

## 4. Cấu trúc đối tượng phản hồi tầng Generation
```json
{
  "answer": "string",
  "citations": [
    {
      "doc_id": "doc_001",
      "title": "Quy chế đào tạo theo tín chỉ",
      "section": "Điều 12",
      "snippet": "Đoạn trích dẫn chứng minh..."
    }
  ]
}
```

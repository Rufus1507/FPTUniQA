# 🌐 Tài Liệu REST API Backend

## 1. Địa chỉ máy chủ
- Môi trường cục bộ: `http://localhost:8000`
- Swagger UI tài liệu tương tác: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 2. Danh sách Endpoints

### 2.1. Kiểm tra trạng thái hệ thống
- **Endpoint**: `GET /healthz`
- **Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2.2. Hỏi đáp quy chế (Query RAG)
- **Endpoint**: `POST /api/v1/query`
- **Request Body**:
```json
{
  "query": "Sinh viên được đăng ký tối đa bao nhiêu tín chỉ một học kỳ chính?",
  "top_k": 5,
  "conversation_id": "session_123"
}
```
- **Response**:
```json
{
  "query": "Sinh viên được đăng ký tối đa bao nhiêu tín chỉ một học kỳ chính?",
  "normalized_query": "sinh viên được đăng ký tối đa bao nhiêu tín chỉ một học kỳ chính?",
  "intent": "factoid",
  "answer": "Theo Điều 12 Quy chế đào tạo, sinh viên có học lực bình thường được đăng ký tối đa 24 tín chỉ mỗi học kỳ chính...",
  "citations": [
    {
      "doc_id": "doc_001",
      "title": "Quy chế đào tạo theo tín chỉ - Điều 12: Đăng ký học phần",
      "section": "Điều 12",
      "snippet": "Sinh viên phải đăng ký học phần trước khi bắt đầu học kỳ..."
    }
  ],
  "retrieved_documents": [ ... ]
}
```

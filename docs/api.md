# 📡 Tài Liệu Đặc Tả Backend REST API (TV3 - Tuần 1)

Tài liệu này mô tả các endpoint của dịch vụ FastAPI Backend cho hệ thống RAG Hỏi - Đáp học vụ Đại học FPT.

---

## 1. Thông Tin Chung

- **Giao thức**: HTTP / REST
- **Định dạng dữ liệu**: `application/json`
- **Địa chỉ mặc định cục bộ**: `http://localhost:8000`
- **Tài liệu Swagger UI tự động**: `http://localhost:8000/docs`
- **Tài liệu ReDoc**: `http://localhost:8000/redoc`

---

## 2. Danh Sách Endpoint

### 2.1. Kiểm tra trạng thái máy chủ (Health Check)

Kiểm tra kết nối và độ sẵn sàng của máy chủ backend.

- **Phương thức**: `GET`
- **Đường dẫn**: `/healthz`
- **Headers**: Không yêu cầu
- **Phản hồi thành công (200 OK)**:
  ```json
  {
    "status": "ok"
  }
  ```

---

### 2.2. Hỏi đáp học vụ qua RAG Pipeline (Query QA)

Tiếp nhận câu hỏi học vụ của sinh viên, kích hoạt luồng RAG và trả về câu trả lời kèm danh sách trích dẫn nguồn có cấu trúc.

- **Phương thức**: `POST`
- **Đường dẫn**: `/api/v1/query`
- **Headers**: 
  - `Content-Type: application/json`

#### Request Body:
```json
{
  "query": "Điều kiện để không bị cảnh cáo học vụ là gì?"
}
```

| Trường (Field) | Kiểu dữ liệu | Bắt buộc | Mô tả |
| :--- | :---: | :---: | :--- |
| `query` | `string` | Có | Câu hỏi bằng ngôn ngữ tự nhiên của sinh viên (tối thiểu 1 ký tự). |

#### Response Body thành công (200 OK):
```json
{
  "answer": "Theo quy chế của Đại học FPT [Nguồn 1], để không bị cảnh cáo học vụ, sinh viên cần duy trì điểm trung bình học kỳ (GPA) đạt từ 1.0 trở lên trong học kỳ đầu tiên, hoặc từ 1.2 trở lên trong các học kỳ tiếp theo. Đồng thời, điểm trung bình tích lũy (CGPA) phải đạt từ 1.2 đối với năm nhất, từ 1.4 đối với năm hai và từ 1.6 đối với năm ba trở đi. Sinh viên nhận 3 lần cảnh báo liên tiếp sẽ bị xử lý buộc thôi học [Nguồn 1].",
  "citations": [
    {
      "doc_id": "FPTU-QC-001",
      "title": "Quy chế cảnh báo học vụ và đình chỉ học tập",
      "source": "Sổ tay sinh viên ĐH FPT 2024 - Mục 4.2: Cảnh báo học tập, Trang 22"
    }
  ]
}
```

| Trường (Field) | Kiểu dữ liệu | Mô tả |
| :--- | :---: | :--- |
| `answer` | `string` | Câu trả lời tổng hợp từ AI dựa trên các tài liệu quy chế được trích xuất. |
| `citations` | `array[object]` | Danh sách các nguồn tài liệu được làm căn cứ trích dẫn cho câu trả lời. |
| `citations[].doc_id` | `string` | Mã định danh văn bản / chunk. |
| `citations[].title` | `string` | Tiêu đề văn bản quy chế hoặc môn học. |
| `citations[].source` | `string` | Nguồn trích dẫn chi tiết (tên quyết định, số trang, số điều). |

#### Response khi có lỗi (500 Internal Server Error):
```json
{
  "detail": "Lỗi trong quá trình xử lý câu hỏi tại RAG Pipeline: [Chi tiết thông báo lỗi]"
}
```

---

## 3. Mã Nguồn Mẫu Gọi API Bằng cURL

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Điều kiện để không bị cảnh cáo học vụ là gì?"}'
```

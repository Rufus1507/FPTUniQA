# 📑 Hợp Đồng Tầng Retrieval (Retrieval Contract Specification)

> **Phụ trách chính**: Thành viên TV3 (Thiết kế Interface & Mock Tuần 1) & Thành viên TV2 (Hiện thực hóa thuật toán Tuần 2+)  
> **Trạng thái**: Đã thống nhất & Khóa giao diện (Frozen Interface)

---

## 1. Mục Đích
Tài liệu này xác lập "Hợp đồng giao diện" (Interface Contract) giữa **Tầng Tìm Kiếm (Retrieval - TV2)** và **Tầng Điều Phối & Sinh (Pipeline/Generation - TV3)**. 

Bằng việc cố định chữ ký hàm (function signature) và lược đồ dữ liệu đầu ra (data schema), TV3 có thể xây dựng hoàn chỉnh Pipeline RAG, API Backend và Giao diện UI ngay trong Tuần 1 với `mock_retriever.py`. Sang Tuần 2, TV2 chỉ cần cài đặt thuật toán tìm kiếm thật (BM25 + Dense FAISS + RRF) tuân theo đúng contract này mà **không làm thay đổi bất kỳ dòng mã nào ở các tầng trên**.

---

## 2. Đặc Tả Chữ Ký Hàm (Function Signature)

```python
def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Truy xuất danh sách các đoạn tài liệu quy chế liên quan nhất đến câu hỏi.

    Tham số:
        query (str): Câu truy vấn của sinh viên (đã được chuẩn hóa bởi normalizer).
        top_k (int, optional): Số lượng đoạn văn bản cần lấy ra. Mặc định là 5.

    Trả về:
        list[dict]: Danh sách các item kết quả, sắp xếp giảm dần theo `score`.
    """
```

---

## 3. Lược Đồ Dữ Liệu Chi Tiết (Item Schema)

Mỗi phần tử `dict` trong danh sách trả về bắt buộc phải có đầy đủ các khóa (keys) sau:

| Tên Khóa (Key) | Kiểu Dữ Liệu | Giá Trị Mẫu | Mô Tả Ý Nghĩa |
| :--- | :---: | :--- | :--- |
| `doc_id` | `str` | `"QC-2024-D12"` | Mã định danh duy nhất của đoạn tài liệu / chunk. |
| `title` | `str` | `"Quy định đăng ký học phần & tín chỉ"` | Tiêu đề điều khoản hoặc phần quy chế. |
| `category` | `str` | `"quy_che"` | Phân loại dữ liệu: `"syllabus"` \| `"quy_che"` \| `"hoc_phi_hoc_bong"`. |
| `content` | `str` | `"Sinh viên được đăng ký tối đa 24 tín chỉ mỗi học kỳ chính..."` | Nội dung văn bản chi tiết dùng làm ngữ cảnh (context) cho LLM. |
| `source` | `str` | `"Quy chế Đào tạo ĐH FPT 2024 - Điều 12, Trang 18"` | Nguồn trích dẫn tường minh để hiển thị lên giao diện UI cho sinh viên. |
| `score` | `float` | `0.89` | Điểm độ tương đồng liên quan, chuẩn hóa trong đoạn `[0.0, 1.0]`. |

---

## 4. Dữ Liệu Trả Về Mẫu (JSON Example)

```json
[
  {
    "doc_id": "FPTU-QC-01",
    "title": "Quy chế cảnh báo học vụ và đình chỉ học tập",
    "category": "quy_che",
    "content": "Sinh viên có điểm trung bình học kỳ (GPA) dưới 1.0 trong kỳ học đầu tiên hoặc dưới 1.2 trong các kỳ tiếp theo sẽ nhận 1 mức cảnh báo học vụ. Sinh viên nhận 3 lần cảnh báo liên tiếp sẽ bị buộc thôi học.",
    "source": "Sổ tay sinh viên ĐH FPT 2024 - Mục 4.2, Trang 22",
    "score": 0.94
  },
  {
    "doc_id": "FPTU-TN-03",
    "title": "Điều kiện xét tốt nghiệp đại học",
    "category": "quy_che",
    "content": "Sinh viên được xét tốt nghiệp khi tích lũy đủ số tín chỉ quy định, điểm trung bình tích lũy toàn khóa (CGPA) đạt từ 2.00 trở lên, hoàn thành chuẩn đầu ra tiếng Anh (TOEIC 550 hoặc IELTS 5.5 hoặc tương đương), chứng chỉ GDQP và GDTC.",
    "source": "Quy chế Đào tạo ĐH FPT 2024 - Điều 28, Trang 45",
    "score": 0.88
  }
]
```

---

## 5. Các Điểm Thành Viên TV2 Cần Lưu Ý Khi Triển Khai (Checklist Tuần 2)

1. **Chuẩn hóa điểm số (`score`)**: 
   - BM25 nguyên bản có điểm không giới hạn, Vector Cosine Sim trong khoảng [-1, 1], còn RRF tính nghịch đảo hạng. TV2 cần chuẩn hóa điểm số trả về về đoạn `[0.0, 1.0]` (ví dụ dùng Min-Max scaling hoặc Sigmoid).
2. **Định dạng `category` cố định**:
   - Hiện tại hệ thống chuẩn hóa 3 nhóm: `"syllabus"`, `"quy_che"`, `"hoc_phi_hoc_bong"`. Nếu TV2 mở rộng thêm danh mục, cần thông báo TV3 cập nhật UI badge.
3. **Ràng buộc hiệu năng (Latency SLA)**:
   - Tổng thời gian thực thi hàm `retrieve()` không nên vượt quá **350ms** trên máy dev để đảm bảo phản hồi UI tức thì.
4. **Xử lý khi không tìm thấy tài liệu phù hợp**:
   - Trả về danh sách rỗng `[]` thay vì văng lỗi `Exception` (Pipeline sẽ tự động xử lý kịch bản không có context).

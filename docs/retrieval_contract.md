# 🔍 Hợp Đồng Đầu Ra Tầng Retrieval (Retrieval Contract)

## 1. Mục tiêu
Quy chuẩn hóa giao diện giữa tầng tìm kiếm (TV2) và tầng sinh ngôn ngữ / tổng hợp context (TV3).

## 2. Đầu vào
- `query` (`str`): Câu truy vấn đã qua bộ chuẩn hóa (`QueryNormalizer`).
- `top_k` (`int`, mặc định: 10): Số lượng tài liệu ứng viên cần lấy ra.

## 3. Đầu ra (Output Signature)
Phương thức `retrieve()` của Retriever hoặc `rerank()` của Reranker bắt buộc trả về danh sách `Tuple[Dict[str, Any], float]`:

```python
List[
    Tuple[
        {
            "id": str,
            "title": str,
            "text": str,
            "metadata": {
                "doc_id": str,
                "section": str,
                "cohort": str,
                "category": str
            }
        },
        float  # Điểm tương đồng hoặc điểm RRF hoặc logit của Cross-Encoder
    ]
]
```

## 4. Ràng buộc hiệu năng
- Thời gian phản hồi tầng Hybrid Search <= 150ms trên CPU.
- Thời gian qua Cross-Encoder Reranker <= 250ms trên CPU cho 20 ứng viên.

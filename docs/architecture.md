# 🏛️ Tài Liệu Kiến Trúc Hệ Thống (Architecture Design)

## 1. Tổng quan hệ thống
Hệ thống **University QA** là kiến trúc RAG chuyên biệt cho các trường đại học, phục vụ việc tra cứu quy chế đào tạo, chuẩn đầu ra, học bổng và biểu phí.

## 2. Sơ đồ dòng dữ liệu và xử lý (End-to-End Flow)

```mermaid
sequenceDiagram
    autonumber
    actor User as Sinh viên
    participant API as FastAPI Gateway
    participant Query as Query Engine (Normalizer & Intent)
    participant Struct as Structured Parser
    participant Hybrid as Hybrid Retriever (BM25 + FAISS)
    participant Rerank as Cross-Encoder Reranker
    participant Gen as Context & LLM Generator

    User->>API: Gửi câu hỏi (query)
    API->>Query: Chuẩn hóa từ viết tắt & phân loại ý định
    alt Ý định Ngoài miền (OOD)
        Query-->>API: Trả về từ chối lịch sự (chống ảo giác)
        API-->>User: Phản hồi từ chối
    else Ý định Học phí / Bảng tính (STRUCTURED)
        Query->>Struct: Tra cứu bảng học phí
        Struct-->>Gen: Trả về dữ liệu bảng số học
    end
    Query->>Hybrid: Gửi câu truy vấn chuẩn hóa
    Hybrid->>Rerank: Top-K ứng viên (BM25 + FAISS qua RRF)
    Rerank-->>Gen: Top-N tài liệu đã tái xếp hạng
    Gen->>Gen: Ghép nối Context + Prompt chống ảo giác
    Gen-->>API: Sinh câu trả lời kèm trích dẫn (Citations)
    API-->>User: Trả lời hoàn chỉnh
```

## 3. Các phân hệ chính
1. **Module Tiền xử lý (TV1)**: Đọc file thô, làm sạch ký tự lạ tiếng Việt, phân đoạn theo Điều/Khoản quy chế, gán metadata cohort.
2. **Module Tìm kiếm & Tái xếp hạng (TV2)**: Kết hợp BM25 (từ khóa tiếng Việt) + FAISS (ngữ nghĩa đa ngôn ngữ E5/BGE) + Reciprocal Rank Fusion + BGE Reranker.
3. **Module Xử lý truy vấn & Sinh ngôn ngữ (TV3)**: Mở rộng từ viết tắt học vụ, phân loại intent, prompt chống bịa đặt, gọi Gemini/OpenAI API và trích dẫn chuẩn hóa.

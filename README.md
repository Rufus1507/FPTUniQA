# 🎓 FPT University Academic QA - Hệ Thống Hỏi Đáp Học Vụ (TMG301 - Tuần 1)

Hệ thống Hỏi - Đáp thông minh dành cho sinh viên Đại học FPT ứng dụng kỹ thuật **RAG (Retrieval-Augmented Generation)**. 

Bản phát hành này đại diện cho **Tuần 1 (Scope TV3)**: Khung sườn hoàn chỉnh (end-to-end skeleton) kết nối từ **Frontend (Streamlit)** -> **Backend API (FastAPI)** -> **RAG Pipeline (Query Normalizer + Mock Retriever + Context Builder + Strict Grounding Prompt + LLM Client + Citation Extraction)**.

---

## ⚡ Hướng Dẫn Chạy Thử Nhanh (Dành Cho TV1 & TV2)

### Bước 1: Cài đặt thư viện phụ thuộc

Sử dụng môi trường Python (>= 3.10) và công cụ quản lý gói `uv` (hoặc `pip` thông thường):

```bash
cd university-qa

# Cài đặt qua uv (khuyến nghị - cực nhanh):
uv sync

# Hoặc cài đặt qua pip truyền thống:
pip install -r requirements.txt
```

---

### Bước 2: Thiết lập biến môi trường

Tạo file `.env` từ file mẫu `.env.example`:

```bash
cp .env.example .env
```

Mở file `.env` và kiểm tra các thông số:
- `ANTHROPIC_API_KEY`: Điền API key Anthropic Claude của bạn (nếu chưa có key, hệ thống sẽ tự động bật **chế độ Fallback Mock LLM** để pipeline vẫn chạy thông suốt không bị gián đoạn).
- `API_BASE_URL`: Mặc định `http://localhost:8000`

---

### Bước 3: Khởi chạy Backend API (FastAPI)

Mở một cửa sổ Terminal và chạy:

```bash
# Khởi chạy server FastAPI:
uv run uvicorn api.main:app --reload

# Hoặc bằng uvicorn trực tiếp:
uvicorn api.main:app --reload
```

- Server sẽ hoạt động tại: `http://localhost:8000`
- Kiểm tra trạng thái máy chủ: `http://localhost:8000/healthz`
- Tài liệu API tương tác (Swagger UI): `http://localhost:8000/docs`

---

### Bước 4: Khởi chạy Giao diện Người Dùng (Streamlit)

Mở một cửa sổ Terminal thứ hai và chạy:

```bash
# Khởi chạy ứng dụng Streamlit:
uv run streamlit run frontend/app.py

# Hoặc bằng streamlit trực tiếp:
streamlit run frontend/app.py
```

- Ứng dụng sẽ tự động mở tại trình duyệt: `http://localhost:8501`
- Bạn có thể nhập các câu hỏi mẫu có sẵn trong sidebar hoặc câu hỏi như:
  > *"Điều kiện để không bị cảnh cáo học vụ là gì?"*
  > *"Điều kiện xét tốt nghiệp đại học như thế nào?"*

---

## 📂 Cấu Trúc Mã Nguồn TV3 Tuần 1

```
university-qa/
├── api/
│   ├── main.py                     # Khởi tạo FastAPI App và cấu hình CORS Middleware
│   ├── schemas.py                  # Pydantic models: QueryRequest, Citation, QueryResponse
│   └── routes/
│       ├── health.py               # Endpoint GET /healthz
│       └── qa.py                   # Endpoint POST /api/v1/query
│
├── frontend/
│   └── app.py                      # Giao diện Streamlit: input, loading spinner, expandable citations
│
├── src/university_qa/
│   ├── query/
│   │   ├── normalizer.py           # Chuẩn hóa Unicode NFC, khoảng trắng, lowercase
│   │   ├── rewriting.py            # TODO: Triển khai ở Tuần 5-6
│   │   └── intent.py               # TODO: Triển khai ở Tuần 5-6
│   │
│   ├── retrieval/
│   │   └── mock_retriever.py       # Dữ liệu giả lập FPTU tuân theo Retrieval Contract
│   │
│   ├── generation/
│   │   ├── prompt.py               # SYSTEM_PROMPT chống ảo giác & hàm build_prompt()
│   │   ├── context.py              # format_context() đánh số [Nguồn N] - title - category
│   │   ├── llm.py                  # LLMClient bọc Anthropic API và fallback an toàn
│   │   └── citation.py             # extract_citations() parse [Nguồn N] thành danh sách có cấu trúc
│   │
│   ├── pipeline/
│   │   └── rag_pipeline.py         # RAGPipeline điều phối luồng 7 bước hoàn chỉnh
│   │
│   └── utils/
│       ├── config.py               # Quản lý đối tượng cấu hình tập trung từ .env
│       └── logger.py               # Ghi log chuẩn định dạng JSONL vào logs/pipeline_events.jsonl
│
├── docs/
│   ├── retrieval_contract.md       # Hợp đồng interface bắt buộc cho TV2 Tuần 2
│   └── api.md                      # Đặc tả REST API
│
├── logs/                           # Lưu trữ log vận hành JSONL
├── requirements.txt                # Danh sách thư viện Python
├── .env.example                    # File cấu hình mẫu
└── pyproject.toml                  # Cấu hình dự án cho uv
```

---

## 📋 Ghi Chú Dành Cho TV2 (Tuần 2)

TV2 cần đọc kỹ tài liệu [docs/retrieval_contract.md](docs/retrieval_contract.md) trước khi bắt tay cài đặt tầng tìm kiếm thật.
Trong Tuần 2, TV2 chỉ cần thay thế hàm `retrieve` trong `src/university_qa/pipeline/rag_pipeline.py` mà không cần sửa đổi bất kỳ logic nào ở tầng API, Prompt hay Frontend!

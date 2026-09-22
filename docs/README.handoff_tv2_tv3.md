# 📦 BÁO CÁO BÀN GIAO DỰ ÁN — FPTUniQA
## Dành cho TV2 (Retrieval & Ranking) và TV3 (Semantic Parsing & Generation)

> **Tên đề tài:** *Context-Aware Vietnamese University Question Answering: A Hybrid Retrieval and Semantic Parsing Approach*  
> **Dự án:** Hệ thống hỏi đáp quy chế & thông tin tuyển sinh Đại học FPT (FPTUniQA)  
> **Người lập:** TV1 (Data & Knowledge Engineer)  
> **Ngày bàn giao:** 22/09/2026  
> **Trạng thái TV1:** ✅ **Hoàn thành toàn bộ giai đoạn Tuần 1–Tuần 2 (ETL Pipeline, Corpus, BM25 Baseline)**

---

## MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Vị trí lưu trữ sản phẩm trong repo](#2-vị-trí-lưu-trữ-sản-phẩm-trong-repo)
3. [Cấu trúc dự án chi tiết](#3-cấu-trúc-dự-án-chi-tiết)
4. [Những gì TV1 đã làm được](#4-những-gì-tv1-đã-làm-được)
5. [Pipeline ETL đã xây dựng](#5-pipeline-etl-đã-xây-dựng)
6. [Checkpoint — Trạng thái hiện tại](#6-checkpoint--trạng-thái-hiện-tại)
7. [Nhiệm vụ tiếp theo cho TV2 & TV3](#7-nhiệm-vụ-tiếp-theo-cho-tv2--tv3)

---

## 1. TỔNG QUAN DỰ ÁN

### Mục tiêu nghiên cứu
Xây dựng hệ thống hỏi đáp tiếng Việt cho sinh viên/thí sinh Đại học FPT, tích hợp **hai trụ cột kỹ thuật chính**:

| Trụ cột | Mô tả | Vai trò |
|---|---|---|
| **Hybrid Retrieval** | BM25 (sparse) + FAISS Dense + RRF + Cross-Encoder Reranker | TV2 chủ trì |
| **Semantic Parsing Routing** | NL → Structured Query → Tra cứu số học trực tiếp (không qua LLM generation) | TV3 chủ trì |

### Phân vai 3 thành viên

```
TV1 ── Data & Knowledge Engineer
        └── Thu thập, tiền xử lý, chunking, metadata, structured data, Ground Truth
TV2 ── Retrieval & Ranking Engineer
        └── FAISS Vector Store, RRF, Cross-Encoder Reranker, Retrieval Metrics
TV3 ── Backend, Semantic Parsing & UI Engineer
        └── FastAPI, Semantic Parser, Query Rewriting, LLM Generation, Streamlit UI
```

### Lộ trình 8 tuần (tổng thể)

| Tuần | Mục tiêu chính | Trạng thái |
|---|---|---|
| **Tuần 1** | Skeleton Pipeline, BM25 Baseline, Data Contract | ✅ **HOÀN THÀNH** |
| **Tuần 2** | Vertical Slice End-to-End Demo | ✅ **HOÀN THÀNH** (TV1 side) |
| **Tuần 3** | FAISS Dense Index, Semantic Parsing bản nháp | 🔲 TV2 + TV3 cần bắt tay |
| **Tuần 4** | Cross-Encoder Reranker, Semantic Parser hoàn thiện | 🔲 |
| **Tuần 5** | Context-Aware Query Rewriting, Multi-turn | 🔲 |
| **Tuần 6** | Guardrails/OOD, Freeze tính năng | 🔲 |
| **Tuần 7** | Ablation Study — đo 6 cấu hình, 5 nhóm metrics | 🔲 |
| **Tuần 8** | Báo cáo, bảo vệ, bài báo khoa học | 🔲 |

---

## 2. VỊ TRÍ LƯU TRỮ SẢN PHẨM TRONG REPO

### 2.1. Sản phẩm đầu ra của TV1 (sẵn sàng sử dụng ngay)

| Sản phẩm | Đường dẫn trong repo | Kích thước | Mô tả |
|---|---|---|---|
| **Corpus chính** (chunks sạch) | `data/processed/corpus.jsonl` | ~4.01 MB | **3,931 chunks** văn bản sạch, đầy đủ metadata, sẵn sàng cho BM25 & FAISS |
| **Bảng học phí cấu trúc** | `data/processed/structured_data.json` | ~115 KB | **190 records** học phí K22 của 5 campus, phục vụ Semantic Parsing Routing |
| **BM25 Index baseline** | `data/processed/bm25_index/bm25_index.pkl` | — | Chỉ mục BM25 đã build & verify thành công (3,931 docs) |
| **Metadata corpus** | `data/processed/metadata.json` | ~865 B | Thông tin tổng hợp về corpus |
| **Nhật ký crawl** | `data/raw/crawl_manifest.jsonl` | ~142 KB | 226 bản ghi thu thập (219 HTTP 200, 7 HTTP 404) |
| **Trang bị loại** | `data/interim/discarded_pages.jsonl` | ~1.48 KB | 8 trang bị lọc + lý do kỹ thuật |
| **Dữ liệu HTML gốc** | `data/raw/fpt_admission/html/` | ~5.71 MB | 170 tệp HTML thô, bảo toàn 100% nguyên vẹn |
| **Gói crawler thô** | `fptuniqa_raw_crawler_starter/fptuniqa_raw_data_20260921.zip` | ~5.99 MB | Gói dữ liệu gốc được bàn giao ban đầu |

> [!IMPORTANT]
> **Đường dẫn ưu tiên sử dụng:**
> - TV2 → `data/processed/corpus.jsonl` + `data/processed/bm25_index/`
> - TV3 → `data/processed/structured_data.json` + `data/processed/corpus.jsonl`

### 2.2. Tài liệu kỹ thuật (trong `docs/`)

| File | Nội dung |
|---|---|
| `docs/architecture.md` | Kiến trúc tổng thể hệ thống |
| `docs/data_schema.md` | Đặc tả Contract 1 — Schema tài liệu |
| `docs/retrieval_contract.md` | Contract 2 — Output của tầng Retrieval (TV2 → TV3) |
| `docs/generation_contract.md` | Contract 3 — Semantic Parsing Output Schema |
| `docs/api.md` | Đặc tả API FastAPI |
| `docs/evaluation.md` | Khung đánh giá và bộ metrics |
| `docs/tv1_data_audit_and_handoff_report.md` | Báo cáo kiểm kê dữ liệu chi tiết của TV1 |
| `docs/danh_gia_chat_luong_du_lieu.md` | Đánh giá SWOT chất lượng dữ liệu & pipeline |

---

## 3. CẤU TRÚC DỰ ÁN CHI TIẾT

```
FPTUniQA/
│
├── baocao.md                      # Kế hoạch lộ trình 8 tuần toàn dự án
├── nhiemvu.md                     # Phân công nhiệm vụ chi tiết
├── pyproject.toml                 # Cấu hình project Python (build, deps)
├── requirements.txt               # Dependencies Python
├── Makefile                       # Các lệnh tiện ích (build, test, run)
│
├── src/university_qa/             # ⭐ Mã nguồn chính (Python package)
│   │
│   ├── data/                      # ✅ [TV1 - HOÀN THÀNH] ETL Pipeline
│   │   ├── loader.py              #   Nạp HTML/TXT/MD + gắn manifest
│   │   ├── html_extractor.py      #   Bóc tách HTML (trafilatura + BS4)
│   │   ├── cleaner.py             #   Chuẩn hóa NFC, VND, khoảng trắng
│   │   ├── chunker.py             #   Chunking ngữ nghĩa bảo toàn bảng
│   │   ├── metadata.py            #   Gán metadata (doc_type, campus, cohort)
│   │   └── structured.py          #   Parser học phí → structured_data.json
│   │
│   ├── retrieval/                 # 🔲 [TV2 - CẦN PHÁT TRIỂN]
│   │   ├── bm25.py                #   ✅ BM25 retriever (đã có skeleton)
│   │   ├── dense.py               #   🔲 FAISS Dense Vector Store
│   │   ├── embedding.py           #   🔲 Embedding model (multilingual-e5)
│   │   ├── rrf.py                 #   🔲 Reciprocal Rank Fusion
│   │   └── retriever.py           #   🔲 Unified Retrieval interface
│   │
│   ├── reranking/                 # 🔲 [TV2 - CẦN PHÁT TRIỂN]
│   │   ├── cross_encoder.py       #   🔲 bge-reranker Cross-Encoder
│   │   └── reranker.py            #   🔲 Reranker interface
│   │
│   ├── query/                     # 🔲 [TV3 - CẦN PHÁT TRIỂN]
│   │   ├── intent.py              #   🔲 Semantic Parser (intent + slots)
│   │   ├── normalizer.py          #   🔲 Query normalizer
│   │   └── rewriting.py           #   🔲 Context-aware Query Rewriter
│   │
│   ├── generation/                # 🔲 [TV3 - CẦN PHÁT TRIỂN]
│   │   ├── llm.py                 #   🔲 LLM client (OpenAI/Gemini)
│   │   ├── prompt.py              #   🔲 Prompt templates & chống ảo giác
│   │   ├── context.py             #   🔲 Context assembly từ retrieved docs
│   │   └── citation.py            #   🔲 Citation enforcement
│   │
│   ├── pipeline/                  # 🔲 [TV3 - CẦN PHÁT TRIỂN]
│   │   ├── rag_pipeline.py        #   🔲 Full RAG Pipeline orchestration
│   │   └── conversational_pipeline.py  # 🔲 Multi-turn conversation
│   │
│   └── evaluation/                # 🔲 [TV1 hỗ trợ + TV2/TV3 chạy]
│       ├── retrieval_metrics.py   #   🔲 Recall@K, MRR
│       ├── answer_metrics.py      #   🔲 Faithfulness, Relevance
│       ├── hallucination.py       #   🔲 Hallucination detection
│       └── evaluator.py           #   🔲 Main evaluator runner
│
├── api/                           # 🔲 [TV3 - CẦN PHÁT TRIỂN]
│   ├── main.py                    #   FastAPI app entry point
│   ├── schemas.py                 #   Pydantic request/response schemas
│   └── routes/                    #   API route handlers
│
├── frontend/                      # 🔲 [TV3 - CẦN PHÁT TRIỂN]
│   └── app.py                     #   Streamlit UI app
│
├── scripts/                       # Utility scripts
│   ├── ingest_data.py             #   ✅ Script nạp & pipeline hoàn chỉnh
│   ├── run_pipeline.py            #   ✅ CLI chạy pipeline
│   ├── build_bm25.py              #   ✅ Build BM25 index
│   ├── build_faiss.py             #   🔲 Build FAISS index (TV2)
│   └── evaluate.py                #   🔲 Evaluation runner (TV2 + TV3)
│
├── data/
│   ├── raw/                       # ✅ Dữ liệu thô (KHÔNG chỉnh sửa)
│   │   ├── fpt_admission/html/    #   170 tệp HTML gốc từ daihoc.fpt.edu.vn
│   │   ├── crawl_manifest.jsonl   #   Nhật ký crawl 226 bản ghi
│   │   └── crawl_inventory.txt    #   Danh sách tệp crawl
│   │
│   ├── interim/                   # ✅ Dữ liệu trung gian
│   │   └── discarded_pages.jsonl  #   8 trang bị loại + lý do
│   │
│   ├── processed/                 # ✅ Sản phẩm chính (TV1 bàn giao)
│   │   ├── corpus.jsonl           #   3,931 chunks sạch ← ĐIỂM VÀO CHÍNH
│   │   ├── structured_data.json   #   190 records học phí ← CHO SEMANTIC PARSER
│   │   ├── metadata.json          #   Metadata tổng hợp corpus
│   │   └── bm25_index/            #   BM25 index đã build sẵn
│   │       └── bm25_index.pkl
│   │
│   └── evaluation/                # 🔲 Test set (TV1 đang xây dựng)
│
├── docs/                          # Tài liệu kỹ thuật
├── configs/                       # Cấu hình YAML/TOML
├── notebooks/                     # Jupyter notebooks thực nghiệm
├── experiments/                   # Log & kết quả thực nghiệm
├── tests/                         # Unit & integration tests
└── fptuniqa_raw_crawler_starter/  # Crawler độc lập (Scrapy/Playwright)
    └── fpt_raw_crawler/
        ├── fptuniqa_raw_data_20260921.zip   # Gói dữ liệu thô gốc
        └── scripts/                          # Scripts crawler
```

---

## 4. NHỮNG GÌ TV1 ĐÃ LÀM ĐƯỢC

### 4.1. Thu thập & Kiểm kê Dữ liệu Thô

- **Nguồn:** Website chính thức `daihoc.fpt.edu.vn`
- **Quy mô crawl:** 226 bản ghi trong `crawl_manifest.jsonl` (219 HTTP 200 ✅, 7 HTTP 404 ❌)
- **13/13 seed URLs thành công (100%)**
- **Thực tế thu được:** 170 tệp HTML thô, tổng ~5.71 MB
- **Dữ liệu gốc:** Bảo toàn 100% trong `data/raw/fpt_admission/html/` — **không bao giờ chỉnh sửa**

### 4.2. ETL Pipeline — Xử lý & Chuẩn hóa

**Kết quả đầu ra tổng hợp:**

| Chỉ số | Giá trị |
|---|---|
| Tổng chunks tạo ra | **3,931 chunks** |
| Dung lượng corpus | ~4.01 MB |
| Trang bị lọc | 8 trang rác (4.7%) |
| Tỷ lệ tuân thủ Contract 1 | **100% (3,931/3,931)** |
| Trường hợp thiếu field | **0 (zero)** |
| BM25 baseline | ✅ Build & verify thành công |
| Structured records học phí | **190 records (38 ngành × 5 campus)** |

### 4.3. Phân bố Corpus theo loại tài liệu

```
curriculum  (Chương trình đào tạo & ngành học)   1,676 chunks (42.6%)
admission   (Quy chế & Phương thức tuyển sinh)     658 chunks (16.7%)
scholarship (Học bổng & Điều kiện)                 581 chunks (14.8%)
general     (Thông tin trường & tin tức)            546 chunks (13.9%)
tuition     (Học phí & Chi phí đào tạo)             445 chunks (11.3%)
enrollment  (Thủ tục nhập học)                       25 chunks ( 0.6%)
```

### 4.4. Phân bố Corpus theo cơ sở đào tạo

```
all         (Áp dụng toàn quốc)      2,535 chunks (64.5%)
ho_chi_minh (TP. Hồ Chí Minh)         691 chunks (17.6%)
ha_noi      (Hà Nội)                   225 chunks ( 5.7%)
can_tho     (Cần Thơ)                  218 chunks ( 5.5%)
da_nang     (Đà Nẵng)                  131 chunks ( 3.3%)
quy_nhon    (Quy Nhơn)                 131 chunks ( 3.3%)
```

### 4.5. Chất lượng Dữ liệu Cấu trúc (Semantic Parsing Foundation)

File `data/processed/structured_data.json` chứa **190 bản ghi học phí K22** với cấu trúc cây:

```json
{
  "campus_name": {
    "major_name": {
      "kv1": 15480000,
      "other_kv": 22120000,
      "prep_english_levels": {
        "level_1": 8680000
      }
    }
  }
}
```

**Chính sách ưu đãi vùng miền đã được tích hợp sẵn:**

| Campus | Ưu đãi địa phương | Học kỳ chuyên ngành (KV1) | Học kỳ chuyên ngành (KV khác) |
|---|---|---|---|
| Hà Nội | 0% | 32,500,000 VNĐ | 32,500,000 VNĐ |
| TP. Hồ Chí Minh | 0% | 32,500,000 VNĐ | 32,500,000 VNĐ |
| Đà Nẵng | **−30%** | 15,480,000 VNĐ | 22,120,000 VNĐ |
| Cần Thơ | **−30%** | 15,480,000 VNĐ | 22,120,000 VNĐ |
| Quy Nhơn | **−50%** | 11,060,000 VNĐ | 15,800,000 VNĐ |

### 4.6. Xác minh BM25 Baseline (Kết quả thực nghiệm)

| Query mẫu | BM25 Score | Kết quả Top 1 |
|---|---|---|
| "Học phí ngành Trí tuệ nhân tạo campus Hà Nội khóa 2026" | **27.138** | ✅ Đúng chunk học phí AI HN |
| "Học bổng tìm kiếm nhân tài kỷ nguyên số" | **33.272** | ✅ Đúng văn bản học bổng |
| "Phương thức xét tuyển TopSchool" | **15.712** | ✅ Đúng văn bản tuyển sinh |
| "Chuẩn đầu ra tiếng Anh TOEIC" | **21.232** | ✅ Đúng văn bản chuẩn đầu ra |

### 4.7. Độ bao phủ tri thức — CÓ và CHƯA CÓ

**Đã có (chất lượng cao):**
- Quy chế Tuyển sinh K22/2026 (THPT, học bạ SchoolRank/TopSchool, thẳng, nước ngoài)
- Học bổng 2026 (Tìm kiếm nhân tài kỷ nguyên số, Tài năng, Khuyến học, Nữ CNTT)
- Học phí đầy đủ 5 campus + chính sách ưu đãi vùng miền
- Chương trình đào tạo (CNTT, QTKD, Truyền thông, Anh, Nhật, Hàn, Trung)
- Chuẩn đầu ra ngoại ngữ (CEFR C1/B2, JLPT N2, TopJ)

**Chưa có (cần thu thập thêm):**
- Quy chế đào tạo tín chỉ nội bộ (cảnh báo học vụ, thi lại, bảo lưu, chuyển ngành)
- Phí ký túc xá từng campus (Hòa Lạc, Quận 9, An Phú Thịnh...)
- Thủ tục nhập học chi tiết (chỉ có 25 chunks enrollment)
- Văn bản PDF pháp quy có số hiệu Quyết định Hiệu trưởng

---

## 5. PIPELINE ETL ĐÃ XÂY DỰNG

### 5.1. Sơ đồ luồng xử lý

```
[Website daihoc.fpt.edu.vn]
         |
         v  (Crawler - fptuniqa_raw_crawler_starter)
[data/raw/fpt_admission/html/]  <- 170 tệp HTML thô (BẢO TOÀN NGUYÊN VẸN)
[data/raw/crawl_manifest.jsonl] <- Nhật ký provenance
         |
         v  scripts/ingest_data.py / scripts/run_pipeline.py
+------------------------------------------------------------------+
|              ETL PIPELINE (src/university_qa/data/)              |
|                                                                  |
|  [1] loader.py                                                   |
|      - Nạp HTML/TXT/MD                                          |
|      - Gắn URL gốc, HTTP status, timestamp, doc_id             |
|         |                                                        |
|         v                                                        |
|  [2] html_extractor.py                                           |
|      - trafilatura (primary) + BeautifulSoup (fallback)         |
|      - Xóa: header/nav/footer WordPress, form wpcf7/ninja       |
|      - Giữ: bảng <table> học phí -> Markdown table             |
|      - Lọc trang rác < 80 từ -> discarded_pages.jsonl          |
|         |                                                        |
|         v                                                        |
|  [3] cleaner.py                                                  |
|      - Chuẩn hóa Unicode NFC (tiếng Việt dựng sẵn)            |
|      - normalize_vnd_amounts() (32.500.000 -> chuẩn hóa)      |
|      - Xóa khoảng trắng/ngắt dòng thừa                         |
|         |                                                        |
|         v                                                        |
|  [4] chunker.py                                                  |
|      - Heading-based Chunking (H1/H2/H3)                       |
|      - Semantic Window: ~800-1200 ký tự, overlap 150 ký tự     |
|      - Table-aware: không cắt giữa hàng bảng học phí           |
|      - Kế thừa tiêu đề vào field "title" của chunk             |
|         |                                                        |
|         v                                                        |
|  [5] metadata.py                                                 |
|      - Gán doc_type: curriculum/admission/scholarship/...       |
|      - Gán campus: all/ha_noi/ho_chi_minh/da_nang/...         |
|      - Gán cohort: K22/2026/All                                 |
|      - Gán effective_date nếu có                                |
|      - Tương thích kép: Contract 1 + Legacy TV2/TV3            |
|         |                                                        |
|         v                                                        |
|  [6] structured.py (chạy song song)                             |
|      - Parser học phí bảng HTML -> JSON cây                    |
|      - campus -> major -> {kv1, other_kv, prep_english}        |
|      - Tích hợp hằng số ưu đãi địa phương                      |
+----------------|----------------------------------+--------------+
                 |                                  |
                 v                                  v
[data/processed/corpus.jsonl]    [data/processed/structured_data.json]
   3,931 chunks sạch                  190 records học phí K22
   ~4.01 MB                           ~115 KB
         |
         v  scripts/build_bm25.py
[data/processed/bm25_index/bm25_index.pkl]
   BM25 Okapi index - 3,931 docs
   Đã verify 4 queries thực tế - score 15-33
```

### 5.2. Schema mỗi Chunk trong `corpus.jsonl` (Contract 1)

```json
{
  "id": "uuid-duy-nhat",
  "doc_id": "url_hoặc_filename_goc",
  "title": "Tiêu đề bài viết — Tiêu đề mục H2/H3",
  "text": "Nội dung đoạn văn bản sạch...",
  "source": "https://daihoc.fpt.edu.vn/...",
  "doc_type": "tuition | admission | scholarship | curriculum | enrollment | general",
  "campus": "all | ha_noi | ho_chi_minh | da_nang | can_tho | quy_nhon",
  "applies_to_cohort": "K22 | 2026 | All",
  "effective_date": "2026-01-01 | null",
  "metadata": {
    "word_count": 46,
    "char_count": 217,
    "has_table": true
  }
}
```

> [!IMPORTANT]
> **100% (3,931/3,931) chunks có đầy đủ tất cả các trường bắt buộc — ZERO missing fields.**

### 5.3. Interface Contracts giữa các thành viên

**Contract 2: TV2 → TV3 (Output của tầng Retrieval)**
```json
[
  {
    "doc_id": "tuition_ai_2026_001",
    "text": "Sinh viên khóa 2026 ngành Trí tuệ nhân tạo...",
    "score": 0.892,
    "source": "https://daihoc.fpt.edu.vn/...",
    "retrieval_strategy": "hybrid_rrf_reranked",
    "metadata": {
      "effective_date": "2026-01-01",
      "applies_to_cohort": ["2026"],
      "doc_type": "tuition",
      "campus": "ha_noi"
    }
  }
]
```

**Contract 3: Semantic Parsing Output (TV3 internal)**
```json
{
  "intent": "tuition_lookup",
  "slots": {
    "program": "AI",
    "campus": "ha_noi",
    "cohort": "2026",
    "metric": "tuition_per_semester"
  },
  "confidence": 0.94,
  "parser_method": "llm_structured_output",
  "fallback_used": false
}
```

---

## 6. CHECKPOINT — TRẠNG THÁI HIỆN TẠI

### Đã hoàn thành (TV1 — Grade A / 9.0/10)

- [x] Thu thập 170 tệp HTML từ `daihoc.fpt.edu.vn`
- [x] Xây dựng `html_extractor.py` (trafilatura + BS4, lọc WordPress rác)
- [x] Xây dựng `cleaner.py` (Unicode NFC, VND normalization)
- [x] Xây dựng `chunker.py` (semantic chunking, table-aware)
- [x] Xây dựng `metadata.py` (doc_type, campus, cohort tagging)
- [x] Xây dựng `structured.py` (parser học phí → JSON)
- [x] Tạo ra `data/processed/corpus.jsonl` — **3,931 chunks, Contract 1 = 100%**
- [x] Tạo ra `data/processed/structured_data.json` — **190 records học phí K22**
- [x] Build và verify `data/processed/bm25_index/bm25_index.pkl`
- [x] Ghi `data/interim/discarded_pages.jsonl` (8 trang bị lọc + lý do)
- [x] Viết scripts: `ingest_data.py`, `run_pipeline.py`, `build_bm25.py`

### TV2 cần làm (Tuần 3–4)

- [ ] Build FAISS Dense Vector Index (`scripts/build_faiss.py`, `retrieval/dense.py`)
  - Embedding model đề xuất: `intfloat/multilingual-e5-base` hoặc `bkai-foundation-models/vietnamese-bi-encoder`
- [ ] Triển khai Reciprocal Rank Fusion — RRF (`retrieval/rrf.py`)
- [ ] Tích hợp Metadata Pre-filtering theo `campus` + `doc_type`
- [ ] Build Cross-Encoder Reranker (`reranking/cross_encoder.py`)
  - Model đề xuất: `BAAI/bge-reranker-base`
- [ ] Đóng gói tầng retrieval thành API endpoint tuân thủ Contract 2
- [ ] Đo Recall@3, Recall@5, Recall@10, MRR trên test set

### TV3 cần làm (Tuần 3–4)

- [ ] Xây dựng Semantic Parser (`query/intent.py`)
  - Input: Câu hỏi tiếng Việt tự nhiên
  - Output: JSON theo Contract 3 (intent, slots, confidence)
  - Dùng OpenAI Function Calling hoặc Gemini structured output; Regex làm fallback
- [ ] Kết nối Structured Lookup `lookup_tuition(campus, major, kv)` từ `structured_data.json`
- [ ] Xây dựng Router: `intent == tuition_lookup` → Structured Lookup; còn lại → RAG
- [ ] Thiết lập FastAPI (`api/main.py`, `api/routes/`)
- [ ] Tích hợp LLM generation với prompt chống ảo giác (`generation/`)
- [ ] Xây dựng Streamlit UI (`frontend/app.py`)
- [ ] Triển khai Context-aware Query Rewriting (Tuần 5)

### TV1 sẽ làm thêm

- [ ] Xây dựng Ground Truth Test Set 150–250 câu hỏi (kèm nhãn intent + slots vàng)
- [ ] Crawl bổ sung: FAP portal (`fap.fpt.edu.vn`), dịch vụ sinh viên (`dichvu.fpt.edu.vn`)
- [ ] Crawl các phân hiệu: `hanoi.fpt.edu.vn`, `hcmuni.fpt.edu.vn`, `dnuni.fpt.edu.vn`...
- [ ] Crawl tài liệu PDF quy chế (Sổ tay sinh viên, quy chế thi, KTX)

---

## 7. NHIỆM VỤ TIẾP THEO CHO TV2 & TV3

### TV2 — Bắt đầu ngay (Tuần 3)

**Bước 1 — Nạp và kiểm tra corpus:**
```bash
python -c "
import json
with open('data/processed/corpus.jsonl') as f:
    docs = [json.loads(l) for l in f]
print(f'Tổng chunks: {len(docs)}')
print(f'Fields: {list(docs[0].keys())}')
"
```

**Bước 2 — Build FAISS index:**
```bash
python scripts/build_faiss.py \
  --corpus data/processed/corpus.jsonl \
  --model intfloat/multilingual-e5-base \
  --output data/processed/faiss_index/
```

**Bước 3 — Implement RRF trong `src/university_qa/retrieval/rrf.py`:**
```python
def reciprocal_rank_fusion(bm25_results, dense_results, k=60):
    """RRF score = sum(1 / (k + rank_i)) cho mỗi doc"""
    scores = {}
    for rank, doc in enumerate(bm25_results):
        scores[doc["doc_id"]] = scores.get(doc["doc_id"], 0) + 1/(k + rank + 1)
    for rank, doc in enumerate(dense_results):
        scores[doc["doc_id"]] = scores.get(doc["doc_id"], 0) + 1/(k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Bước 4 — Metadata Pre-filtering (tăng precision theo campus):**
```python
def filter_by_campus(query_campus: str, docs: list) -> list:
    """Chỉ trả về docs áp dụng cho campus được hỏi hoặc áp dụng toàn quốc"""
    return [d for d in docs if d["campus"] in [query_campus, "all"]]
```

### TV3 — Bắt đầu ngay (Tuần 3)

**Bước 1 — Load Structured Data và viết lookup function:**
```python
import json

with open("data/processed/structured_data.json") as f:
    TUITION_DB = json.load(f)

def lookup_tuition(campus: str, major: str, kv: str = "kv1") -> dict:
    """Tra cứu học phí trực tiếp — 100% chính xác, không qua LLM"""
    return TUITION_DB.get(campus, {}).get(major, {}).get(kv, None)
```

**Bước 2 — Semantic Parser dùng OpenAI Function Calling:**
```python
# src/university_qa/query/intent.py
PARSE_SCHEMA = {
    "name": "parse_query",
    "parameters": {
        "intent": {"enum": ["tuition_lookup", "scholarship_query",
                             "admission_query", "general_info", "out_of_domain"]},
        "slots": {
            "campus": {"enum": ["ha_noi", "ho_chi_minh", "da_nang",
                                 "can_tho", "quy_nhon", None]},
            "major": {"type": "string", "nullable": True},
            "cohort": {"enum": ["2026", None]},
            "metric": {"enum": ["tuition_per_semester", "prep_english", None]}
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    }
}
```

**Bước 3 — Router Logic trong `src/university_qa/pipeline/rag_pipeline.py`:**
```python
def route_and_answer(query: str, parsed: dict) -> dict:
    if parsed["intent"] == "tuition_lookup" and parsed["confidence"] > 0.85:
        # Structured Lookup — KHÔNG qua LLM, triệt tiêu ảo giác số liệu
        result = lookup_tuition(
            campus=parsed["slots"]["campus"],
            major=parsed["slots"]["major"]
        )
        return {"answer": format_tuition(result), "source": "structured_db",
                "hallucination_risk": 0}
    else:
        # RAG Pipeline — retrieval + LLM generation với citation
        docs = retrieve(query)
        return generate_with_citation(query, docs)
```

---

## PHỤ LỤC: ABLATION STUDY — 6 CẤU HÌNH CẦN ĐO Ở TUẦN 7

| # | Cấu hình Pipeline | Recall@5 | MRR | Faithfulness | OOD Rejection | Latency |
|---|---|---|---|---|---|---|
| 1 | BM25 Baseline | Chờ đo | Chờ đo | Chờ đo | Chờ đo | ~100–150ms |
| 2 | FAISS Only (Dense) | Chờ đo | Chờ đo | Chờ đo | Chờ đo | ~150–200ms |
| 3 | Hybrid (BM25 + FAISS) | Chờ đo | Chờ đo | Chờ đo | Chờ đo | ~200–250ms |
| 4 | Hybrid + RRF + Metadata Filter | Chờ đo | Chờ đo | Chờ đo | Chờ đo | ~250–320ms |
| 5 | Full (Reranker, **không** Semantic Parsing) | Chờ đo | Chờ đo | Chờ đo | Chờ đo | ~600–750ms |
| **6** | **Full + Semantic Parsing Routing** | Chờ đo | Chờ đo | Chờ đo | Chờ đo | Chờ đo |

> **Cấu hình 6 vs Cấu hình 5** = Bằng chứng thực nghiệm chứng minh đóng góp của "Semantic Parsing" trong tên đề tài.

### 5 Nhóm Metrics cần đo

| Nhóm | Metrics |
|---|---|
| **Retrieval** (TV2) | Recall@3, Recall@5, Recall@10, MRR |
| **Semantic Parsing** (TV3) | Intent Accuracy, Slot Accuracy, Exact Match, Fallback Rate |
| **Generation** (TV3) | Answer Faithfulness, Citation Correctness |
| **Safety & OOD** (TV3) | OOD Rejection Rate, Hallucination Rate |
| **System Performance** (All) | E2E Latency p50/p95, API Success Rate |

---

*Báo cáo lập bởi TV1 — Data & Knowledge Engineer | FPTUniQA Project | 22/09/2026*
*Tham chiếu: `baocao.md` | `docs/tv1_data_audit_and_handoff_report.md` | `docs/danh_gia_chat_luong_du_lieu.md`*

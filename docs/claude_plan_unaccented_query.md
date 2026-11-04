## Mục tiêu
Khôi phục dấu và chuẩn hóa truy vấn tiếng Việt không dấu bằng tài nguyên nội bộ (`EntityNormalizer`, từ điển học vụ và heuristic nhẹ), sau đó đưa truy vấn đã chuẩn hóa vào cả BM25 và Dense Retrieval. Giữ nguyên hành vi hiện tại đối với câu hỏi đã có dấu, không gọi thêm model và không thay đổi LLM 3B.

## Phân tích / Nguyên nhân gốc
- Chỉ mục BM25 chỉ chứa token có dấu, trong khi query không dấu không thể khớp `điều_kiện`, `sinh_viên`, `tốt_nghiệp`.
- `EntityNormalizer` đã nhận diện đúng entity và `slots_hint`, nhưng kết quả chưa được đưa trở lại pipeline truy vấn.
- Query normalizer hiện chỉ thực hiện `NFC`, không phục hồi dấu hoặc tạo biến thể truy vấn có dấu.
- Dense retrieval và cross-encoder vì vậy nhận nội dung không dấu, làm giảm semantic similarity và khiến RRF đưa các chunk không liên quan lên đầu.
- LLM chỉ phản ánh sai lệch của retriever, không phải nguyên nhân gốc.

## Các bước thực hiện

- Bước 1: Bổ sung bộ regression test cho query không dấu và query đã có dấu
  - File: `tests/normalization/test_query_normalizer.py`
  - Thay đổi cụ thể:
    - Thêm fixture:
      - `dieu kien de sinh vien duoc xet tot nghiep la gi`
      - `hoc phi nganh cntt khoa k21 la bao nhieu`
      - `sinh vien k18 can bao nhieu tin chi de di ojt`
    - Thêm các phiên bản có dấu tương ứng làm baseline.
    - Khẳng định pipeline cuối cùng trả về `doc_fpt_k21_0418` cho câu đầu tiên.
    - Khẳng định query có dấu không bị thêm token, đổi thứ tự hoặc suy giảm kết quả so với baseline.
  - Kiểm tra:
    ```bash
    pytest tests/normalization/test_query_normalizer.py -q
    ```

- Bước 2: Tạo lớp phục hồi dấu tiếng Việt theo lexicon, không phụ thuộc model ngoài
  - File: `src/FPTUniQA/normalization/accent.py`
  - Thay đổi cụ thể:
    - Tạo `AccentRestorer` với API:
      ```python
      restore(text: str) -> AccentRestoreResult
      ```
    - `AccentRestoreResult` tối thiểu gồm:
      ```python
      original_text: str
      restored_text: str
      replacements: list[AccentReplacement]
      ambiguous_tokens: list[str]
      ```
    - Xây dựng lexicon tra cứu từ:
      - Các entity và alias trong `EntityNormalizer`.
      - Các từ, cụm từ và từ khóa học vụ trong `data/dictionary/`.
    - Chuẩn hóa key tra cứu bằng cách bỏ dấu và hạ chữ thường.
    - Áp dụng longest-match, ưu tiên cụm dài trước từ đơn.
    - Với từ không có trong từ điển, dùng bảng quy tắc dấu tiếng Việt có sẵn trong module để khôi phục các trường hợp không mơ hồ.
    - Không tự chọn phương án mơ hồ nếu từ điển có nhiều candidate; giữ nguyên token và ghi nhận vào `ambiguous_tokens`.
    - Không gọi network, Ollama, embedding model hoặc LLM.
    - Giới hạn công việc bằng precomputed dictionary index, không duyệt toàn bộ corpus mỗi request.
  - Kiểm tra:
    ```bash
    pytest tests/normalization/test_accent_restorer.py -q
    ```
    Tiêu chí:
    - `dieu kien` → `điều kiện`
    - `sinh vien` → `sinh viên`
    - `duoc xet tot nghiep` → `được xét tốt nghiệp`
    - Query có dấu trả về nguyên văn sau Unicode normalization.

- Bước 3: Mở rộng `EntityNormalizer` để trả về cả canonical replacement và thông tin truy vấn
  - File: `src/FPTUniQA/normalization/engine.py`
  - Thay đổi cụ thể:
    - Thêm API:
      ```python
      analyze_with_spans(text: str) -> EntityAnalysisResult
      ```
    - `EntityAnalysisResult` phải chứa:
      ```python
      canonical_text: str
      entities: list[EntityMatch]
      replacements: list[EntityReplacement]
      slots_hint: dict[str, Any]
      ```
    - `EntityMatch` phải lưu:
      ```text
      source_text, canonical_text, start, end, entity_type, aliases
      ```
    - Với câu mẫu, kỳ vọng:
      - `sinh vien` → `Sinh viên`
      - `tot nghiep` → `Điều kiện tốt nghiệp`
      - `slots_hint["topic"] == "tot_nghiep"`
    - Giữ nguyên toàn bộ API hiện tại; không thay đổi hành vi của các caller cũ.
    - Không hard-code riêng câu hỏi mẫu; mọi kết quả phải đến từ entity/dictionary hiện có.
  - Kiểm tra:
    ```bash
    pytest tests/normalization/test_entity_normalizer.py -q
    ```

- Bước 4: Tích hợp phục hồi dấu và entity normalization vào query normalizer
  - File: `src/FPTUniQA/query/normalizer.py`
  - Thay đổi cụ thể:
    - Thêm dataclass:
      ```python
      @dataclass(frozen=True)
      class NormalizedQuery:
          original: str
          normalized: str
          retrieval_query: str
          is_unaccented: bool
          entity_expansion: tuple[str, ...]
          slots_hint: dict[str, Any]
      ```
    - Thêm API:
      ```python
      normalize_for_retrieval(text: str) -> NormalizedQuery
      ```
    - Pipeline:
      1. `unicodedata.normalize("NFC", text)`.
      2. Chuẩn hóa whitespace.
      3. Phát hiện query không dấu bằng cách kiểm tra dấu tiếng Việt trên các token chữ cái.
      4. Nếu query không dấu:
         - Gọi `AccentRestorer.restore()`.
         - Gọi `EntityNormalizer.analyze_with_spans()` trên query không dấu và trên query đã phục hồi dấu.
         - Thay các span bằng canonical entity.
         - Tạo `retrieval_query` từ query đã phục hồi dấu, có thể bổ sung canonical phrase chưa xuất hiện trong câu hỏi.
      5. Nếu query đã có dấu:
         - Vẫn chạy entity normalization để giữ hành vi hiện tại.
         - Không thêm alias, không thêm token và không tạo biến thể mới.
      6. Không thay đổi API `normalize()` hiện tại để tránh lỗi caller.
    - `retrieval_query` cho câu mẫu phải chứa được các cụm dạng:
      ```text
      điều kiện
      sinh viên
      được
      xét
      tốt nghiệp
      ```
      và canonical phrase:
      ```text
      Điều kiện tốt nghiệp
      ```
    - Loại bỏ canonical phrase trùng lặp và chuẩn hóa whitespace trước khi trả về.
  - Kiểm tra:
    ```bash
    pytest tests/normalization/test_query_normalizer.py tests/normalization/test_accent_restorer.py -q
    ```
    Tiêu chí:
    - `retrieval_query` của query không dấu có dấu và chứa canonical entity.
    - `retrieval_query` của query có dấu không dài hơn baseline và không có token trùng lặp.

- Bước 5: Đưa query đã chuẩn hóa vào BM25 mà không thay đổi chỉ mục hiện tại
  - File: `src/FPTUniQA/retrieval/bm25.py`
  - Thay đổi cụ thể:
    - Thêm hỗ trợ query có nhiều biến thể qua API:
      ```python
      search(query: str, top_k: int, query_variants: Sequence[str] | None = None)
      ```
    - Token hóa query không dấu theo thứ tự:
      1. Query đã phục hồi dấu.
      2. Canonical entity expansion.
      3. Nếu vẫn không khớp token chỉ mục, áp dụng accent-insensitive token mapping cho token đơn còn lại.
    - Không lowercase hoặc bỏ dấu trực tiếp token trong chỉ mục; giữ nguyên corpus và index hiện tại.
    - Không cộng điểm lặp cho cùng một token từ nhiều biến thể.
    - Với query đã có dấu, chỉ dùng một query variant để giữ nguyên hành vi scoring.
    - Nếu có nhiều variant, fuse kết quả bằng RRF nội bộ thay vì cộng điểm thô.
    - Giữ nguyên contract trả về top-k, score và metadata.
  - Kiểm tra:
    ```bash
    pytest tests/retrieval/test_bm25.py -q
    ```
    Tiêu chí:
    - Query không dấu có candidate thuộc `doc_fpt_k21_0418` trong top-k.
    - Query có dấu cho cùng candidate và không làm thay đổi thứ tự/score ngoài tolerance đã định nghĩa.
    - Không trả về chunk “Bài hát truyền thống FPT” trong top candidate cho câu về tốt nghiệp.

- Bước 6: Đưa cùng biến thể truy vấn chuẩn hóa vào Dense Retrieval và RRF
  - File: `src/FPTUniQA/retrieval/retriever.py`
  - Thay đổi cụ thể:
    - Thay việc truyền trực tiếp `clean_query` không dấu:
      ```python
      dense_results = self.dense_retriever.search(clean_query, ...)
      bm25_results = self.bm25.search(clean_query, ...)
      ```
      bằng pipeline sử dụng `NormalizedQuery`.
    - BM25 nhận:
      ```text
      normalized.retrieval_query
      normalized.entity_expansion
      ```
    - Dense retriever nhận `normalized.retrieval_query` làm query chính.
    - Nếu dense API hỗ trợ nhiều query, truyền:
      1. `normalized.retrieval_query`
      2. Các canonical phrase chưa có trong câu hỏi
    - Nếu dense API chỉ hỗ trợ một query, chỉ truyền `normalized.retrieval_query`; không gọi model nhiều lần.
    - Giữ nguyên công thức và trọng số RRF hiện tại.
    - Không lọc bỏ ứng viên BM25 chỉ vì dense score thấp; reranker phải tiếp tục nhận đủ candidate pool như trước.
    - Không thay đổi LLM, system prompt hoặc generation flow.
  - Kiểm tra:
    ```bash
    pytest tests/retrieval/test_retriever.py -q
    ```
    Tiêu chí:
    - `doc_fpt_k21_0418` vào top-k cuối cùng.
    - Chunk bài hát không còn chiếm vị trí top đầu cho câu hỏi về tốt nghiệp.
    - Query có dấu giữ nguyên candidate ranking baseline trong tolerance.

- Bước 7: Bổ sung đánh giá hồi quy trên ba nhóm câu hỏi nghiệp vụ
  - File: `tests/integration/test_unaccented_query_retrieval.py`
  - Thay đổi cụ thể:
    - Tạo bảng test gồm:
      - Câu tốt nghiệp không dấu → kỳ vọng chunk chứa “Điều kiện xét và công nhận tốt nghiệp”.
      - Câu học phí CNTT K21 không dấu → chunk chứa quy định học phí.
      - Câu OJT không dấu → chunk chứa điều kiện OJT.
      - Phiên bản có dấu của cả ba câu.
    - Ghi lại:
      - Top candidate trước rerank.
      - Candidate sau rerank.
      - Top-k intersection giữa query có dấu và không dấu.
      - Thời gian chuẩn hóa query.
    - Assert candidate đúng nằm trong top-k và chunk sai về bài hát không nằm ở vị trí đầu.
    - Không hard-code ID cho các chunk học phí/OJT nếu corpus thay đổi; xác định theo title/content hoặc fixture ID hiện có.
  - Kiểm tra:
    ```bash
    pytest tests/integration/test_unaccented_query_retrieval.py -q
    ```

- Bước 8: Gắn quan sát và chống hồi quy ở ranh giới normalizer
  - File: `src/FPTUniQA/query/normalizer.py`
  - Thay đổi cụ thể:
    - Ghi log ở mức debug/metric:
      - `query_has_vietnamese_accents`
      - `accent_replacement_count`
      - `entity_match_count`
      - `retrieval_query_length_delta`
      - `ambiguous_token_count`
    - Chỉ log số liệu và token đã chuẩn hóa theo chính sách hiện tại; không tự động ghi toàn bộ nội dung truy vấn nếu hệ thống không ghi truy vấn.
    - Thêm safeguard: nếu chuẩn hóa làm `retrieval_query` dài hơn giới hạn định nghĩa, chỉ giữ query gốc và entity canonical đã xác nhận.
    - Nếu không có entity match và phục hồi dấu không chắc chắn, dùng query gốc thay vì suy đoán mạo hiểm.
  - Kiểm tra:
    ```bash
    pytest tests/normalization tests/retrieval tests/integration/test_unaccented_query_retrieval.py -q
    ```

## Rủi ro & lưu ý
- **Khôi phục dấu có thể mơ hồ:** Không dùng bảng quy tắc để tự chọn dấu khi có nhiều phương án hợp lý; ưu tiên từ điển và giữ nguyên token mơ hồ.
- **Entity expansion quá rộng:** Chỉ thêm canonical phrase do `EntityNormalizer` xác nhận; không thêm toàn bộ alias của entity.
- **Câu hỏi có dấu bị thay đổi:** Query pipeline phải phân nhánh rõ ràng; với query đã có dấu, `retrieval_query` phải tương đương baseline.
- **Không nên thêm trường âm thanh vào chỉ mục:** Có thể gây nhiễu và làm thay đổi toàn bộ ranking của corpus hiện tại.
- **RRF chỉ giải quyết hợp nhất, không sửa truy vấn sai:** Việc chuẩn hóa phải hoàn tất trước khi BM25, Dense và reranker chạy.
- **Candidate pool:** Không giảm số candidate đưa sang reranker, tránh làm chunk đúng bị loại trước cross-encoder.
- **Độ trễ:** Lexicon phải được load một lần khi khởi tạo ứng dụng; mỗi request chỉ thực hiện lookup hash và chuẩn hóa câu hỏi.
- **Đo benchmark:** Nếu môi trường thực tế có quy ước latency riêng, kiểm tra p95 của normalization nằm dưới `5ms`; nếu không, báo cáo số đo thực tế thay vì tuyên bố đạt tuyệt đối.

## Lệnh kiểm thử cuối cùng
```bash
pytest tests/normalization \
  tests/retrieval \
  tests/integration/test_unaccented_query_retrieval.py \
  -q
```

Kiểm tra chất lượng tối thiểu:

```bash
pytest tests/integration/test_unaccented_query_retrieval.py \
  -q -m "unaccented and not slow"
```

## Việc KHÔNG được làm
- Không thay đổi, fine-tune hoặc thay thế LLM 3B qua Ollama.
- Không thay đổi system prompt để che giấu lỗi retrieval.
- Không gọi API dịch, API khôi phục dấu, embedding service hoặc model bên ngoài.
- Không reindex toàn bộ corpus chỉ để xử lý query không dấu.
- Không bỏ dấu toàn bộ token trong BM25 index.
- Không thêm toàn bộ 1108 alias vào mỗi query.
- Không hard-code mapping riêng cho ba câu hỏi mẫu.
- Không thay đổi công thức, trọng số RRF hoặc top-k hiện tại nếu không cần thiết.
- Không loại bỏ candidate BM25 chỉ vì Dense Retriever không tìm thấy.
- Không sử dụng route fallback sang LLM để sửa câu hỏi không dấu.
- Không thay đổi hành vi của API `normalize()` hiện tại.
- Không thực hiện `git push`.
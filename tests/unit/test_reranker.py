"""Kiểm thử đơn vị toàn diện cho module Reranker & CrossEncoderReranker."""

from FPTUniQA.reranking.cross_encoder import CrossEncoderReranker


def test_cross_encoder_reranker_ranking():
    reranker = CrossEncoderReranker(device="cpu")
    docs = [
        {"id": "doc_1", "title": "Thể thao", "text": "Đá bóng và bơi lội trong khuôn viên trường."},
        {"id": "doc_2", "title": "Tín chỉ học phần", "text": "Quy chế đăng ký tín chỉ cho sinh viên năm nhất."},
    ]
    query = "đăng ký tín chỉ sinh viên"
    reranked = reranker.rerank(query, docs, top_n=2)

    assert len(reranked) == 2
    # doc_2 có độ liên quan cao hơn về đăng ký tín chỉ
    assert reranked[0][0]["id"] == "doc_2"


def test_cross_encoder_score_normalization_and_contract2_bounds():
    reranker = CrossEncoderReranker(device="cpu")
    docs = [
        {"id": "doc_1", "title": "Học bổng", "text": "Học bổng tài năng dành cho tân sinh viên."},
        {"id": "doc_2", "title": "Học phí", "text": "Hạn nộp học phí học kỳ Fall."},
    ]
    query = "xét học bổng"
    reranked = reranker.rerank(query, docs, top_n=2)

    assert len(reranked) > 0
    for doc, score in reranked:
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0, f"Score vượt ra ngoài khoảng [0.0, 1.0]: {score}"


def test_cross_encoder_score_thresholding():
    reranker = CrossEncoderReranker(device="cpu")
    docs = [
        {"id": "doc_1", "title": "Món ăn", "text": "Cơm tấm sườn bì chả ở canteen."},
        {"id": "doc_2", "title": "Cảnh báo học vụ", "text": "Quy chế cảnh báo học vụ khi điểm dưới 1.0."},
    ]
    query = "cảnh báo học vụ và đình chỉ"

    # Không có threshold
    all_res = reranker.rerank(query, docs, top_n=2, score_threshold=0.0)
    assert len(all_res) == 2

    # Đặt threshold cao để lọc nhiễu
    filtered_res = reranker.rerank(query, docs, top_n=2, score_threshold=0.1)
    for doc, score in filtered_res:
        assert score >= 0.1
    # doc_1 về canteen là hoàn toàn irrelevant nên score rất thấp và bị filter ra
    doc_ids = [d["id"] for d, _ in filtered_res]
    assert "doc_2" in doc_ids


def test_cross_encoder_empty_inputs():
    reranker = CrossEncoderReranker(device="cpu")
    docs = [{"id": "doc_1", "title": "A", "text": "B"}]

    assert reranker.rerank("", docs) == []
    assert reranker.rerank("   ", docs) == []
    assert reranker.rerank(None, docs) == []
    assert reranker.rerank("câu hỏi", []) == []


def test_cross_encoder_fallback_dummy():
    reranker = CrossEncoderReranker(device="cpu")
    reranker._model = "dummy"

    docs = [
        {"id": "doc_1", "title": "Thể thao", "text": "Bóng đá và cầu lông."},
        {"id": "doc_2", "title": "Học phí", "text": "Học phí ngành Công nghệ thông tin."},
    ]
    query = "học phí công nghệ thông tin"
    results = reranker.rerank(query, docs, top_n=2)

    assert len(results) == 2
    assert results[0][0]["id"] == "doc_2"
    for _, score in results:
        assert 0.0 <= score <= 1.0


def test_cross_encoder_custom_config():
    reranker = CrossEncoderReranker(
        model_name="BAAI/bge-reranker-large",
        device="cpu",
        batch_size=8,
        score_threshold=0.25,
    )
    assert reranker.model_name == "BAAI/bge-reranker-large"
    assert reranker.device == "cpu"
    assert reranker.batch_size == 8
    assert reranker.score_threshold == 0.25


def test_cross_encoder_monotonic_normalization():
    """Kiểm tra tính đơn điệu và biên [0.0, 1.0] tuyệt đối của hàm chuẩn hóa điểm số."""
    raw_logits = [-3.0, -1.0, -0.01, 0.01, 1.0, 3.0]
    norm_scores = CrossEncoderReranker._normalize_scores(raw_logits)

    assert len(norm_scores) == len(raw_logits)
    for s in norm_scores:
        assert 0.0 <= s <= 1.0

    # Thứ tự phải tăng nghiêm ngặt (monotonic strictly increasing)
    for i in range(len(norm_scores) - 1):
        assert (
            norm_scores[i] < norm_scores[i + 1]
        ), f"Vi phạm tính đơn điệu: {norm_scores[i]} >= {norm_scores[i + 1]} tại index {i}"


def test_cross_encoder_content_field_fallback():
    """Kiểm tra hỗ trợ trường 'content' thay thế khi 'text' không tồn tại (Contract 2)."""
    reranker = CrossEncoderReranker(device="cpu")
    reranker._model = "dummy"

    docs = [
        {"id": "doc_1", "title": "Thể thao", "content": "Bóng đá và cầu lông."},
        {"id": "doc_2", "title": "Học phí", "content": "Học phí ngành Kỹ thuật phần mềm."},
    ]
    query = "kỹ thuật phần mềm"
    results = reranker.rerank(query, docs, top_n=2)

    assert len(results) == 2
    assert results[0][0]["id"] == "doc_2"
    assert results[0][1] > 0.0


def test_cross_encoder_invalid_documents_resilience():
    """Kiểm tra khả năng chịu lỗi khi danh sách documents chứa None hoặc phần tử rỗng."""
    reranker = CrossEncoderReranker(device="cpu")
    reranker._model = "dummy"

    docs = [None, {}, {"id": "doc_valid", "text": "Quy chế học vụ ĐH FPT"}]
    results = reranker.rerank("quy chế", docs, top_n=2)

    assert len(results) == 1
    assert results[0][0]["id"] == "doc_valid"

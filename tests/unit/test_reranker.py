"""Kiểm thử đơn vị cho module Reranker."""

from university_qa.reranking.cross_encoder import CrossEncoderReranker


def test_cross_encoder_reranker():
    reranker = CrossEncoderReranker()
    docs = [
        {"id": "doc_1", "title": "Thể thao", "text": "Đá bóng và bơi lội."},
        {"id": "doc_2", "title": "Tín chỉ học phần", "text": "Quy chế đăng ký tín chỉ cho sinh viên năm nhất."},
    ]
    query = "đăng ký tín chỉ sinh viên"
    reranked = reranker.rerank(query, docs, top_n=2)

    assert len(reranked) == 2
    # doc_2 có độ liên quan cao hơn về đăng ký tín chỉ
    assert reranked[0][0]["id"] == "doc_2"

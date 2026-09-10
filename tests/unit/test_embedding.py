"""Kiểm thử đơn vị cho module Embedding."""

from university_qa.retrieval.embedding import EmbeddingModel


def test_embedding_model():
    model = EmbeddingModel()
    texts = ["Xin chào sinh viên", "Quy chế đào tạo đại học"]
    embeddings = model.embed_documents(texts)
    assert embeddings.shape[0] == 2
    assert embeddings.shape[1] > 0

    query_emb = model.embed_query("tín chỉ")
    assert query_emb.shape[0] > 0

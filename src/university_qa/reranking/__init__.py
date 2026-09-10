"""Module xếp hạng lại kết quả truy xuất (Cross-Encoder Reranker). Phụ trách: TV2."""

from university_qa.reranking.cross_encoder import CrossEncoderReranker
from university_qa.reranking.reranker import BaseReranker

__all__ = ["BaseReranker", "CrossEncoderReranker"]

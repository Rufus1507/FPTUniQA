"""Dòng chảy RAG chuẩn cho truy vấn đơn. Phụ trách: TV2 + TV3."""

import sys
from typing import Any, Dict, List, Optional
from university_qa.data.structured import StructuredDataParser
from university_qa.generation.citation import CitationExtractor
from university_qa.generation.context import ContextBuilder
from university_qa.generation.llm import LLMClient
from university_qa.generation.prompt import PromptManager
from university_qa.query.intent import IntentClassifier, QueryIntent
from university_qa.query.normalizer import QueryNormalizer
from university_qa.reranking.cross_encoder import CrossEncoderReranker
from university_qa.retrieval.retriever import HybridRetriever
from university_qa.utils.config import load_config
from university_qa.utils.io import read_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("university_qa.rag_pipeline")


class RAGPipeline:
    """Pipeline RAG tích hợp đầy đủ các thành phần."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        llm_client: Optional[LLMClient] = None,
        structured_parser: Optional[StructuredDataParser] = None,
    ):
        self.config = config or load_config()
        self.normalizer = QueryNormalizer()
        self.intent_classifier = IntentClassifier()

        self.retriever = retriever or HybridRetriever()
        self.reranker = reranker or CrossEncoderReranker()
        self.llm_client = llm_client or LLMClient()
        self.context_builder = ContextBuilder()

        structured_path = self.config.get("data", {}).get(
            "structured_path", "data/processed/structured_data.json"
        )
        self.structured_parser = structured_parser or StructuredDataParser(structured_path)

    def load_corpus(self, corpus_path: Optional[str] = None) -> None:
        """Nạp corpus văn bản và lập chỉ mục cho bộ tìm kiếm."""
        path = corpus_path or self.config.get("data", {}).get(
            "corpus_path", "data/processed/corpus.jsonl"
        )
        docs = read_jsonl(path)
        logger.info(f"Đang lập chỉ mục {len(docs)} tài liệu từ {path}")
        self.retriever.build_index(docs)

    def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Thực thi toàn bộ luồng RAG cho một câu truy vấn."""
        # 1. Chuẩn hóa câu hỏi
        normalized_query = self.normalizer.normalize(query)
        logger.debug(f"Query gốc: {query} -> Chuẩn hóa: {normalized_query}")

        # 2. Phân loại ý định
        intent, confidence = self.intent_classifier.classify(normalized_query)
        logger.debug(f"Ý định: {intent} (độ tin cậy: {confidence:.2f})")

        # 3. Xử lý trường hợp Ngoài miền (OOD) - Chống ảo giác
        if intent == QueryIntent.OOD:
            return {
                "query": query,
                "normalized_query": normalized_query,
                "intent": intent.value,
                "answer": PromptManager.OOD_REJECTION_PROMPT,
                "retrieved_documents": [],
                "citations": [],
            }

        # 4. Tra cứu dữ liệu cấu trúc (Học phí / bảng tính) nếu có
        structured_matches = []
        if intent == QueryIntent.STRUCTURED:
            structured_matches = self.structured_parser.get_tuition_by_major(normalized_query)

        # 5. Tìm kiếm văn bản lai (Hybrid Retrieval: BM25 + FAISS)
        candidate_docs_with_scores = self.retriever.retrieve(
            query=normalized_query, top_k=top_k * 2
        )
        candidates = [doc for doc, _ in candidate_docs_with_scores]

        # 6. Tái xếp hạng bằng Cross-Encoder Reranker
        if candidates:
            reranked_docs_with_scores = self.reranker.rerank(
                query=normalized_query, documents=candidates, top_n=top_k
            )
            final_docs = [doc for doc, _ in reranked_docs_with_scores]
        else:
            final_docs = []

        # 7. Ghép ngữ cảnh
        context = self.context_builder.build_context(
            documents=final_docs, structured_info=structured_matches
        )

        # 8. Sinh câu trả lời qua LLM
        prompt = PromptManager.format_rag_prompt(query=query, context=context)
        llm_answer = self.llm_client.generate(
            prompt=prompt, system_instruction=PromptManager.SYSTEM_PROMPT
        )

        # 9. Trích xuất nguồn trích dẫn (Citations)
        citations = CitationExtractor.extract_from_answer_and_docs(llm_answer, final_docs)

        return {
            "query": query,
            "normalized_query": normalized_query,
            "intent": intent.value,
            "answer": llm_answer,
            "retrieved_documents": final_docs,
            "citations": citations,
        }


def main():
    """Hàm chạy dòng lệnh CLI."""
    pipeline = RAGPipeline()
    try:
        pipeline.load_corpus()
    except Exception as e:
        logger.warning(f"Chưa nạp corpus: {e}")

    query = sys.argv[1] if len(sys.argv) > 1 else "Sinh viên được đăng ký tối đa bao nhiêu tín chỉ?"
    print(f"\n[?] Câu hỏi: {query}")
    result = pipeline.run(query)
    print(f"\n[*] Trả lời:\n{result['answer']}")
    print(f"\n[*] Nguồn tham chiếu: {len(result['citations'])} tài liệu")


if __name__ == "__main__":
    main()

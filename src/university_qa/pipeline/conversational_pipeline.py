"""Luồng hội thoại đa lượt có nhớ ngữ cảnh (Conversational RAG). Phụ trách: TV2 + TV3."""

from typing import Any, Dict, List, Optional
from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.query.rewriting import QueryRewriter


class ConversationalRAGPipeline:
    """Quản lý luồng hỏi đáp đa lượt với lịch sử hội thoại."""

    def __init__(self, rag_pipeline: Optional[RAGPipeline] = None):
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.rewriter = QueryRewriter(llm_client=self.rag_pipeline.llm_client)
        self.history: List[Dict[str, str]] = []

    def chat(self, user_message: str) -> Dict[str, Any]:
        """Tiếp nhận tin nhắn mới trong chuỗi hội thoại."""
        # Viết lại câu hỏi nếu có ngữ cảnh trước đó
        standalone_query = self.rewriter.rewrite(user_message, self.history)

        # Chạy pipeline RAG chuẩn với câu hỏi độc lập
        result = self.rag_pipeline.run(standalone_query)

        # Lưu lại lịch sử lượt chat
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": result["answer"]})

        result["original_user_message"] = user_message
        result["standalone_query"] = standalone_query
        return result

    def clear_history(self) -> None:
        """Xóa lịch sử trò chuyện."""
        self.history = []

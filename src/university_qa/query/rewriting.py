"""Mở rộng câu hỏi theo ngữ cảnh và lịch sử hội thoại. Phụ trách: TV3."""

from typing import Dict, List, Optional


class QueryRewriter:
    """Tái tạo câu truy vấn độc lập (standalone query) từ lịch sử hội thoại."""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def rewrite(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Nếu có lịch sử hội thoại, giải quyết đại từ thay thế và ngữ cảnh bị thiếu."""
        if not history or len(history) == 0:
            return query

        # Nếu có LLM client kết nối
        if self.llm_client and hasattr(self.llm_client, "generate"):
            prompt = (
                "Cho lịch sử hội thoại và câu hỏi mới của sinh viên. "
                "Hãy viết lại câu hỏi mới thành một câu hỏi độc lập đầy đủ chủ ngữ, "
                "không dùng đại từ thay thế, giữ nguyên ngôn ngữ tiếng Việt.\n\n"
                f"Lịch sử:\n{history}\n\n"
                f"Câu hỏi: {query}\n\n"
                "Câu hỏi hoàn chỉnh:"
            )
            try:
                rewritten = self.llm_client.generate(prompt)
                return rewritten.strip()
            except Exception:
                pass

        # Heuristic đơn giản: Nối thực thể gần nhất nếu câu hỏi quá ngắn (ví dụ: 'còn học phí thì sao?')
        last_turn = history[-1]
        if any(w in query.lower() for w in ["còn", "thế còn", "vậy", "nó", "đó", "ngành đó"]):
            return f"{query} (trong ngữ cảnh: {last_turn.get('content', '')[:60]})"

        return query

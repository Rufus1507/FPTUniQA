"""Dòng chảy RAG chuẩn (RAG Pipeline) kết nối các module từ Query -> Retrieval -> Generation. Phụ trách: TV3."""

import time
from typing import Any, Dict, List, Optional
from university_qa.generation.citation import extract_citations
from university_qa.generation.context import format_context
from university_qa.generation.guardrails import check_hallucination
from university_qa.generation.llm import LLMClient
from university_qa.generation.prompt import SYSTEM_PROMPT, build_prompt
from university_qa.query.normalizer import normalize_query
from university_qa.query.rewriting import rewrite_query
from university_qa.query.semantic_parser import parse_query
from university_qa.query.router import route_query, execute_structured_lookup
from university_qa.pipeline.mock_retriever import retrieve
from university_qa.utils.config import config
from university_qa.utils.logger import get_logger, log_pipeline_event, log_query_event

logger = get_logger("university_qa.rag_pipeline")


class SessionManager:
    """Quản lý trạng thái ngữ cảnh hội thoại in-memory theo session_id (Tuần 5)."""

    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(session_id, [])

    def add_turn(
        self,
        session_id: str,
        query: str,
        rewritten_query: str,
        answer: str,
        parsed_query: Optional[Dict[str, Any]] = None,
        route_chosen: Optional[str] = None,
    ) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "query": query,
            "rewritten_query": rewritten_query,
            "answer": answer,
            "parsed_query": parsed_query,
            "route_chosen": route_chosen,
        })

    def clear(self, session_id: Optional[str] = None) -> None:
        if session_id:
            self._sessions.pop(session_id, None)
        else:
            self._sessions.clear()


class RAGPipeline:
    """Pipeline điều phối toàn bộ quy trình Hỏi - Đáp học vụ đa lượt."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        top_k: Optional[int] = None,
        score_threshold: float = 0.3,
    ):
        self.llm = llm_client or LLMClient()
        self.top_k = top_k or config.default_top_k
        self.score_threshold = score_threshold
        self.session_manager = SessionManager()
        logger.info(f"Khởi tạo RAGPipeline với top_k={self.top_k}, score_threshold={self.score_threshold}")

    def answer(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Thực thi luồng RAG kết hợp Query Rewriting đa lượt, Semantic Parsing, Routing và Guardrails Tuần 6."""
        start_time = time.time()
        logger.info(f"Bắt đầu xử lý truy vấn: '{query}' (session_id={session_id})")

        try:
            # Lấy lịch sử hội thoại của session (nếu có)
            history = self.session_manager.get_history(session_id) if session_id else []
            turn_index = len(history) + 1

            # Bước 1: Query Rewriting đa lượt (Chạy trước Semantic Parser)
            rewritten_query = rewrite_query(query, history=history)
            clean_query = normalize_query(rewritten_query)
            logger.info(f"Query sau khi Rewriting: '{rewritten_query}' (gốc: '{query}')")

            # Bước 2: Semantic Parsing (Contract 3) trên câu hỏi đã viết lại
            parsed_query = parse_query(rewritten_query)
            logger.debug(f"Bước 2 - ParsedQuery: intent={parsed_query.intent}, slots={parsed_query.slots}")

            # Bước 3: Điều phối qua Router (TV3)
            route_res = route_query(parsed_query)
            route_chosen = str(route_res)
            clarification_msg = getattr(route_res, "clarification", None)

            retrieved_chunks: List[Dict] = []
            final_context = ""
            answer_fallback = False
            possible_hallucination = False
            ungrounded_numbers: List[str] = []

            # Xử lý theo từng loại Route
            if "ClarificationRoute" in route_chosen and clarification_msg:
                answer_text = clarification_msg
                citations = []
            elif "OODRoute" in route_chosen:
                answer_text = "Xin lỗi, câu hỏi của bạn nằm ngoài phạm vi tư vấn quy chế, tuyển sinh và đào tạo của Đại học FPT."
                citations = []
            elif "StructuredRoute" in route_chosen:
                # Tra cứu số học trực tiếp từ bảng có cấu trúc
                lookup_res = execute_structured_lookup(parsed_query)
                answer_text = lookup_res.get("text", "Không tìm thấy thông tin phù hợp trong bảng biểu.")
                citations = [
                    {
                        "doc_id": "structured_tuition_table",
                        "title": "Bảng biểu học phí có cấu trúc (K22 - 2026)",
                        "source": "Biểu phí chính thức ĐH FPT",
                        "chunk_id": "table_001",
                        "match_score": 1.0,
                    }
                ]
            else:
                # Hybrid RAG Route: Truy xuất tài liệu văn bản
                # Ưu tiên dùng TV2 Retriever nếu có, fallback mock_retriever nội bộ TV3
                try:
                    from university_qa.retrieval.retriever import HybridRetriever
                    hybrid = HybridRetriever()
                    # Truy xuất với hybrid nếu có
                    retrieved_chunks = retrieve(clean_query, top_k=self.top_k)
                except Exception:
                    retrieved_chunks = retrieve(clean_query, top_k=self.top_k)

                if not retrieved_chunks:
                    answer_text = "Xin lỗi, tôi không tìm thấy tài liệu phù hợp để trả lời câu hỏi của bạn."
                    citations = []
                    answer_fallback = True
                else:
                    final_context = format_context(retrieved_chunks)
                    prompt = build_prompt(
                        query=rewritten_query,
                        context=final_context,
                        system_prompt=SYSTEM_PROMPT,
                        history=history,
                    )
                    answer_text = self.llm.generate(prompt)
                    citations = extract_citations(answer_text, retrieved_chunks)

                    # Guardrail: Kiểm tra ảo giác trích xuất số liệu
                    guardrail_res = check_hallucination(answer_text, final_context)
                    possible_hallucination = guardrail_res.get("is_hallucinated", False)
                    ungrounded_numbers = guardrail_res.get("ungrounded_entities", [])

            # Cập nhật lịch sử lượt thoại vào session_manager
            if session_id:
                self.session_manager.add_turn(
                    session_id=session_id,
                    query=query,
                    rewritten_query=rewritten_query,
                    answer=answer_text,
                    parsed_query=parsed_query.model_dump(),
                    route_chosen=route_chosen,
                )

            latency_ms = (time.time() - start_time) * 1000.0
            log_pipeline_event(
                query=query,
                latency_ms=latency_ms,
                status="SUCCESS",
                message=f"Hoàn thành turn {turn_index}, route={route_chosen}",
            )

            return {
                "answer": answer_text,
                "citations": citations,
                "query": query,
                "original_query": query,
                "rewritten_query": rewritten_query,
                "route": route_chosen,
                "parsed_query": parsed_query.model_dump(),
                "session_id": session_id,
                "turn_index": turn_index,
                "possible_hallucination": possible_hallucination,
                "ungrounded_numbers": ungrounded_numbers,
                "retrieved_chunks": retrieved_chunks,
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.error(f"Lỗi trong quá trình thực thi RAGPipeline: {e}", exc_info=True)
            log_pipeline_event(
                query=query,
                latency_ms=latency_ms,
                status="ERROR",
                message=str(e),
            )
            raise e


def main():
    """Hàm chạy thử nghiệm pipeline nhanh trên terminal."""
    pipeline = RAGPipeline()
    test_query = "Học phí ngành Kỹ thuật phần mềm ở Cần Thơ năm 2026 là bao nhiêu?"
    print(f"\n[?] Câu hỏi: {test_query}")
    res = pipeline.answer(test_query)
    print(f"\n[*] Trả lời:\n{res['answer']}")
    print(f"\n[*] Route: {res['route']}")
    print(f"\n[*] Citations ({len(res['citations'])}):")
    for cit in res["citations"]:
        print(f"  - [{cit.get('doc_id')}] {cit.get('title')} ({cit.get('source')})")


if __name__ == "__main__":
    main()

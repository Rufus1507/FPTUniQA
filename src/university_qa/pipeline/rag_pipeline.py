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
# Nhập hàm retrieve từ mock_retriever nội bộ TV3 trong pipeline
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

            # Nhánh 0: Độ tin cậy thấp (Guardrail an toàn Tuần 6 - confidence < 0.5)
            if route_chosen == "uncertain":
                answer_text = clarification_msg or "Hệ thống chưa chắc chắn về câu hỏi này (độ tin cậy phân tích thấp). Vui lòng diễn đạt rõ hơn hoặc cung cấp thêm thông tin học vụ cụ thể."
                final_context = ""
                citations = []
                answer_fallback = True

            # Nhánh 1: Structured Lookup (Tra cứu trực tiếp biểu phí - Zero Hallucination)
            elif route_chosen == "structured_lookup":
                lookup_res = execute_structured_lookup(parsed_query.slots)
                answer_text = lookup_res["answer"]
                final_context = str(lookup_res.get("data") or "")
                if lookup_res.get("found"):
                    citations = [{
                        "doc_id": "MOCK_TUITION_TABLE",
                        "title": "Biểu phí tuyển sinh ĐH FPT",
                        "source": lookup_res.get("source", "Biểu phí tuyển sinh ĐH FPT"),
                    }]
                    retrieved_chunks = [lookup_res["data"]] if lookup_res.get("data") else []
                else:
                    citations = []
                    answer_fallback = True

            # Nhánh 2: Hỏi làm rõ thông tin thiếu (Clarification)
            elif route_chosen == "clarification":
                answer_text = clarification_msg or "Vui lòng cung cấp thêm thông tin để tôi có thể hỗ trợ bạn chính xác nhất."
                final_context = ""
                citations = []
                answer_fallback = False

            # Nhánh 3: Ngoài phạm vi (OOD)
            elif route_chosen == "ood":
                answer_text = "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu hiện có."
                final_context = ""
                citations = []
                answer_fallback = True

            # Nhánh 4: RAG Pipeline (Tra cứu quy chế qua mock_retriever)
            else:
                retrieved_chunks = retrieve(
                    clean_query,
                    top_k=self.top_k,
                    score_threshold=self.score_threshold,
                    parsed_query=parsed_query,
                )
                logger.debug(f"Đã truy xuất {len(retrieved_chunks)} chunks tài liệu đạt ngưỡng {self.score_threshold}")

                if not retrieved_chunks:
                    logger.warning(f"Kích hoạt Answer Fallback (intent={parsed_query.intent}, retrieved_count=0)")
                    answer_fallback = True
                    answer_text = "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu hiện có."
                    final_context = ""
                    citations = []
                else:
                    answer_fallback = False
                    context_text = format_context(retrieved_chunks)
                    final_context = context_text
                    user_prompt = build_prompt(query=clean_query, context_chunks=retrieved_chunks)
                    answer_text = self.llm.generate(
                        system_prompt=SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                    )
                    citations = extract_citations(answer=answer_text, context_chunks=retrieved_chunks)

                    # Guardrail hậu kỳ: Kiểm tra ảo giác số liệu không có trong context (Tuần 6)
                    hallucination_check = check_hallucination(answer=answer_text, context=context_text)
                    possible_hallucination = hallucination_check["possible_hallucination"]
                    ungrounded_numbers = hallucination_check["ungrounded_numbers"]
                    if possible_hallucination:
                        logger.warning(f"Guardrail cảnh báo: Số liệu có thể bị ảo giác trong câu trả lời: {ungrounded_numbers}")

            # Lưu lượt hội thoại vào session_manager
            if session_id:
                self.session_manager.add_turn(
                    session_id=session_id,
                    query=query,
                    rewritten_query=rewritten_query,
                    answer=answer_text,
                    parsed_query=parsed_query.model_dump(),
                    route_chosen=route_chosen,
                )

            # Đo lường thời gian thực thi (latency)
            latency_ms = (time.time() - start_time) * 1000.0

            # Ghi Structured Log đầy đủ 7 trường theo đúng kế hoạch gốc kèm cờ Guardrail
            log_query_event(
                original_query=query,
                rewritten_query=rewritten_query,
                parsed_query=parsed_query.model_dump(),
                retrieved_docs=retrieved_chunks,
                reranked_docs=None,  # Ghi chú rõ: chưa có TV2 (reranker thật)
                final_context=final_context,
                citations=citations,
                answer=answer_text,
                route_chosen=route_chosen,
                answer_fallback=answer_fallback,
                possible_hallucination=possible_hallucination,
                ungrounded_numbers=ungrounded_numbers,
                session_id=session_id,
                turn_index=turn_index,
                latency_ms=latency_ms,
            )

            # Ghi log sự kiện hoàn thành dạng JSONL
            log_pipeline_event(
                query=query,
                latency_ms=latency_ms,
                status="SUCCESS",
                extra={
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "rewritten_query": rewritten_query,
                    "route_chosen": route_chosen,
                    "retrieved_count": len(retrieved_chunks),
                    "citations_count": len(citations),
                    "answer_fallback": answer_fallback,
                    "possible_hallucination": possible_hallucination,
                    "ungrounded_numbers": ungrounded_numbers,
                },
            )
            logger.info(f"Hoàn thành truy vấn trong {latency_ms:.2f}ms (route: {route_chosen}, hallucination: {possible_hallucination})")

            # Bước 7: Trả về kết quả hoàn chỉnh
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
    test_query = "Điều kiện để không bị cảnh cáo học vụ là gì?"
    print(f"\n[?] Câu hỏi: {test_query}")
    res = pipeline.answer(test_query)
    print(f"\n[*] Trả lời:\n{res['answer']}")
    print(f"\n[*] Citations ({len(res['citations'])}):")
    for cit in res["citations"]:
        print(f"  - [{cit['doc_id']}] {cit['title']} ({cit['source']})")


if __name__ == "__main__":
    main()

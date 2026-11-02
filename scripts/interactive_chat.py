"""Giao diện Terminal tương tác trực tiếp (Interactive Chat) với hệ thống FPTUniQA.
Cho phép đặt câu hỏi liên tục, hỗ trợ đa lượt (multi-turn memory) và hiển thị chi tiết câu trả lời, route, citations.
"""

import sys
import uuid
from FPTUniQA.pipeline.rag_pipeline import RAGPipeline


def main():
    print("=" * 70)
    print("🎓 CHƯƠNG TRÌNH HỎI ĐÁP QUY CHẾ VÀ ĐÀO TẠO ĐẠI HỌC FPT (FPTUniQA)")
    print("=" * 70)
    print("Đang khởi tạo hệ thống và nạp chỉ mục...")
    
    pipeline = RAGPipeline(use_mock_fallback=False)
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    print("\n✅ Hệ thống đã sẵn sàng!")
    print("💡 Mẹo sử dụng:")
    print("   - Nhập câu hỏi tự nhiên bằng tiếng Việt.")
    print("   - Hệ thống tự nhớ ngữ cảnh các câu trước (hỏi 'môn này', 'kỳ mấy'...).")
    print("   - Gõ '/new' để bắt đầu phiên hội thoại mới.")
    print("   - Gõ '/exit' hoặc '/quit' để thoát.")
    print("-" * 70)

    turn = 1
    while True:
        try:
            prompt = f"\n[Lượt {turn}] Bạn: "
            query = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nĐã thoát chương trình. Tạm biệt!")
            break

        if not query:
            continue

        if query.lower() in ["/exit", "/quit", "exit", "quit"]:
            print("\nĐã thoát chương trình. Tạm biệt!")
            break

        if query.lower() == "/new":
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            turn = 1
            print("\n🔄 Đã tạo phiên hội thoại mới (xóa lịch sử cũ).")
            continue

        print("⏳ Đang tra cứu và xử lý...", end="\r", flush=True)
        res = pipeline.answer(query, session_id=session_id)
        print(" " * 40, end="\r")  # Xóa dòng đang xử lý

        ans = res.get("answer", "")
        route = res.get("route", "unknown")
        rewritten = res.get("rewritten_query")

        print(f"\n🤖 FPTUniQA (Route: {route}):")
        if rewritten and rewritten != query:
            print(f"   [Query Rewritten: '{rewritten}']")
        print(ans)

        citations = res.get("citations", [])
        if citations:
            print("\n📚 Nguồn trích dẫn:")
            for cit in citations:
                doc_id = cit.get("doc_id", "")
                title = cit.get("title", "")
                print(f"   - [{doc_id}] {title}")

        print("-" * 70)
        turn += 1


if __name__ == "__main__":
    main()

"""Ứng dụng giao diện người dùng Streamlit hoàn thiện cho hệ thống RAG hỏi đáp học vụ FPTU. Phụ trách: TV3.

Tính năng:
1. Trạng thái loading rõ ràng khi gọi API (st.spinner).
2. Tách biệt hoàn toàn 2 khối hiển thị:
   - Khối 1: [📝 Câu trả lời] kèm thông tin Route và Query sau Rewriting (nếu có).
   - Khối 2: [📚 Căn cứ quy chế & Nguồn trích dẫn] hiển thị danh sách trích dẫn độc lập.
3. Hỗ trợ phiên hội thoại đa lượt (Multi-turn session) thông qua session_id.
"""

import os
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv

# Nạp biến môi trường
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="FPTU Academic QA - Trợ lý Học vụ",
    page_icon="🎓",
    layout="centered",
)

# Khởi tạo session_id cho hội thoại đa lượt nếu chưa có
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Header & Tiêu đề chính
st.title("🎓 Trợ Lý Hỏi Đáp Học Vụ ĐH FPT")
st.caption("Hệ thống RAG giải đáp quy chế, học phí, học bổng và điều kiện tốt nghiệp — TV3 (Tuần 6 Freeze)")

# Ô nhập câu hỏi của người dùng
query_text = st.text_area(
    label="Nhập câu hỏi học vụ của bạn:",
    placeholder="Ví dụ: Học phí ngành AI khoá 2026 là bao nhiêu? hoặc Còn năm 2023 thì sao?",
    height=90,
    key="current_user_query",
)

# Nút gửi câu hỏi và nút xóa lịch sử
col1, col2 = st.columns([2, 3])
with col1:
    submit_button = st.button("🚀 Gửi câu hỏi", type="primary", use_container_width=True)
with col2:
    if st.button("🔄 Tạo phiên hội thoại mới", use_container_width=True):
        st.session_state["session_id"] = str(uuid.uuid4())[:8]
        st.session_state["messages"] = []
        st.rerun()

st.caption(f"Mã phiên làm việc hiện tại: `{st.session_state['session_id']}`")

if submit_button:
    clean_query = query_text.strip()
    if not clean_query:
        st.warning("⚠️ Vui lòng nhập nội dung câu hỏi trước khi gửi.")
    else:
        # 1. Trạng thái Loading rõ ràng khi đang gọi API Backend
        with st.spinner("⏳ Đang tra cứu quy chế và tổng hợp câu trả lời từ AI..."):
            endpoint = f"{API_BASE_URL}/api/v1/query"
            try:
                payload = {
                    "query": clean_query,
                    "session_id": st.session_state["session_id"],
                }
                response = requests.post(url=endpoint, json=payload, timeout=45)

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])
                    route = data.get("route", "rag_pipeline")
                    rewritten = data.get("rewritten_query", clean_query)
                    possible_hallucination = data.get("possible_hallucination", False)

                    # Lưu vào danh sách tin nhắn hiển thị
                    st.session_state["messages"].append({
                        "query": clean_query,
                        "rewritten": rewritten,
                        "answer": answer,
                        "citations": citations,
                        "route": route,
                        "possible_hallucination": possible_hallucination,
                    })

                else:
                    st.error(
                        f"❌ Máy chủ trả về mã lỗi HTTP {response.status_code}. "
                        f"Chi tiết: {response.text}"
                    )

            except requests.exceptions.ConnectionError:
                st.error(
                    f"⚠️ Không thể kết nối đến Backend API tại `{API_BASE_URL}`. "
                    f"Vui lòng đảm bảo bạn đã khởi động server FastAPI: `uvicorn api.main:app --reload`."
                )
            except requests.exceptions.Timeout:
                st.error("⏳ Quá thời gian chờ phản hồi từ máy chủ. Vui lòng thử lại sau.")
            except Exception as e:
                st.error(f"⚠️ Đã xảy ra lỗi không mong muốn: {str(e)}")

# Hiển thị lịch sử các câu hỏi và câu trả lời trong phiên
if st.session_state["messages"]:
    st.markdown("---")
    for msg_idx, msg in enumerate(reversed(st.session_state["messages"]), start=1):
        # Hiển thị câu hỏi của sinh viên
        st.markdown(f"#### 👤 Câu hỏi: *\"{msg['query']}\"*")

        # Hiển thị câu hỏi viết lại nếu có sự khác biệt (Đa lượt)
        if msg.get("rewritten") and msg["rewritten"] != msg["query"]:
            st.info(f"💡 **Câu hỏi đã làm rõ ngữ cảnh:** *\"{msg['rewritten']}\"*")

        # KHỐI 1: TÁCH RIÊNG HOÀN TOÀN KHỐI CÂU TRẢ LỜI
        with st.container(border=True):
            st.markdown("### 📝 Câu trả lời")
            route_label = msg.get("route", "RAG").upper()
            st.caption(f"🎯 **Tuyến xử lý:** `{route_label}`")
            st.write(msg["answer"])

            if msg.get("possible_hallucination"):
                st.warning("⚠️ **Lưu ý kiểm thử (Guardrail Tuần 6):** Câu trả lời có chứa số liệu cần đối chiếu thêm với tài liệu gốc.")

        # KHỐI 2: TÁCH RIÊNG HOÀN TOÀN KHỐI CĂN CỨ & NGUỒN TRÍCH DẪN
        with st.container(border=True):
            st.markdown("### 📚 Căn cứ quy chế & Nguồn trích dẫn")
            citations = msg.get("citations", [])
            if citations:
                for idx, cit in enumerate(citations, start=1):
                    title = cit.get("title", "Tài liệu học vụ")
                    source = cit.get("source", "Tài liệu quy chế")
                    doc_id = cit.get("doc_id", f"DOC-{idx}")

                    with st.expander(f"📌 [Nguồn {idx}] {title} ({doc_id})", expanded=True):
                        st.write(f"**Văn bản trích dẫn:** {source}")
            else:
                st.caption("ℹ️ Không có trích dẫn tài liệu cụ thể cho câu hỏi này (phù hợp với tuyến tra cứu hiện tại).")

        st.markdown("---")

# Sidebar thông tin trợ giúp
with st.sidebar:
    st.header("ℹ️ Về hệ thống")
    st.write(
        "Hệ thống RAG QA học vụ Đại học FPT được phát triển cho đồ án TMG301. "
        "Trong **Tuần 6**, hệ thống hoàn thiện bộ lọc Guardrails chống ảo giác, "
        "đóng băng phạm vi mock và chuẩn bị bàn giao cho TV1 & TV2."
    )
    st.markdown("---")
    st.subheader("💡 Câu hỏi gợi ý thử nghiệm:")
    suggestions = [
        "Học phí ngành AI khoá 2026 là bao nhiêu?",
        "Còn năm 2023 thì sao?",
        "Điều kiện để không bị cảnh cáo học vụ là gì?",
        "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
        "Điều kiện xét tốt nghiệp đại học như thế nào?",
    ]
    for s in suggestions:
        st.code(s, language=None)

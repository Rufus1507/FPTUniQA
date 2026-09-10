"""Giao diện người dùng Streamlit cho hệ thống University QA. Phụ trách: TV3."""

import requests
import streamlit as st

st.set_page_config(
    page_title="Hệ Thống Hỏi Đáp Đại Học (RAG)",
    page_icon="🎓",
    layout="wide",
)

# Tùy chỉnh CSS giao diện hiện đại
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .citation-card {
        background-color: #F3F4F6;
        border-left: 4px solid #3B82F6;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 4px;
    }
    .intent-badge {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🎓 Trợ Lý Tư Vấn Đào Tạo & Quy Chế Đại Học</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Hệ thống RAG thông minh tra cứu quy chế, học phí, đăng ký học phần và chuẩn đầu ra.</div>',
    unsafe_allow_html=True,
)

# Sidebar cấu hình
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    api_url = st.text_input("Địa chỉ Backend API", value="http://localhost:8000")
    top_k = st.slider("Số lượng tài liệu tra cứu (Top-K)", min_value=1, max_value=10, value=4)

    st.markdown("---")
    st.subheader("💡 Câu hỏi gợi ý:")
    sample_queries = [
        "Sinh viên được đăng ký tối đa bao nhiêu tín chỉ một kỳ?",
        "Nếu bị điểm F thì phải làm sao?",
        "Điều kiện chuẩn đầu ra ngoại ngữ để tốt nghiệp?",
        "Tiêu chuẩn nhận học bổng khuyến khích loại Xuất sắc?",
        "Học phí 1 tín chỉ ngành Khoa học máy tính là bao nhiêu?",
    ]
    for q in sample_queries:
        if st.button(q, key=q):
            st.session_state["current_query"] = q

query_input = st.text_input(
    "Nhập câu hỏi của bạn tại đây:",
    value=st.session_state.get("current_query", ""),
    placeholder="Ví dụ: Quy định về cảnh báo học tập và thôi học như thế nào?",
)

if st.button("🚀 Gửi câu hỏi", type="primary"):
    if not query_input.strip():
        st.warning("Vui lòng nhập nội dung câu hỏi.")
    else:
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            try:
                # Gọi API backend
                response = requests.post(
                    f"{api_url}/api/v1/query",
                    json={"query": query_input, "top_k": top_k},
                    timeout=30,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success("Đã tìm thấy câu trả lời!")

                    # Hiển thị thông tin Intent
                    intent = data.get("intent", "factoid")
                    st.markdown(f"**Phân loại ý định:** <span class='intent-badge'>{intent.upper()}</span>", unsafe_allow_html=True)

                    st.markdown("### 📝 Câu trả lời")
                    st.markdown(data.get("answer", ""))

                    # Hiển thị trích dẫn nguồn
                    citations = data.get("citations", [])
                    if citations:
                        st.markdown("### 📚 Căn cứ quy chế & Nguồn trích dẫn")
                        for cit in citations:
                            st.markdown(
                                f"""
                                <div class="citation-card">
                                    <strong>[{cit.get('doc_id')}] {cit.get('title')}</strong> - <em>{cit.get('section', '')}</em><br/>
                                    <small>{cit.get('snippet')}</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    # Chi tiết tài liệu
                    with st.expander("🔍 Xem các đoạn tài liệu ngữ cảnh trích xuất"):
                        for doc in data.get("retrieved_documents", []):
                            st.write(f"**{doc.get('title')}** (ID: `{doc.get('id')}`)")
                            st.write(doc.get("text"))
                            st.divider()

                else:
                    st.error(f"Lỗi từ server API: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Không thể kết nối đến Backend API ({api_url}). Vui lòng đảm bảo server đang chạy.\nChi tiết: {e}")

"""Giao diện người dùng Streamlit cho hệ thống FPTUniQA. Phụ trách: TV3."""

import requests
import streamlit as st

st.set_page_config(
    page_title="FPTUniQA - Trợ Lý Học Vụ & Quy Chế Đại Học FPT",
    page_icon="🎓",
    layout="wide",
)

# Tùy chỉnh CSS giao diện hiện đại & cam FPT đặc trưng
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F37021;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .badge-container {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    .intent-badge {
        background-color: #FFF2E8;
        color: #D4380D;
        border: 1px solid #FFBB96;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .cohort-badge {
        background-color: #E6F7FF;
        color: #096DD9;
        border: 1px solid #91D5FF;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .campus-badge {
        background-color: #F6FFED;
        color: #389E0D;
        border: 1px solid #B7EB8F;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .citation-card {
        background-color: #FAFAFA;
        border-left: 4px solid #F37021;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🎓 FPTUniQA - Trợ Lý Học Vụ & Quy Chế Đại Học FPT</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Hệ thống RAG tiên tiến nhận biết niên khóa K17-K22, tra cứu quy chế, học phí, OJT và chuẩn đầu ra.</div>',
    unsafe_allow_html=True,
)

# Sidebar cấu hình
with st.sidebar:
    st.header("⚙️ Cấu Hình Hệ Thống")
    api_url = st.text_input("Địa chỉ Backend API", value="http://localhost:8000")
    top_k = st.slider("Số lượng tài liệu tra cứu (Top-K)", min_value=1, max_value=10, value=4)

    st.markdown("---")
    st.subheader("💡 Câu hỏi mẫu FPT (K17 - K22):")
    sample_queries = [
        "Mức học phí một kỳ chuyên ngành của sinh viên K19 là bao nhiêu tiền?",
        "Sinh viên K20 bị điểm F môn học thì phải xử lý như thế nào?",
        "Học phí tiếng Anh chuẩn bị một mức của sinh viên K22 là bao nhiêu?",
        "Điều kiện để sinh viên K18 được đi thực tập tốt nghiệp doanh nghiệp OJT?",
        "Chi phí ở ký túc xá phòng 4 người tại campus Hòa Lạc FUHL là bao nhiêu tiền một kỳ?",
        "Lệ phí thi lại và học lại tại Đại học FPT được tính thế nào?",
        "Thời tiết hôm nay thế nào?",
    ]
    for q in sample_queries:
        if st.button(q, key=q):
            st.session_state["current_query"] = q

query_input = st.text_input(
    "Nhập câu hỏi học vụ hoặc tra cứu quy chế của bạn:",
    value=st.session_state.get("current_query", ""),
    placeholder="Ví dụ: Quy định về học phí chuyên ngành K19 hoặc điều kiện chuyển ngành...",
)

if st.button("🚀 Gửi câu hỏi", type="primary"):
    if not query_input.strip():
        st.warning("Vui lòng nhập nội dung câu hỏi.")
    else:
        with st.spinner("Đang trích xuất thực thể, tra cứu dữ liệu kép và tổng hợp câu trả lời..."):
            try:
                # Gọi API backend
                response = requests.post(
                    f"{api_url}/api/v1/query",
                    json={"query": query_input, "top_k": top_k},
                    timeout=30,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success("Đã tìm thấy câu trả lời chính xác!")

                    # Hiển thị thông tin Intent và Metadata Slots (Cohort / Campus)
                    intent = data.get("intent", "factoid")
                    cohort = data.get("cohort")
                    campus = data.get("campus")

                    badges_html = f"<div class='badge-container'>"
                    badges_html += f"<span class='intent-badge'>🏷️ Ý ĐỊNH: {intent.upper()}</span>"
                    if cohort:
                        badges_html += f"<span class='cohort-badge'>🎓 KHÓA: {cohort} (Đã lọc cứng)</span>"
                    if campus:
                        badges_html += f"<span class='campus-badge'>📍 CƠ SỞ: {campus}</span>"
                    badges_html += "</div>"
                    st.markdown(badges_html, unsafe_allow_html=True)

                    st.markdown("### 📝 Câu trả lời chi tiết")
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
                    with st.expander("🔍 Xem các đoạn tài liệu ngữ cảnh trích xuất từ Sổ tay"):
                        for doc in data.get("retrieved_documents", []):
                            doc_cohort = doc.get("applies_to_cohort") or doc.get("metadata", {}).get("cohort", "ALL")
                            st.write(f"**{doc.get('title')}** (ID: `{doc.get('id')}` | Khóa: `{doc_cohort}`)")
                            st.write(doc.get("text"))
                            st.divider()

                else:
                    st.error(f"Lỗi từ server API: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Không thể kết nối đến Backend API ({api_url}). Vui lòng đảm bảo server đang chạy.\nChi tiết: {e}")

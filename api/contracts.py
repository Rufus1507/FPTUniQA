"""Định nghĩa hợp đồng dữ liệu (Data Contracts & Schemas) cho toàn bộ hệ thống University QA.

Hệ thống tuân thủ 3 Hợp Đồng Giao Diện cốt lõi (Contract 1, Contract 2, Contract 3):
- CONTRACT 1: Hợp đồng Giao Tiếp Client / API & Đầu Ra Generation (API & Generation Contract)
- CONTRACT 2: Hợp đồng Tầng Tìm Kiếm / Tra Cứu Tài Liệu (Retrieval Contract Specification - TV2 & TV3)
- CONTRACT 3: Hợp đồng Tầng Xử Lý & Hiểu Truy Vấn (Semantic Parsing Contract - ParsedQuery)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


# ==============================================================================
# CONTRACT 1: HỢP ĐỒNG GIAO TIẾP CLIENT / API & ĐẦU RA GENERATION
# ==============================================================================

class QueryRequest(BaseModel):
    """Hợp đồng nhận câu hỏi từ Client (hỗ trợ cả trường 'query' và 'question')."""

    query: Optional[str] = Field(
        default=None,
        description="Nội dung câu hỏi của sinh viên về quy chế học vụ",
        example="Điều kiện để không bị cảnh cáo học vụ là gì?",
    )
    question: Optional[str] = Field(
        default=None,
        description="Alias câu hỏi nhận từ các client/curl khác nhau",
        example="Điều kiện để không bị cảnh cáo học vụ là gì?",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Mã định danh phiên hội thoại (phục vụ multi-turn)",
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng đoạn tài liệu cần truy xuất",
    )

    @model_validator(mode="after")
    def validate_and_sync_query(self) -> "QueryRequest":
        """Đồng bộ trường query và question để tương thích linh hoạt mọi payload."""
        if not self.query and not self.question:
            raise ValueError("Vui lòng cung cấp trường 'query' hoặc 'question'.")
        if not self.query and self.question:
            self.query = self.question
        elif not self.question and self.query:
            self.question = self.query
        return self


class Citation(BaseModel):
    """Hợp đồng cấu trúc nguồn tài liệu trích dẫn căn cứ."""

    doc_id: str = Field(..., example="FPTU-QC-001", description="Mã định danh tài liệu quy chế")
    title: str = Field(..., example="Quy chế cảnh báo học vụ và đình chỉ học tập", description="Tiêu đề văn bản")
    source: str = Field(..., example="Sổ tay sinh viên ĐH FPT 2024 - Mục 4.2, Trang 22", description="Vị trí trích dẫn cụ thể")
    category: Optional[str] = Field(default="quy_che", description="Phân loại: 'syllabus' | 'quy_che' | 'hoc_phi_hoc_bong'")
    source_index: Optional[int] = Field(default=1, description="Số thứ tự đánh dấu [Nguồn N] trong câu trả lời")


class QueryResponse(BaseModel):
    """Hợp đồng phản hồi kết quả trả lời kèm danh sách trích dẫn (Strict Grounding)."""

    answer: str = Field(..., description="Câu trả lời tổng hợp từ tài liệu quy chế kèm trích dẫn [Nguồn N]")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Danh sách các nguồn tài liệu được dùng làm căn cứ",
    )
    route: Optional[str] = Field(default=None, description="Tuyến định tuyến đã chọn")
    rewritten_query: Optional[str] = Field(default=None, description="Câu hỏi sau khi qua Query Rewriting")
    session_id: Optional[str] = Field(default=None, description="Mã phiên hội thoại")
    possible_hallucination: Optional[bool] = Field(default=False, description="Cờ cảnh báo số liệu ngoài context (Tuần 6)")


class HealthResponse(BaseModel):
    """Hợp đồng phản hồi trạng thái sức khỏe dịch vụ API."""

    status: str = Field(default="ok", description="Trạng thái máy chủ")


class GenerationOutput(BaseModel):
    """Hợp đồng đầu ra của LLM và tầng Generation."""

    answer: str = Field(..., description="Câu trả lời đã được trích dẫn ký hiệu [Nguồn N]")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Danh sách trích dẫn căn cứ tương ứng",
    )


# ==============================================================================
# CONTRACT 2: HỢP ĐỒNG TẦNG TÌM KIẾM / TRA CỨU TÀI LIỆU (RETRIEVAL CONTRACT)
# ==============================================================================

class DocumentChunk(BaseModel):
    """Lược đồ dữ liệu bắt buộc cho từng đoạn tài liệu trích xuất từ Tầng Retrieval (TV2).

    Các trường lõi bắt buộc:
    - doc_id: str
    - text: str (nội dung chunk)
    - score: float (độ tương đồng [0.0, 1.0])
    - retrieval_strategy: str ('bm25' | 'dense' | 'hybrid' | 'mock')
    - metadata: Dict[str, Any] (chứa ít nhất effective_date, applies_to_cohort, doc_type)
    """

    doc_id: str = Field(..., description="Mã định danh duy nhất của đoạn tài liệu / chunk (VD: 'FPTU-QC-001')")
    text: str = Field(..., description="Nội dung văn bản chi tiết làm ngữ cảnh (context) cho LLM")
    score: float = Field(..., ge=0.0, le=1.0, description="Điểm độ tương đồng liên quan đã chuẩn hóa [0.0, 1.0]")
    retrieval_strategy: str = Field(
        default="mock",
        description="Chiến lược tìm kiếm: 'bm25' | 'dense' | 'hybrid' | 'mock'",
        example="hybrid",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "effective_date": "2024-01-01",
            "applies_to_cohort": "ALL",
            "doc_type": "quy_che",
        },
        description="Metadata lồng: effective_date, applies_to_cohort, doc_type, ...",
        example={
            "effective_date": "2024-01-01",
            "applies_to_cohort": "K2020-K2024",
            "doc_type": "quy_che",
        },
    )

    # Các trường phụ trợ cho giao diện UI và tương thích ngược
    title: Optional[str] = Field(default=None, description="Tiêu đề điều khoản hoặc phần quy chế")
    category: Optional[str] = Field(default="quy_che", description="Phân loại: 'syllabus' | 'quy_che' | 'hoc_phi_hoc_bong'")
    source: Optional[str] = Field(default=None, description="Nguồn trích dẫn tường minh hiển thị lên UI")
    content: Optional[str] = Field(default=None, description="Alias tương thích ngược cho text")

    @model_validator(mode="after")
    def sync_text_and_content(self) -> "DocumentChunk":
        """Đồng bộ text và content để đảm bảo tương thích hoàn toàn."""
        if not self.text and self.content:
            self.text = self.content
        elif not self.content and self.text:
            self.content = self.text
        return self


class RetrievalResponse(BaseModel):
    """Hợp đồng danh sách kết quả trả về từ hàm retrieve(query, top_k)."""

    results: List[DocumentChunk] = Field(
        default_factory=list,
        description="Danh sách chunk liên quan nhất, sắp xếp giảm dần theo score",
    )


# ==============================================================================
# CONTRACT 3: HỢP ĐỒNG TẦNG XỬ LÝ & HIỂU TRUY VẤN (SEMANTIC PARSING CONTRACT)
# ==============================================================================

class ParsedQuery(BaseModel):
    """Hợp đồng đối tượng đầu ra sau khi phân tích và hiểu truy vấn (Semantic Parsing).

    Bắt buộc 5 trường cốt lõi phục vụ đánh giá Slot Accuracy, Exact Match, Fallback Rate (Tuần 7):
    - intent: str (Ý định người dùng)
    - slots: Dict[str, Any] (Các slot trích xuất có cấu trúc)
    - confidence: float (Độ tin cậy [0.0, 1.0])
    - parser_method: str ('rule_based' | 'few_shot_llm' | 'fine_tuned_slm')
    - fallback_used: bool (Cờ báo hiệu kích hoạt fallback)
    """

    # --- 5 TRƯỜNG CỐT LÕI BẮT BUỘC THEO BẢN KẾ HOẠCH GỐC ---
    intent: str = Field(
        ...,
        description="Ý định người dùng (VD: 'hoi_quy_che', 'tra_cuu_hoc_phi', 'xet_tot_nghiep', 'ood')",
        example="hoi_quy_che",
    )
    slots: Dict[str, Any] = Field(
        default_factory=dict,
        description="Các slot trích xuất dạng dict có cấu trúc (VD: {'program': 'AI', 'cohort': '2027'})",
        example={"topic": "canh_bao_hoc_vu", "target": "dieu_kien"},
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Độ tin cậy của bộ phân tích semantic parsing [0.0, 1.0]",
        example=0.95,
    )
    parser_method: str = Field(
        ...,
        description="Phương pháp phân tích: 'rule_based' | 'few_shot_llm' | 'fine_tuned_slm'",
        example="rule_based",
    )
    fallback_used: bool = Field(
        ...,
        description="Cờ báo hiệu có kích hoạt cơ chế fallback khi parser chính thất bại hay không",
        example=False,
    )

    # --- CÁC TRƯỜNG PHỤ TRỢ (TÙY CHỌN) ---
    original_query: Optional[str] = Field(
        default=None,
        description="Câu hỏi thô ban đầu do sinh viên nhập vào",
        example="Dieu kien de k bi canh cao hoc vu la gi?",
    )
    normalized_query: Optional[str] = Field(
        default=None,
        description="Câu hỏi sau chuẩn hóa Unicode NFC, xóa khoảng trắng thừa, lowercase",
        example="điều kiện để không bị cảnh cáo học vụ là gì?",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Danh sách từ khóa học vụ trích xuất phục vụ tìm kiếm BM25",
        example=["cảnh cáo", "học vụ", "điều kiện"],
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Các thực thể nhận diện được",
        example={"terms": ["cảnh cáo học vụ"], "target": "điều kiện"},
    )
    is_valid: bool = Field(
        default=True,
        description="Đánh giá câu hỏi có hợp lệ (không rỗng, không spam, trong phạm vi) hay không",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Siêu dữ liệu bổ trợ phục vụ điều phối pipeline và lọc bộ lọc",
    )


__all__ = [
    # Contract 1: API & Generation
    "QueryRequest",
    "Citation",
    "QueryResponse",
    "HealthResponse",
    "GenerationOutput",
    # Contract 2: Retrieval
    "DocumentChunk",
    "RetrievalResponse",
    # Contract 3: Query Parsing
    "ParsedQuery",
]

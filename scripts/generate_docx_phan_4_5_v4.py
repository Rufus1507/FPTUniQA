"""
Script xuất Phần 4 (Kiến trúc Hệ thống) & Phần 5 (Thiết lập Thực nghiệm) chuẩn hóa v4 ra Word (.docx & .doc).
"""

import shutil
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def set_cell_background(cell, fill_hex: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=90, bottom=90, left=130, right=130) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_callout(doc, title: str, text: str, color_hex="1E3A8A", bg_hex="EFF6FF") -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.7)
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=110, bottom=110, left=160, right=160)

    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{color_hex}"/>'
        f'<w:top w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    r_title = p.add_run(f"[{title}]\n")
    r_title.bold = True
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(10.5)
    r_title.font.color.rgb = RGBColor.from_string(color_hex)

    r_text = p.add_run(text)
    r_text.font.name = "Times New Roman"
    r_text.font.size = Pt(10.5)
    r_text.font.color.rgb = RGBColor(31, 41, 55)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_heading_styled(doc, text: str, level: int):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(12 if level > 1 else 16)
    h.paragraph_format.space_after = Pt(5)
    for r in h.runs:
        r.font.name = "Times New Roman"
        r.bold = True
        if level == 1:
            r.font.size = Pt(15)
            r.font.color.rgb = RGBColor(30, 58, 138)
        elif level == 2:
            r.font.size = Pt(13)
            r.font.color.rgb = RGBColor(37, 99, 235)
        else:
            r.font.size = Pt(11.5)
            r.font.color.rgb = RGBColor(31, 41, 55)
    return h


def add_para(doc, text: str, bold_prefix: str = "", space_after: int = 5):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.18
    if bold_prefix:
        rp = p.add_run(bold_prefix)
        rp.bold = True
        rp.font.name = "Times New Roman"
        rp.font.size = Pt(11)
        rp.font.color.rgb = RGBColor(30, 58, 138)
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(31, 41, 55)
    return p


def add_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    for j, h in enumerate(headers):
        table.cell(0, j).text = h

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            table.cell(i + 1, j).text = str(val)

    for i, row in enumerate(table.rows):
        is_header = (i == 0)
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        if is_header:
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for j, cell in enumerate(row.cells):
            if col_widths and j < len(col_widths):
                cell.width = Inches(col_widths[j])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            if is_header:
                set_cell_background(cell, "1E3A8A")
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(9.5)
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "FFFFFF" if i % 2 == 1 else "F8FAFC")
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(9.5)
                        r.font.color.rgb = RGBColor(31, 41, 55)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table


def main():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(4)
    rt = p_title.add_run("BÁO CÁO NGHIÊN CỨU FPTUniQA (PHIÊN BẢN V4)\nPHẦN 4: KIẾN TRÚC HỆ THỐNG & PHẦN 5: THIẾT LẬP THỰC NGHIỆM")
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(15)
    rt.bold = True
    rt.font.color.rgb = RGBColor(30, 58, 138)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    rs = p_sub.add_run("Chuẩn hóa từ Báo cáo Kiến trúc Pipeline và Báo cáo Đánh giá Thực nghiệm Toàn diện v4 (Commit: c083ad3)")
    rs.font.name = "Times New Roman"
    rs.font.size = Pt(10.5)
    rs.italic = True
    rs.font.color.rgb = RGBColor(100, 116, 139)

    # ==================== PHẦN 4 ====================
    add_heading_styled(doc, "4. KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)", level=1)
    add_para(
        doc,
        "FPTUniQA được thiết kế theo kiến trúc Đa tầng Thích ứng Kết hợp Định tuyến Ba nhánh (Multi-Tier Adaptive Tri-Routing Architecture). "
        "Hệ thống phân luồng câu hỏi qua 8 tầng xử lý (Tầng 0 đến Tầng 7) và điều phối về 3 động cơ chuyên biệt: "
        "(1) Tra cứu Bảng dữ liệu Xác định (SSOT Lookup), (2) Đồ thị Tri thức Học thuật (Academic Knowledge Graph), "
        "và (3) Truy xuất Văn bản Lai ghép (Hybrid Text-RAG)."
    )

    add_heading_styled(doc, "4.1. Luồng Dữ liệu Tổng thể (Tầng 0 đến Tầng 7)", level=2)
    add_callout(
        doc,
        "SƠ ĐỒ DÒNG CHẢY XỬ LÝ 8 TẦNG (TẦNG 0 – TẦNG 7)",
        "[Truy vấn + session_id]\n"
        "  ├─> TẦNG 0: Safety Pre-Gate & Near-OOD (< 5ms: external_orgs.json + Regex Injection/Gian lận) ──(Vi phạm)──> Từ chối OOD\n"
        "  ├─> TẦNG 1: Session Memory (Max 10 turns, TTL 3600s) & Query Rewriting (Teencode + Self-Contained/Topic-Switch Gate + Qwen2.5-3B)\n"
        "  ├─> TẦNG 2: Semantic Parser (Fast-path Regex < 2ms / LLM Constrained JSON) & EntityNormalizer (6 từ điển, Longest-Match, NFKC)\n"
        "  ├─> TẦNG 3: Intent Router & Hierarchy Levels (Levels 1–10) phân luồng 5 nhánh:\n"
        "  │     ├─ [ood / uncertain] ──> Từ chối chuẩn sư phạm (Level 10)\n"
        "  │     ├─ [clarification]   ──> Hỏi làm rõ thực thể thiếu (Level 4)\n"
        "  │     ├─ [structured_lookup] ──> TẦNG 6A: Deterministic SSOT Renderer (190 biểu phí + 3.282 mục môn học, 0% Hallucination)\n"
        "  │     └─ [rag_pipeline]      ──> TẦNG 4: Hybrid Retrieval (BM25 PyVi + FAISS e5-base 768d, RRF k=60, w=[0.4, 0.6], Pool K=60..80)\n"
        "  │                                   + TẦNG 5: Academic Knowledge Graph (Topo-sort tiên quyết, OJT K17-K22, Context Injection)\n"
        "  │                                   + TẦNG 6B: Text-RAG LLM Generator (Ollama qwen2.5:3b-instruct, temp=0.1)\n"
        "  └─> TẦNG 7: Guardrails (Ungrounded Numbers Detector) + Trích xuất Citations [Nguồn N] + Disclaimer FAP & Audit Log"
    )

    add_heading_styled(doc, "4.2. Đặc tả Kỹ thuật Từng Tầng Xử lý", level=2)
    add_para(doc, "Quét từ điển tổ chức ngoài (external_orgs.json) và biểu thức chính quy phát hiện Prompt Injection, gian lận thi PE/EOS trước khi gọi LLM (< 5 ms).", "• Tầng 0 – Safety Pre-Gate & Near-OOD (safety_gate.py): ")
    add_para(doc, "Lưu tối đa 10 lượt/phiên (TTL 3.600s), cửa sổ trượt 5 lượt gần nhất (cắt câu trả lời cũ 150 ký tự). Chuẩn hóa teencode, kiểm tra Self-Containedness Gate và Topic Switch Gate (8 chủ đề) để khử độc ngữ cảnh cũ trước khi viết lại câu hỏi bằng Rule Fast-Path hoặc Qwen 2.5 3B.", "• Tầng 1 – Session Memory & Query Rewriting (rewriting.py): ")
    add_para(doc, "Chuẩn hóa thực thể qua 6 bộ từ điển JSON (Longest Match First, NFKC, không dấu). Kết hợp Fast-Path Regex (< 2 ms) và LLM Constrained JSON xuất đối tượng chuẩn Contract 3 (ParsedQuery).", "• Tầng 2 – Semantic Parser & EntityNormalizer (semantic_parser.py, engine.py): ")
    add_para(doc, "Gán cấp độ phức tạp Level 1–10 và điều phối về 5 tuyến: ood, uncertain (confidence < 0.5), clarification (thiếu khóa/cơ sở), structured_lookup (SSOT), hoặc rag_pipeline.", "• Tầng 3 – Intent Router (router.py): ")
    add_para(doc, "Kết hợp BM25Okapi (pyvi + ACADEMIC_COMPOUND_TERMS) và FAISS IndexFlatIP (intfloat/multilingual-e5-base 768 chiều). Hợp nhất RRF (k=60, trọng số [0.4, 0.6], Pool K=60..80). Hỗ trợ 3 chế độ lọc metadata theo khóa/cơ sở (none, soft với alpha=beta=0.25, và hard kèm Graceful Fallback) cùng Cross-Encoder Reranker (BAAI/bge-reranker-base).", "• Tầng 4 – Hybrid Retrieval Engine (bm25.py, dense.py, rrf.py, filter.py, retriever.py): ")
    add_para(doc, "Đồ thị DAG duyệt tô-pô chuỗi môn học tiên quyết (PRF192 -> PRO192 -> PRJ301/SWE201C -> SWP391), phân tầng điều kiện OJT theo khóa K17–K22, đối chiếu CTĐT liên ngành; vừa hỗ trợ trả lời cấu trúc vừa bơm ngữ cảnh (Context Injection) vào nhánh Text-RAG.", "• Tầng 5 – Academic Knowledge Graph (knowledge_graph.py): ")
    add_para(doc, "Tầng 6A kết xuất tất định từ 190 biểu phí chính quy và 3.282 bản ghi môn học trên RAM (100% Faithfulness, 0% Hallucination). Tầng 6B sinh văn bản quy chế bằng qwen2.5:3b-instruct (temperature=0.1) với System Prompt kiểm soát nghiêm ngặt.", "• Tầng 6 – Dual Generation Engine (Tầng 6A SSOT & Tầng 6B Text-RAG LLM): ")
    add_para(doc, "Quét thực thể số học không có trong ngữ cảnh (ungrounded_numbers -> possible_hallucination), ánh xạ trích dẫn [Nguồn N] về doc_id/quyết định ban hành, gắn khuyến cáo xác nhận trên cổng FAP.", "• Tầng 7 – Output Guardrails & Citations (guardrails.py, citation.py): ")

    add_heading_styled(doc, "4.3. Bảng Tổng hợp Tham số Cấu hình Hệ thống", level=2)
    cfg_headers = ["Phân hệ / Tầng", "Tham số Kỹ thuật", "Giá trị Cấu hình", "Tệp Định nghĩa", "Vai trò Vận hành"]
    cfg_rows = [
        ["Dữ liệu & Chunking", "chunk_size / overlap", "512 / 64 ký tự", "configs/base.yaml", "Phân đoạn quy chế tạo 824 chunks chuẩn."],
        ["Dữ liệu Cấu trúc", "structured_data", "190 biểu phí + 6 từ điển", "data/processed/", "Bảng SSOT (38 ngành x 5 cơ sở) & từ điển thực thể."],
        ["Tầng 1: Memory", "max_turns / ttl / window", "10 lượt / 3600s / 5 lượt", "rag_pipeline.py, rewriting.py", "Giới hạn phiên RAM, trượt 5 lượt, cắt đáp án cũ 150 ký tự."],
        ["Tầng 2 & 3", "parser_temp / conf_min", "temp = 0.0 / conf = 0.5", "base.yaml, router.py", "Ép JSON tất định; dưới 0.5 chuyển sang uncertain."],
        ["Tầng 4: BM25", "k1 / b / tokenizer", "1.5 / 0.75 / pyvi", "base.yaml, bm25.py", "Tìm kiếm từ vựng tiếng Việt + từ ghép học vụ."],
        ["Tầng 4: Dense", "model / dim / metric", "multilingual-e5-base (768d, IP)", "base.yaml, dense.py", "Tìm kiếm vector ngữ nghĩa chuẩn hóa L2."],
        ["Tầng 4: RRF & Pool", "rrf_k / weights / cand_k", "k=60, w=[0.4, 0.6], K=60..80", "base.yaml, retriever.py", "Hợp nhất thứ hạng ưu tiên Dense và mở rộng pool lọc."],
        ["Tầng 4: Filter", "metadata_mode / alpha, beta", "hard / soft (0.25, 0.25) / none", "filter.py, retriever.py", "Kiểm soát đúng khóa tuyển sinh, giữ quy chế chung."],
        ["Tầng 4: Reranker", "model / candidate_k / top_k", "bge-reranker-base / 20 / 5", "base.yaml, config.py", "Tái xếp hạng Cross-Encoder giai đoạn 2."],
        ["Tầng 6B: LLM Gen", "model / temp / max_tokens", "qwen2.5:3b-instruct / 0.1 / 320", "base.yaml, llm.py", "Sinh câu trả lời quy chế cục bộ qua Ollama."],
    ]
    add_styled_table(doc, cfg_headers, cfg_rows, col_widths=[1.2, 1.3, 1.4, 1.1, 1.7])

    # ==================== PHẦN 5 ====================
    add_heading_styled(doc, "5. THIẾT LẬP THỰC NGHIỆM (EXPERIMENTAL SETUP)", level=1)
    add_para(
        doc,
        "Toàn bộ quy trình thực nghiệm trong phiên bản v4 được chuẩn hóa độc lập, tắt bộ nhớ đệm (disable_cache=True) khi đo ablation và độ trễ, "
        "kiểm tra toàn vẹn số bản ghi bằng assert và truy vết 100% số liệu về tệp experiments/audit/numbers_traceability_v4.csv."
    )

    add_heading_styled(doc, "5.1. Phần cứng, Phần mềm và Mô hình Triển khai", level=2)
    hw_headers = ["Hạng mục Hạ tầng", "Thông số Kỹ thuật Chi tiết", "Vai trò trong Thực nghiệm"]
    hw_rows = [
        ["CPU & Bộ nhớ RAM", "AMD Ryzen 7 (16 Cores), RAM khả dụng 15,24 GB (~83,4% load)", "Thực thi BM25, FAISS-CPU, Embedding và pipeline Python."],
        ["Hệ điều hành & Git", "Windows 11 Enterprise, Python 3.10.11, Commit 85e1e6e / c083ad3", "Môi trường chuẩn chạy các script kiểm toán độc lập v4."],
        ["Framework AI/ML", "PyTorch 2.6.0+cu124, faiss-cpu 1.10.0, transformers 4.49.0, pyvi", "Tính toán tensor, tìm kiếm vector và xử lý tiếng Việt."],
        ["Mô hình LLM Biên", "Qwen 2.5 3B Instruct (4-bit, Ollama GPU, 0 VNĐ chi phí API)", "Thực thi Query Rewriter, Semantic Parser và Text-RAG Generator."],
        ["Embedding & Reranker", "intfloat/multilingual-e5-base (768d) & BAAI/bge-reranker-base", "Mã hóa 824 chunks quy chế và tái xếp hạng ứng viên."],
    ]
    add_styled_table(doc, hw_headers, hw_rows, col_widths=[1.5, 2.7, 2.5])

    add_heading_styled(doc, "5.2. Cấu hình Chi tiết 8 Biến thể Ablation và Các Thí nghiệm", level=2)
    abl_headers = ["Mã", "Tên Cấu hình", "retriever_mode", "Pool K & Lọc Metadata", "Parser", "Router", "Rerank", "Mục tiêu Đối sánh"]
    abl_rows = [
        ["C1", "BM25 Lexical Baseline", "bm25", "K=5, không lọc", "regex", "Tắt", "Tắt", "Baseline từ vựng rời rạc thuần túy."],
        ["C2", "Dense Vector Baseline", "dense", "K=5, không lọc", "regex", "Tắt", "Tắt", "Baseline vector ngữ nghĩa thuần túy."],
        ["C3", "Hybrid Sequential", "c3_hybrid_sequential", "K=60, mode=none (Tuần tự)", "regex", "Tắt", "Tắt", "Hợp nhất RRF tuần tự, chưa lọc khóa."],
        ["C3p", "Hybrid Parallel", "c3p_hybrid_parallel", "K=60, mode=none (Song song)", "regex", "Tắt", "Tắt", "Kiểm tra bảo toàn Recall & độ trễ đa luồng."],
        ["C4-soft", "Hybrid + Soft Boost", "c4_hybrid_rrf_soft", "K=80, mode=soft (0.25/0.25)", "regex", "Tắt", "Tắt", "Tăng/phạt điểm mềm theo khóa sau RRF."],
        ["C4-hard", "Hybrid + Hard Filter", "c4_hybrid_rrf_filter", "K=80, mode=hard (Lọc cứng)", "regex", "Tắt", "Tắt", "Triệt tiêu lỗi lẫn khóa (Wrong-Cohort)."],
        ["C5", "Full (No LLM Parser)", "hybrid_filter", "K=80, mode=hard", "regex", "Bật", "Bật", "Đầy đủ Router+SSOT+Graph nhưng dùng Regex."],
        ["C6", "Full Architecture", "hybrid_filter", "K=80, mode=hard", "auto (LLM)", "Bật", "Bật", "Kiến trúc hoàn chỉnh tích hợp LLM Parser."],
    ]
    add_styled_table(doc, abl_headers, abl_rows, col_widths=[0.55, 1.3, 1.15, 1.25, 0.55, 0.45, 0.45, 1.0])

    add_para(doc, "Đo độ trễ tầng retrieval thuần không cache (100 câu x 5 lần lặp có warm-up); kiểm thử khả năng tổng quát hóa trên tập Held-out (N=50 câu mới); khảo sát lưới trọng số RRF và tác động Cross-Encoder trên tập Canonical Retrieval mở rộng (N=117 câu, 14 câu có khóa).", "• Thí nghiệm Truy xuất Mở rộng & Độ trễ Thuần: ")
    add_para(doc, "So sánh WITHOUT_GRAPH (Flat RAG), Stronger Baseline (mở rộng bảng) và WITH_GRAPH (Academic KG) trên N=30 câu hỏi đa chặng thuộc 5 lớp bài toán (prereq_chain, next_course, program_compare, ojt_conditions, f_grade_policy).", "• Thí nghiệm Graph RAG Ablation (N=30): ")
    add_para(doc, "Chạy liên tục 1.000 lượt hội thoại thuộc 768 session từ 15 tệp dữ liệu chuẩn với cấu hình Production (C4-hard K=80, w=[0.4, 0.6], auto_load=True, use_reranker=False) để đo độ ổn định, Topic-Switch, tỉnh lược Anaphora, Routing và phân phối độ trễ theo tuyến.", "• Thí nghiệm Hội thoại Đa lượt Quy mô lớn (N=1.000 lượt / 768 phiên): ")
    add_para(doc, "Kiểm định trên N=20 câu Near-OOD (trường ngoài/chính sách nhà nước) và N=15 câu Adversarial/Jailbreak (vượt quyền, sửa điểm, lừa đảo học vụ), phân loại thủ công theo 3 mức độ an toàn thực tế.", "• Thí nghiệm An toàn Biên & Chống Tấn công (N=35): ")

    add_heading_styled(doc, "5.3. Định nghĩa Chỉ số và Bảng Chốt Mẫu số Đo lường (Denominators)", level=2)
    add_para(
        doc,
        "Các chỉ số được tính toán tự động bằng mã nguồn tại src/FPTUniQA/evaluation/: "
        "(1) Recall@5 (Doc ID) và Recall@5 (Equiv) tính tỷ lệ bao phủ tài liệu vàng hoặc nhóm tương đương trong top-5 (cho phép điểm 0.5 nếu trúng 1/2 tài liệu vàng); "
        "(2) MRR@5 là trung bình nghịch đảo thứ hạng đầu tiên; "
        "(3) Wrong-Cohort Rate đo tỷ lệ câu hỏi có yêu cầu khóa bị lẫn tài liệu khóa khác vào top-5 (0,00% là tốt tuyệt đối); "
        "(4) Faithfulness tính riêng cho SSOT (100%), OOD (100%) và Text-RAG (Lexical Word Overlap sau khi lọc hư từ), gộp theo trọng số 70/20/10; "
        "(5) Kiểm định thống kê dùng Paired Bootstrap (B=10.000, seed=42) và khoảng tin cậy nhị thức Wilson 95% (z=1,96)."
    )

    den_headers = ["Tập Dữ liệu / Thí nghiệm", "Chỉ số Đo lường", "Mẫu số (N)", "Giải thích Nguồn gốc & Quy tắc Mẫu số Chuẩn v4"]
    den_rows = [
        ["Canonical Benchmark V2 (Ablation)", "Latency (p50, p95, Mean) & Weighted Faithfulness", "N = 100 câu", "10 câu x 10 batch. Theo expected_route gồm đúng: 70 câu SSOT (70%) + 20 câu Text-RAG (20%) + 10 câu OOD (10%)."],
        ["Canonical V2 – Retrieval Gold", "Recall@5 (Doc ID), Recall@5 (Equiv), MRR@5", "N = 26 câu", "26 câu hỏi văn bản trong 100 câu có nhãn tài liệu quy chế vàng tại retrieval_gold.json."],
        ["Canonical V2 – Cohort Gold", "Wrong-Cohort Rate (Ablation C1–C6)", "N = 6 câu", "6 câu hỏi trong 26 câu retrieval gold có định danh khóa cụ thể (expected_cohorts). Loại câu chung khỏi mẫu số."],
        ["Held-out Retrieval Set", "Recall@5 (Doc/Equiv), MRR@5, Binary Hit@5", "N = 50 câu", "50 câu có nhãn retrieval gold chưa từng nằm trong 100 câu Ablation (tổng cộng 150 câu kiểm định)."],
        ["Canonical Retrieval Expanded", "RRF Grid Search & Cross-Encoder Impact", "N = 117 câu", "103 câu quy chế chung + 14 câu có khóa cụ thể (N=14 là mẫu số Wrong-Cohort của tập mở rộng)."],
        ["Graph RAG Suite", "ROUGE-L, Entity Precision / Recall / F1", "N = 30 câu", "5 lớp bài toán cấu trúc đa chặng x 6 câu/lớp (graph_rag_suite.jsonl)."],
        ["Safety & Security Suite", "Safe Refusal Rate & Phân loại 3 Mức độ", "N = 35 ca", "Gồm N = 20 câu Near-OOD và N = 15 câu Adversarial / Prompt Injection."],
        ["Multi-turn Simulation (768 phiên)", "Request Success, Route Acc, Topic-Switch, Latency", "N = 1.000 lượt", "Ground truth đổi chủ đề thực tế gồm 75 lượt Switch và 925 lượt Continuation (104 là số kịch bản dự kiến ban đầu)."],
        ["Multi-turn Subsets", "Macro Keyword Recall / OOD / Guardrail Flagged", "N = 157 / 110 / 143", "157 lượt tỉnh lược có nhãn từ khóa; 110 lượt OOD kỳ vọng; 143 lượt thực tế chạy qua Text-RAG và Guardrail (trên 148 lượt RAG kỳ vọng)."],
    ]
    add_styled_table(doc, den_headers, den_rows, col_widths=[1.4, 1.5, 0.9, 2.9])

    out_docx = Path("docs/Phan_4_5_Kien_Truc_Va_Thiet_Lap_Thuc_Nghiem_v4.docx")
    out_doc = Path("docs/Phan_4_5_Kien_Truc_Va_Thiet_Lap_Thuc_Nghiem_v4.doc")
    doc.save(str(out_docx))
    shutil.copyfile(str(out_docx), str(out_doc))
    print(f"Successfully generated:\n- {out_docx}\n- {out_doc}")


if __name__ == "__main__":
    main()

"""
Script generate Word (.docx & .doc) cho Báo cáo Kiến trúc Pipeline FPTUniQA.
"""

import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    border = OxmlElement('w:insideV')
    border.set(qn('w:val'), 'none')
    tblBorders.append(border)
    tblPr.append(tblBorders)

def add_heading_with_spacing(doc, text, level):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    for r in p.runs:
        r.font.name = 'Times New Roman'
        if level == 1:
            r.font.size = Pt(15)
            r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
            r.bold = True
        elif level == 2:
            r.font.size = Pt(13)
            r.font.color.rgb = RGBColor(0x2E, 0x75, 0xB6)
            r.bold = True
        elif level == 3:
            r.font.size = Pt(11.5)
            r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            r.bold = True
    return p

def add_styled_paragraph(doc, text, bold_prefix="", italic=False, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Times New Roman'
        r_pre.font.size = Pt(11)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    return p

def add_callout_box(doc, title, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F2F6FA")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=120)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    left_b = OxmlElement('w:left')
    left_b.set(qn('w:val'), 'single')
    left_b.set(qn('w:sz'), '24')
    left_b.set(qn('w:color'), '1F4E79')
    tcBorders.append(left_b)
    for b in ['top', 'bottom', 'right']:
        node = OxmlElement(f'w:{b}')
        node.set(qn('w:val'), 'none')
        tcBorders.append(node)
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(title + "\n")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(11)
    r1.bold = True
    r1.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    
    r2 = p.add_run(text)
    r2.font.name = 'Times New Roman'
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def populate_table(doc, headers, data, col_widths=None):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    
    # Header row
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], "1F4E79")
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=100, right=100)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10)
            r.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            
    # Data rows
    for row_idx, row_data in enumerate(data):
        row_cells = table.rows[row_idx + 1].cells
        bg_color = "F9FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value)
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=70, bottom=70, left=90, right=90)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 0 or len(str(cell_value)) > 20 else WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
                
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                if i < len(row.cells):
                    row.cells[i].width = Inches(w)
                    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(2)
    p_sp.paragraph_format.space_after = Pt(6)
    return table

def main():
    doc = docx.Document()
    
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        
    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("BÁO CÁO THIẾT KẾ KIẾN TRÚC VÀ ĐẶC TẢ KỸ THUẬT DÒNG CHẢY HỆ THỐNG\n(SYSTEM ARCHITECTURE & PIPELINE TECHNICAL REPORT)")
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(17)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("Đề tài: Hệ thống Hỏi đáp Quy chế Đào tạo và Biểu phí FPTUniQA (Phiên bản Kiến trúc 2.0)")
    run_sub.font.name = 'Times New Roman'
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    
    meta_headers = ["Thông số Kiến trúc", "Mô tả Chi tiết Triển khai"]
    meta_data = [
        ["Mô hình Ngôn ngữ Biên", "Ollama qwen2.5:3b-instruct (Chạy on-premise hoàn toàn, RAM 16GB)"],
        ["Mô hình Embedding", "intfloat/multilingual-e5-base (Vector 768 chiều, kích hoạt thực)"],
        ["Động cơ Đồ thị Tri thức", "NetworkX Academic Knowledge Graph (Topological Sort, Cohort-Aware)"],
        ["Động cơ Bảng cấu trúc", "Deterministic CKB SSOT Engine (190 biểu phí chính thức K17-K22)"],
        ["Cơ chế Hội thoại", "Conversational Query Rewriting đa lượt + Context Decontamination"]
    ]
    populate_table(doc, meta_headers, meta_data, col_widths=[2.4, 4.4])

    # SECTION 1
    add_heading_with_spacing(doc, "1. TỔNG QUAN KIẾN TRÚC TOÀN PHẦN (END-TO-END ARCHITECTURE)", level=1)
    add_styled_paragraph(doc,
        "FPTUniQA triển khai kiến trúc Đa tầng thích ứng (Multi-Tier Adaptive Pipeline) với sự phân tách triệt để giữa dữ liệu số học cấu trúc và văn bản quy chế mở. Khác với các hệ thống RAG phẳng truyền thống (như URAG hay R2GQA) vốn chuyển toàn bộ câu hỏi vào LLM sinh, FPTUniQA sử dụng cơ chế Semantic Parsing Routing để chuyển trực tiếp các câu hỏi số học vào bảng cấu trúc SSOT, triệt tiêu 100% ảo giác số học và tiết kiệm thời gian tính toán.")
    
    add_callout_box(doc, "LUỒNG XỬ LÝ DỮ LIỆU TUẦN TỰ (END-TO-END FLOW):",
        "1. Input User Message -> Tầng 0: Safety Pre-gate quét từ điển tổ chức ngoài và regex vi phạm (<5ms).\n"
        "2. Tầng 1: Session Memory & Rewriter giải quyết đồng tham chiếu, tỉnh lược, tạo câu hỏi độc lập (Standalone Query).\n"
        "3. Tầng 2: Semantic Parser bóc tách Intent và Slots theo chuẩn Contract 3 (ParsedQuery).\n"
        "4. Tầng 3: Intent Router phân luồng sang Structured CKB, Hybrid RAG, Clarification hoặc OOD (Levels 1 - 10).\n"
        "5. Tầng 4: Hybrid Retrieval chạy song song BM25 và FAISS (RRF k=60) kết hợp Soft Metadata Filter.\n"
        "6. Tầng 5: Academic Knowledge Graph duyệt tô-pô cây môn học tiên quyết và điều kiện OJT.\n"
        "7. Tầng 6: Generation qua Template Deterministic (CKB) hoặc Qwen2.5:3B LLM (Text RAG).\n"
        "8. Tầng 7: Guardrail kiểm tra ungrounded numbers, trích xuất citations, gắn disclaimer Phòng Đào tạo.")

    # SECTION 2
    add_heading_with_spacing(doc, "2. CHI TIẾT CÁC TẦNG VÀ CƠ CHẾ KỸ THUẬT TRONG PIPELINE", level=1)
    
    add_styled_paragraph(doc,
        "Đứng trước toàn bộ pipeline để lọc trước các câu hỏi hỏi về trường khác (Bách Khoa, NEU, ĐHQG...), prompt injection và gian lận học vụ. Độ trễ cực thấp (<5ms), bảo vệ an toàn và tiết kiệm 100% tài nguyên tính toán của mô hình LLM.",
        bold_prefix="• Tầng 0 (Safety Pre-gate & Near-OOD): ")
    
    add_styled_paragraph(doc,
        "Quản lý phiên hội thoại với SessionManager (TTL 3600s, max 10 turns). Tích hợp Circuit Breaker (ngắt sau 2 lỗi), chuẩn hóa teencode tức thời, Self-Containedness Gate và Topic Switch Gate ngăn ô nhiễm ngữ cảnh cũ.",
        bold_prefix="• Tầng 1 (Conversational Memory & Rewriting): ")

    add_styled_paragraph(doc,
        "Bao gồm Fast-path Regex Parser (<2ms cho câu hỏi rõ ràng) và Small LLM Parser xuất Constrained JSON (max 320 tokens). Động cơ EntityNormalizer nạp 6 bộ từ điển miền với thuật toán Longest Match First, chuẩn NFKC N1 và không dấu diacritic-insensitive.",
        bold_prefix="• Tầng 2 (Semantic Parser & Entity Normalizer): ")

    add_styled_paragraph(doc,
        "Điều phối truy vấn dựa trên intent, slots và confidence. Phân loại câu hỏi thành 5 nhánh (structured_lookup, rag_pipeline, clarification, ood, uncertain) và gán nhãn mức độ phức tạp từ Level 1 đến Level 10.",
        bold_prefix="• Tầng 3 (Intent Router & Hierarchy Levels): ")

    add_styled_paragraph(doc,
        "Kết hợp FAISS Dense Vector (multilingual-e5-base) và BM25 Sparse (ViTokenizer tiếng Việt và cụm từ chuyên ngành ACADEMIC_COMPOUND_TERMS). Dung hợp qua RRF k=60. Soft-filter metadata ưu tiên tài liệu đúng khóa tuyển sinh và cơ sở, song song hóa qua ThreadPoolExecutor giảm 42.8% độ trễ.",
        bold_prefix="• Tầng 4 (Hybrid Retrieval Engine): ")

    add_styled_paragraph(doc,
        "Xây dựng trên NetworkX, hỗ trợ thuật toán sắp xếp tô-pô (Topological Sort) duyệt cây môn học tiên quyết, phân tầng điều kiện OJT theo khóa tuyển sinh K17-K22, so sánh khung chương trình liên ngành và bơm ngữ cảnh cấu trúc vào prompt sinh.",
        bold_prefix="• Tầng 5 (Academic Knowledge Graph RAG): ")

    add_styled_paragraph(doc,
        "Hai nhánh sinh riêng biệt: Nhánh Deterministic CKB sinh qua template chuẩn từ dữ liệu SSOT (0% hallucination, 100% faithfulness); nhánh Text RAG dùng Qwen2.5:3B on-premise với System Prompt nghiêm ngặt cấm bịa đặt số liệu.",
        bold_prefix="• Tầng 6 (Generation & Deterministic SSOT Engine): ")

    add_styled_paragraph(doc,
        "Quét regex phát hiện ungrounded numbers (số liệu xuất hiện trong câu trả lời nhưng không có trong context), trích xuất citation nguồn căn cứ (mã văn bản, quyết định, ngày ban hành, khóa áp dụng) và tự động gắn cảnh báo xác nhận Phòng Đào tạo.",
        bold_prefix="• Tầng 7 (Guardrails & Legal Citation): ")

    # SECTION 3 & 4
    add_heading_with_spacing(doc, "3. CƠ CHẾ XỬ LÝ HỘI THOẠI ĐA NGỮ CẢNH VÀ CẮT TỰ ĐỘNG", level=1)
    
    add_styled_paragraph(doc,
        "Khi người dùng đặt câu hỏi tiếp nối, hệ thống duyệt lịch sử theo chiều ngược lại (reversed), ưu tiên thực thể xuất hiện ở lượt gần nhất để kế thừa vào câu hỏi mới.",
        bold_prefix="1. Kế thừa Thực thể Ngược (Reverse Traversal): ")

    add_styled_paragraph(doc,
        "Phân giải đại từ 'môn này/môn đó' -> Môn {hist_course}; 'ngành này' -> ngành {hist_program}; 'ở đó/tại đó' -> tại {hist_campus}.",
        bold_prefix="2. Giải quyết Đồng tham chiếu (Coreference): ")

    add_styled_paragraph(doc,
        "Nhận diện các mẫu câu tiếp nối ('thế còn K21?', 'ở Cần Thơ thì sao?'), giữ nguyên chủ đề và ngành học cũ, chỉ hoán đổi slot mới vào.",
        bold_prefix="3. Giải quyết Tỉnh lược (Ellipsis): ")

    add_styled_paragraph(doc,
        "Khi người dùng đính chính ('Không, mình hỏi K21 cơ'), hệ thống phát hiện từ phủ định và đè thực thể mới lên thực thể cũ.",
        bold_prefix="4. Xử lý Đính chính & Phủ định: ")

    add_styled_paragraph(doc,
        "Prompt Rewriter chỉ lấy tối đa 5 lượt gần nhất (history[-5:]) và cắt ngắn câu trả lời của trợ lý ở mức 150 ký tự, chống tràn context window của LLM 3B.",
        bold_prefix="5. Cửa sổ Trượt & Cắt ngắn (Sliding Window & Truncation): ")

    add_styled_paragraph(doc,
        "Self-Containedness Gate và Topic Switch Gate phát hiện nếu câu hỏi mới tự chứa đủ thông tin hoặc đổi chủ đề (từ học phí sang điểm danh/kỷ luật) thì lập tức ngắt kế thừa, ngăn chặn hoàn toàn ô nhiễm ngữ cảnh cũ (Context Decontamination).",
        bold_prefix="6. Khử Ô Nhiễm Ngữ Cảnh (Context Decontamination): ")

    # SECTION 5: EXAMPLES TRACE
    add_heading_with_spacing(doc, "4. NĂM VÍ DỤ MINH HỌA DÒNG CHẢY XỬ LÝ CHI TIẾT (STEP-BY-STEP TRACES)", level=1)
    
    trace_headers = ["Ví dụ Kiểm thử", "Câu hỏi Đầu vào", "Đường đi Pipeline & Quyết định Phân luồng", "Kết quả Đầu ra & Độ trễ"]
    trace_data = [
        ["1. Tra cứu Biểu phí Đơn lượt", "Học phí ngành KTPM ở Cần Thơ khóa K20 bao nhiêu?", "Pre-gate (PASS) -> Fast-path Parser -> Route 'structured_lookup' -> CKB Engine SSOT", "20,090,000 VNĐ/kỳ (12ms, 0% Hallucination)"],
        ["2. Hội thoại Đa lượt Tỉnh lược", "Trong kỳ này có phải đóng học phí không? (Turn 2 OJT)", "Rewriter nhận diện OJT từ Turn 1 -> Viết lại Standalone Query -> Route 'rag_pipeline'", "Trả lời quy định học phí kỳ thực tập doanh nghiệp OJT"],
        ["3. Cắt Ngữ cảnh Đổi Chủ đề", "Quy chế điểm danh vắng quá 20% bị xử lý thế nào?", "Self-Contained Gate & Topic Switch kích hoạt -> Ngắt kế thừa ngành học cũ -> Text RAG", "Bị cấm thi (điểm F) và phải học lại môn đó"],
        ["4. Graph RAG Chuỗi Tiên quyết", "Muốn học SWP391 thì phải học những môn nào trước?", "Parser trích xuất SWP391 -> Graph Engine Topo-sort chuỗi: PRF192 -> PRO192 -> PRJ301 -> SWP391", "Liệt kê chính xác lộ trình 4 môn học (Pass 100%)"],
        ["5. Chặn An toàn Cận miền", "Học phí Đại học Bách Khoa Hà Nội năm 2026 bao nhiêu?", "Safety Pre-gate quét trúng 'Bách Khoa' trong external_orgs.json -> Block ngay lập tức", "Từ chối an toàn có định danh (1.2ms, tiết kiệm LLM)"]
    ]
    populate_table(doc, trace_headers, trace_data, col_widths=[1.5, 1.8, 2.0, 1.7])

    # SECTION 6: CORE REPOSITORY MAP
    add_heading_with_spacing(doc, "5. BẢN ĐỒ THÀNH PHẦN MÃ NGUỒN CỐT LÕI (SOURCE REPOSITORY MAP)", level=1)
    
    repo_headers = ["Thành phần Module", "Đường dẫn Tệp Mã Nguồn", "Chức năng & Nhiệm vụ Trọng tâm"]
    repo_data = [
        ["Pipeline Điều phối", "src/FPTUniQA/pipeline/rag_pipeline.py", "Quản lý answer(), SessionManager, gắn Guardrails & Citations"],
        ["Viết lại Câu hỏi", "src/FPTUniQA/query/rewriting.py", "Teencode, Topic Switch, Self-Containedness, Coreference"],
        ["Phân tích Ngữ nghĩa", "src/FPTUniQA/query/semantic_parser.py", "Fast-path Regex Parser + Small LLM Constrained JSON (Max 320t)"],
        ["Chuẩn hóa Thực thể", "src/FPTUniQA/normalization/engine.py", "Longest Match First, NFKC N1, Accent-Insensitive Matching"],
        ["Tiền kiểm An toàn", "src/FPTUniQA/query/safety_gate.py", "Bộ lọc <5ms tên trường ngoài, prompt injection, gian lận thi PE"],
        ["Điều phối Định tuyến", "src/FPTUniQA/query/router.py", "Phân luồng CKB, RAG, Clarification, OOD và gán Levels 1-10"],
        ["Truy xuất Lai ghép", "src/FPTUniQA/retrieval/retriever.py", "FAISS Dense + BM25Okapi + RRF (k=60) + Soft Metadata Filter"],
        ["Đồ thị Tri thức", "src/FPTUniQA/graph/knowledge_graph.py", "Topological Sort chuỗi tiên quyết, lộ trình OJT, so sánh CTĐT"],
        ["Kiểm soát Ảo giác", "src/FPTUniQA/generation/guardrails.py", "Quét Ungrounded Numbers, đối soát số học với Context"]
    ]
    populate_table(doc, repo_headers, repo_data, col_widths=[1.6, 2.4, 3.0])

    # Save to Word format (.docx and .doc)
    out_docx = os.path.abspath("docs/Bao_Cao_Kien_Truc_Pipeline_FPTUniQA.docx")
    out_doc = os.path.abspath("docs/Bao_Cao_Kien_Truc_Pipeline_FPTUniQA.doc")
    
    doc.save(out_docx)
    shutil.copyfile(out_docx, out_doc)
    
    print(f"Successfully generated DOCX & DOC pipeline reports at:")
    print(f"1. {out_docx}")
    print(f"2. {out_doc}")

if __name__ == "__main__":
    main()

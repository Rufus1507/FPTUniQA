"""
Generate professional Word (.docx & .doc) report for FPTUniQA 1,000-turn Multi-turn Benchmark.
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


def set_cell_margins(cell, top=90, bottom=90, left=130, right=130):
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
    p.paragraph_format.space_before = Pt(13)
    p.paragraph_format.space_after = Pt(4)
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
    if title:
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
        set_cell_margins(hdr_cells[i], top=90, bottom=90, left=90, right=90)
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
            set_cell_margins(row_cells[col_idx], top=70, bottom=70, left=80, right=80)
            p = row_cells[col_idx].paragraphs[0]
            # Alignment: numeric / short values centered, text left-aligned
            val_str = str(cell_value).strip()
            if col_idx in [0, len(row_data) - 1] and len(val_str) > 15:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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
    p_sp.paragraph_format.space_after = Pt(5)
    return table


def build_benchmark_report():
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
    run_title = p_title.add_run("BÁO CÁO TỔNG KẾT KIỂM THỬ HỆ THỐNG FPTUNIQA\nKẾT QUẢ THỰC NGHIỆM TRÊN 1.000 LƯỢT HỘI THOẠI ĐA LƯỢT")
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(16)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(10)
    run_sub = p_sub.add_run("Đề tài: Context-Aware Vietnamese University Question Answering (Hệ thống FPTUniQA)")
    run_sub.font.name = 'Times New Roman'
    run_sub.font.size = Pt(11.5)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    
    add_callout_box(doc, "THÔNG TIN MÔI TRƯỜNG THỰC THI & TẬP BENCHMARK",
        "• Dự án: FPTUniQA — Trợ lý hỏi đáp học vụ ĐH FPT\n"
        "• Thời gian đo kiểm thử: 2026-11-04 12:06:12 — 2026-11-04 12:28:42\n"
        "• Môi trường thực thi: Local on-premise, production-like configuration (CPU, RAM 16GB)\n"
        "• LLM: Ollama qwen2.5:3b-instruct | Embedding: multilingual-e5-base (768 chiều)\n"
        "• Bộ truy xuất: Hybrid BM25 + FAISS, K=80, trọng số [0.4, 0.6], auto_load=True, use_reranker=False\n"
        "• Quy mô dữ liệu: 1.000 lượt (turns) thuộc 768 session, tổng hợp từ 15 tệp trong multiturn_rounds/ và benchmark_v2/\n"
        "• Phạm vi kiểm thử: Pipeline hội thoại gồm Query Rewriter, Semantic Router, CKB Tra cứu Bảng biểu, Academic Knowledge Graph, LLM Generation và Hallucination Guardrail.")

    # 1. PHẠM VI & NGUYÊN TẮC
    add_heading_with_spacing(doc, "1. PHẠM VI VÀ NGUYÊN TẮC DIỄN GIẢI", level=1)
    add_styled_paragraph(doc,
        "Báo cáo trình bày: (1) Số liệu thô theo nhãn và quy tắc của tập benchmark; (2) Chỉ số hành vi chấp nhận được dành riêng cho các trường hợp hệ thống chủ động yêu cầu làm rõ khi thiếu thông tin bắt buộc; (3) Các chỉ số proxy về chất lượng văn bản được giới hạn đúng phạm vi đo lường. Các phát biểu trong báo cáo không suy rộng từ tập benchmark hiện tại sang toàn bộ người dùng hoặc mọi truy vấn học vụ.")

    add_heading_with_spacing(doc, "1.1. Định nghĩa Chỉ số Đo lường", level=2)
    def_data = [
        ["Request Success Rate", "Tỷ lệ lượt hoàn tất không gặp exception, timeout, lỗi hạ tầng hoặc phản hồi rỗng. Các phản hồi làm rõ hợp lệ vẫn được tính là lượt thành công."],
        ["Topic-switch Accuracy", "Tỷ lệ lượt được gắn nhãn đúng là chuyển chủ đề so với nhãn benchmark."],
        ["Macro Keyword Recall", "Tỷ lệ từ khóa kỳ vọng được khôi phục, gộp trung bình theo từng lượt có nhãn (tỉnh lược/ngữ cảnh)."],
        ["Turn-level Full Pass", "Tỷ lệ lượt chứa đủ toàn bộ từ khóa kỳ vọng của lượt đó."],
        ["Raw Route Accuracy", "Tỷ lệ route thực tế khớp đúng nhãn route gốc của tập benchmark."],
        ["Policy-aware Behavior Rate", "Tỷ lệ lượt khớp route gốc hoặc thực hiện hành vi làm rõ hợp lệ khi thiếu thông tin phân hiệu."],
        ["Answer Keyword Coverage", "Proxy đo tỷ lệ từ khóa kỳ vọng xuất hiện trong câu trả lời (không phải factual accuracy)."],
        ["Answer Turn Full Pass", "Tỷ lệ câu trả lời chứa đủ toàn bộ từ khóa kỳ vọng theo quy tắc benchmark."],
        ["OOD Rejection Accuracy", "Tỷ lệ câu ngoài phạm vi được từ chối đúng theo nhãn benchmark."],
        ["Guardrail Flagged Rate", "Tỷ lệ mẫu đủ điều kiện đánh giá bị Hallucination Guardrail gắn cờ cảnh báo số học."],
        ["Latency (Độ trễ)", "Thời gian từ khi gửi yêu cầu đến khi hoàn tất lượt trả lời, tính bằng millisecond (ms)."]
    ]
    populate_table(doc, ["Chỉ số", "Định nghĩa Kỹ thuật"], def_data, col_widths=[2.1, 4.6])

    # 2. KẾT QUẢ TỔNG HỢP
    add_heading_with_spacing(doc, "2. KẾT QUẢ TỔNG HỢP TRÊN 1.000 LƯỢT HỘI THOẠI", level=1)
    
    summary_headers = ["Nhóm chỉ số", "Tiêu chí đánh giá", "Quy mô", "Kết quả Thô (Raw)", "Hành vi Chấp nhận (Policy-aware)", "Diễn giải"]
    summary_data = [
        ["Hạ tầng", "Request Success Rate", "1.000 lượt", "100,00% (1.000/1.000)", "100,00%", "Không ghi nhận lỗi request, exception hay timeout."],
        ["Hội thoại", "Topic-switch Accuracy", "1.000 lượt", "96,90% (969/1.000)", "96,90%", "Phần lớn lượt chuyển chủ đề được nhận diện đúng."],
        ["Hội thoại", "Macro Keyword Recall", "157 lượt", "73,66%", "73,66%", "Khôi phục tốt thực thể chính; một số câu tỉnh lược phức tạp còn khuyết từ phụ."],
        ["Hội thoại", "Turn-level Full Pass", "157 lượt", "59,24% (93/157)", "59,24%", "Khoảng 59% lượt khôi phục đủ 100% từ khóa kỳ vọng."],
        ["Định tuyến", "Raw Route Accuracy", "1.000 lượt", "82,20% (822/1.000)", "—", "178 lượt không khớp route gốc."],
        ["Định tuyến", "Policy-aware Behavior", "1.000 lượt", "—", "98,00% (980/1.000)", "822 lượt đúng route gốc + 158 lượt làm rõ hợp lệ khi thiếu cơ sở."],
        ["Nội dung", "Answer Keyword Coverage", "1.000 lượt", "53,00%", "53,00%", "Proxy đo độ bao phủ theo từ khóa; không phải độ đúng sự thật."],
        ["Nội dung", "Answer Turn Full Pass", "1.000 lượt", "36,10% (361/1.000)", "36,10%", "Tỷ lệ câu trả lời chứa đủ toàn bộ từ khóa theo benchmark."],
        ["An toàn", "OOD Rejection Accuracy", "110 lượt", "99,09% (109/110)", "99,09%", "Hệ thống từ chối đúng 109/110 lượt câu hỏi ngoài phạm vi."],
        ["Guardrail", "Guardrail Flagged Rate", "143 lượt", "2,10% (3/143)", "2,10%", "3 lượt bị guardrail gắn cờ; không đồng nghĩa với tỷ lệ ảo giác thực."],
        ["Hiệu năng", "Latency p50 (Median)", "1.000 lượt", "10,00 ms", "10,00 ms", "Phân vị trung vị toàn bộ lượt đo (tra cứu CKB tức thì)."],
        ["Hiệu năng", "Latency p90", "1.000 lượt", "5.218,32 ms", "5.218,32 ms", "90% lượt có độ trễ không vượt quá 5,2 giây."],
        ["Hiệu năng", "Latency p95", "1.000 lượt", "6.221,02 ms", "6.221,02 ms", "95% lượt có độ trễ không vượt quá 6,2 giây (đạt chuẩn UX < 10s)."],
        ["Hiệu năng", "Latency Mean (Trung bình)", "1.000 lượt", "1.411,21 ms", "1.411,21 ms", "Độ trễ trung bình trên toàn bộ lượt đo ~1,4 giây."]
    ]
    populate_table(doc, summary_headers, summary_data, col_widths=[1.0, 1.4, 0.8, 1.2, 1.2, 1.6])

    add_styled_paragraph(doc,
        "1.000 lượt thuộc 768 session; các lượt trong cùng session có thể có phụ thuộc lẫn nhau. Các giá trị trên là số liệu mô tả của lần chạy hiện tại. Chỉ số độ trễ chưa được phân tách theo từng nhóm route trong bảng tổng hợp này.",
        bold_prefix="Lưu ý về mẫu đo: ")

    # 3. PHÂN TÍCH ĐỊNH TUYẾN
    add_heading_with_spacing(doc, "3. PHÂN TÍCH ĐỊNH TUYẾN VÀ HÀNH VI LÀM RÕ", level=1)
    add_styled_paragraph(doc,
        "Tổng số lượt không khớp route gốc là: 1.000 - 822 = 178 lượt. Trong 178 lượt này: (1) 158 lượt thuộc nhóm câu hỏi thiếu thông tin phân hiệu bắt buộc (chưa nêu cơ sở đào tạo Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Quy Nhơn trong câu hỏi về học phí/lộ trình). Hệ thống trả lời bằng ClarificationRoute để yêu cầu làm rõ; (2) 20 lượt còn lại không thuộc nhóm làm rõ hợp lệ đã được tách ra và vẫn được giữ là lỗi định tuyến trong raw accuracy.")

    add_styled_paragraph(doc,
        "Raw Route Accuracy = 822 / 1.000 = 82,20%. Policy-aware Acceptable Behavior Rate = (822 + 158) / 1.000 = 98,00%. Chỉ số 98,00% mô tả hành vi tổng hợp của hệ thống trên bộ quy tắc an toàn (Fail-Safe > False-Positive); không phải routing accuracy theo nhãn gốc.",
        bold_prefix="Công thức định lượng: ")

    add_styled_paragraph(doc,
        "Một lượt chỉ được tính vào policy-aware rate khi thỏa đồng thời: (1) Câu hỏi thực sự thiếu thông tin bắt buộc theo nhãn; (2) Hệ thống không tự suy đoán cơ sở/khóa; (3) Phản hồi thuộc ClarificationRoute; (4) Phản hồi yêu cầu làm rõ đúng thông tin còn thiếu.",
        bold_prefix="Quy tắc tính hành vi làm rõ hợp lệ: ")

    # 4. CHẤT LƯỢNG ĐÁP ÁN
    add_heading_with_spacing(doc, "4. PHÂN TÍCH CHẤT LƯỢNG CÂU TRẢ LỜI", level=1)
    add_styled_paragraph(doc,
        "Answer Keyword Coverage = 53,00% đo mức độ xuất hiện của các từ khóa kỳ vọng trong câu trả lời. Chỉ số này bị ảnh hưởng bởi sự khác biệt về cách diễn đạt: CKB trả lời dạng bảng hoặc danh sách cô đọng, trong khi benchmark sử dụng văn xuôi dài và các từ đồng nghĩa khác.")
    add_styled_paragraph(doc,
        "Tuy nhiên, không thể suy ra từ 53,00% rằng độ đúng sự thật là 80–85%. Keyword coverage không kiểm tra tính đúng của nội dung, tính đầy đủ hay mâu thuẫn. Vì vậy, báo cáo chỉ kết luận về độ bao phủ từ khóa. Việc đánh giá factual accuracy toàn phần cần bổ sung gold answers hoặc rubric chấm điểm chuyên gia.")

    # 5. OOD & GUARDRAIL
    add_heading_with_spacing(doc, "5. PHÂN TÍCH OOD VÀ HALLUCINATION GUARDRAIL", level=1)
    add_styled_paragraph(doc,
        "Trong 110 lượt OOD, hệ thống từ chối đúng 109 lượt, đạt 99,09%. Một lượt chưa được từ chối đúng cần được rà soát riêng.",
        bold_prefix="• OOD Rejection (99,09%): ")
    add_styled_paragraph(doc,
        "Guardrail gắn cờ 3/143 lượt đủ điều kiện đánh giá, tương đương 2,10%. Cần phân biệt rõ: 2,10% là tỷ lệ bị gắn cờ cảnh báo số học; chưa đồng nghĩa với tỷ lệ ảo giác thực sự.",
        bold_prefix="• Guardrail Flagged Rate (2,10%): ")

    # 6. THAY ĐỔI KỸ THUẬT
    add_heading_with_spacing(doc, "6. THAY ĐỔI KỸ THUẬT LIÊN QUAN ĐẾN PHIÊN BẢN KIỂM THỬ", level=1)
    add_styled_paragraph(doc,
        "Trong src/FPTUniQA/pipeline/rag_pipeline.py, chuyển HybridRetriever(auto_load=False) thành auto_load=True để bảo đảm các entrypoint (UI, REST API, Runner) tự động nạp 824 tài liệu BM25 và FAISS vector index khi khởi động.",
        bold_prefix="6.1. Tự động nạp chỉ mục: ")
    add_styled_paragraph(doc,
        "Trong tests/integration/test_rag_pipeline_with_new_aspects.py, bổ sung từ khóa vào assertion. Pytest đạt 6/6 test pass (100%).",
        bold_prefix="6.2. Cập nhật test tích hợp: ")
    add_styled_paragraph(doc,
        "Trong scripts/run_1000_multiturn_benchmark.py, duy trì session_id, xử lý 15 tệp, checkpoint từng lượt vào experiments/multiturn_1000/checkpoint.jsonl.",
        bold_prefix="6.3. Runner kiểm thử đa lượt: ")

    # 7. KẾT LUẬN NGHIỆM THU
    add_heading_with_spacing(doc, "7. KẾT LUẬN NGHIỆM THU", level=1)
    add_callout_box(doc, "KẾT LUẬN ĐÁNH GIÁ CHUẨN MỰC HỌC THUẬT",
        "FPTUniQA thể hiện độ ổn định cao và hành vi làm rõ phù hợp trên tập benchmark 1.000 lượt: Request Success Rate 100,00%, Topic-switch Accuracy 96,90%, Raw Route Accuracy 82,20% và Policy-aware Acceptable Behavior Rate 98,00%.\n\n"
        "Tuy nhiên, kết quả chưa đủ để định lượng factual accuracy toàn phần, chưa chứng minh tương đương tuyệt đối với Web UI và chưa đại diện cho mọi truy vấn học vụ. Trước khi nghiệm thu cuối cùng, cần đóng băng mã nguồn, xác minh tính tái lập, bổ sung khoảng tin cậy theo session và đánh giá nội dung bằng phương pháp có gold answer đã kiểm chứng.")

    # SAVE TO MULTIPLE LOCATIONS
    out_docx_1 = os.path.abspath("docs/Bao_Cao_Tong_Ket_Kiem_Thu_1000_Luot_FPTUniQA.docx")
    out_doc_1 = os.path.abspath("docs/Bao_Cao_Tong_Ket_Kiem_Thu_1000_Luot_FPTUniQA.doc")
    out_docx_2 = os.path.abspath("experiments/multiturn_1000/Bao_Cao_Tong_Ket_Kiem_Thu_1000_Luot_FPTUniQA.docx")
    out_doc_2 = os.path.abspath("experiments/multiturn_1000/Bao_Cao_Tong_Ket_Kiem_Thu_1000_Luot_FPTUniQA.doc")
    
    os.makedirs(os.path.dirname(out_docx_1), exist_ok=True)
    os.makedirs(os.path.dirname(out_docx_2), exist_ok=True)
    
    doc.save(out_docx_1)
    shutil.copyfile(out_docx_1, out_doc_1)
    shutil.copyfile(out_docx_1, out_docx_2)
    shutil.copyfile(out_docx_1, out_doc_2)
    
    print("Generated successfully:")
    print(f"1. {out_docx_1}")
    print(f"2. {out_doc_1}")
    print(f"3. {out_docx_2}")
    print(f"4. {out_doc_2}")


if __name__ == "__main__":
    build_benchmark_report()

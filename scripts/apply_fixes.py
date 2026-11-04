"""Script thực hiện các cải tiến cho hệ thống FPTUniQA dựa trên dữ liệu log kiểm thử.
Các vấn đề được khắc phục:
1. semantic_parser.py:
   - Thêm nhận diện 'tien', 'tiền' kết hợp ngành/khóa/phân hiệu vào is_tuition.
   - Bổ sung tên ngành đào tạo vào academic_keywords.
   - Sửa fallback OOD confidence thành 0.50 (thay vì 0.95).
   - Sửa try_rule_fast_parse: sửa NameError normalizer và điều kiện OOD (chỉ kích hoạt khi có OOD_KEYWORDS).
2. safety_gate.py:
   - Bổ sung check_chitchat() xử lý câu hỏi danh tính bot, khen tốc độ, chào hỏi, cảm ơn.
3. rag_pipeline.py:
   - Tích hợp check_chitchat() tại Bước 0.1 (<5ms), lưu session với topic_switch_detected=True.
4. rewriting.py:
   - Cập nhật is_self_contained_query() để coi câu hỏi về nội dung/chương trình đào tạo của một ngành là độc lập (không dính cơ sở cũ).
   - Thêm quy tắc Chitchat và không đổi ngành/cơ sở vào REWRITER_SYSTEM_PROMPT.
5. prompt.py:
   - Lọc bỏ các câu trả lời OOD khỏi history để LLM không lặp lại lời từ chối.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def patch_semantic_parser():
    file_path = ROOT / "src" / "FPTUniQA" / "query" / "semantic_parser.py"
    content = file_path.read_text(encoding="utf-8")

    # 1. Bổ sung money words vào is_tuition
    old_tuition = """    is_tuition = is_common_fee or has_tuition_entity or any(kw in q_lower for kw in [
        "học phí", "hoc phi", "tiền học", "tien hoc", "chi phí", "chi phi", "khoản phí", "khoan phi",
        "lệ phí", "le phi", "biểu phí", "bieu phi", "phí bảo hiểm", "bảo hiểm y tế"
    ]) or (
        ("tín chỉ" in q_lower or "tin chi" in q_lower) and any(kw in q_lower for kw in [
            "bao nhiêu tiền", "giá", "mức phí", "đóng tiền", "một tín chỉ", "1 tín chỉ", "bao nhieu tien"
        ])
    )"""

    new_tuition = """    has_money_word = bool(re.search(r"\\b(tiền|tien|phí|phi|mức phí|muc phi)\\b", q_lower))
    is_tuition = is_common_fee or has_tuition_entity or any(kw in q_lower for kw in [
        "học phí", "hoc phi", "tiền học", "tien hoc", "chi phí", "chi phi", "khoản phí", "khoan phi",
        "lệ phí", "le phi", "biểu phí", "bieu phi", "phí bảo hiểm", "bảo hiểm y tế"
    ]) or (
        has_money_word and any(kw in q_lower for kw in [
            "cntt", "ai", "ktpm", "attt", "qtkd", "mkt", "ib", "ds",
            "k17", "k18", "k19", "k20", "k21", "k22", "2026", "2025", "2024", "2023",
            "quy nhơn", "quy nhon", "cần thơ", "can tho", "hà nội", "ha noi", "đà nẵng", "da nang", "hcm", "tphcm"
        ])
    ) or (
        ("tín chỉ" in q_lower or "tin chi" in q_lower) and any(kw in q_lower for kw in [
            "bao nhiêu tiền", "giá", "mức phí", "đóng tiền", "một tín chỉ", "1 tín chỉ", "bao nhieu tien"
        ])
    )"""

    assert old_tuition in content, "old_tuition not found in semantic_parser.py"
    content = content.replace(old_tuition, new_tuition, 1)

    # 2. Bổ sung academic_keywords & giảm fallback OOD confidence
    old_academic = """    academic_keywords = [
        "học", "hoc", "sinh viên", "sinh vien", "trường", "truong", "thi", "điểm", "diem",
        "học kỳ", "hoc ky", "tiếng anh", "tieng anh", "ngoại ngữ", "ngoai ngu",
        "chương trình", "chuong trinh", "đào tạo", "dao tao", "chứng chỉ", "chung chi",
        "môn", "mon", "ngành", "nganh", "khóa", "khoa", "tín chỉ", "tin chi"
    ]
    if has_academic_entities or any(kw in q_lower for kw in academic_keywords) or re.search(r"\\b(kỳ|ky|kỳ học|ky hoc|mức độ|muc do|k\\d{2})\\b", q_lower):
        return {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "slots": {},
            "confidence": 0.75,
        }

    return {
        "intent": QueryIntent.OOD.value,
        "slots": {},
        "confidence": 0.95,
    }"""

    new_academic = """    academic_keywords = [
        "học", "hoc", "sinh viên", "sinh vien", "trường", "truong", "thi", "điểm", "diem",
        "học kỳ", "hoc ky", "tiếng anh", "tieng anh", "ngoại ngữ", "ngoai ngu",
        "chương trình", "chuong trinh", "đào tạo", "dao tao", "chứng chỉ", "chung chi",
        "môn", "mon", "ngành", "nganh", "khóa", "khoa", "tín chỉ", "tin chi",
        "cntt", "ktpm", "attt", "qtkd", "mkt", "ib", "ds"
    ]
    if has_academic_entities or any(kw in q_lower for kw in academic_keywords) or re.search(r"\\b(kỳ|ky|kỳ học|ky hoc|mức độ|muc do|k\\d{2})\\b", q_lower):
        prog = norm_res.slots_hint.get("program") if norm_res else None
        slots_out = {"program": prog} if prog else {}
        return {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "slots": slots_out,
            "confidence": 0.75,
        }

    return {
        "intent": QueryIntent.OOD.value,
        "slots": {},
        "confidence": 0.50,
    }"""

    assert old_academic in content, "old_academic not found in semantic_parser.py"
    content = content.replace(old_academic, new_academic, 1)

    # 3. Sửa try_rule_fast_parse
    old_fast_parse = """def try_rule_fast_parse(question: str) -> Optional[ParsedQuery]:
    \"\"\"Bỏ qua LLM Parser đối với các câu hỏi rule-based có độ tin cậy cao để giảm p95 latency.\"\"\"
    norm_res = None
    try:
        norm_res = normalizer.normalize(question)
    except Exception:
        pass

    regex_dict = _parse_with_regex(question, norm_res=norm_res)
    conf = regex_dict.get("confidence", 0.0)
    intent = regex_dict.get("intent", "")
    slots = regex_dict.get("slots", {}) or {}

    # 1. Câu hỏi OOD rõ ràng
    is_ood = (intent == QueryIntent.OOD.value) or any(kw in question.lower() for kw in OOD_KEYWORDS)
    # 2. Câu hỏi course đã xác thực mã môn trong CKB
    has_valid_course = bool(slots.get("course_code")) and (slots.get("course_code") in _get_known_course_codes())
    # 3. Câu hỏi structured tuition đủ program và (cohort hoặc campus)
    is_structured_tuition = (
        intent in [QueryIntent.TUITION_LOOKUP.value, QueryIntent.POLICY_LOOKUP.value]
        and bool(slots.get("program"))
        and (bool(slots.get("cohort")) or bool(slots.get("campus")))
    )

    if (is_ood and conf >= 0.85) or (has_valid_course and conf >= 0.85) or (is_structured_tuition and conf >= 0.85):
        parsed = ParsedQuery(
            intent=intent,
            slots=slots,
            confidence=conf,
            raw_query=question,
            parser_method="rule_fast_path",
            fallback_used=False,
        )
        return parsed

    return None"""

    new_fast_parse = """def try_rule_fast_parse(question: str) -> Optional[ParsedQuery]:
    \"\"\"Bỏ qua LLM Parser đối với các câu hỏi rule-based có độ tin cậy cao để giảm p95 latency.\"\"\"
    norm_res = None
    try:
        from FPTUniQA.normalization.engine import get_entity_normalizer
        norm_res = get_entity_normalizer().normalize(question)
    except Exception:
        pass

    regex_dict = _parse_with_regex(question, norm_res=norm_res)
    conf = regex_dict.get("confidence", 0.0)
    intent = regex_dict.get("intent", "")
    slots = regex_dict.get("slots", {}) or {}

    # 1. Câu hỏi OOD rõ ràng: CHỈ kích hoạt khi câu hỏi thực sự chứa từ khóa ngoài phạm vi (OOD_KEYWORDS)
    is_explicit_ood = any(kw in question.lower() for kw in OOD_KEYWORDS)
    # 2. Câu hỏi course đã xác thực mã môn trong CKB
    has_valid_course = bool(slots.get("course_code")) and (slots.get("course_code") in _get_known_course_codes())
    # 3. Câu hỏi structured tuition đủ program và (cohort hoặc campus)
    is_structured_tuition = (
        intent in [QueryIntent.TUITION_LOOKUP.value, QueryIntent.POLICY_LOOKUP.value]
        and bool(slots.get("program"))
        and (bool(slots.get("cohort")) or bool(slots.get("campus")))
    )

    if (is_explicit_ood and conf >= 0.85) or (has_valid_course and conf >= 0.85) or (is_structured_tuition and conf >= 0.85):
        parsed = ParsedQuery(
            intent=intent,
            slots=slots,
            confidence=conf,
            raw_query=question,
            parser_method="rule_fast_path",
            fallback_used=False,
        )
        return parsed

    return None"""

    assert old_fast_parse in content, "old_fast_parse not found in semantic_parser.py"
    content = content.replace(old_fast_parse, new_fast_parse, 1)

    file_path.write_text(content, encoding="utf-8")
    print("Patch semantic_parser.py thành công!")


def patch_safety_gate():
    file_path = ROOT / "src" / "FPTUniQA" / "query" / "safety_gate.py"
    content = file_path.read_text(encoding="utf-8")

    chitchat_code = '''
# Bộ nhận diện Chitchat / Greeting / Identity (<5ms)
_CHITCHAT_PATTERNS = [
    (
        "identity",
        re.compile(
            r"^\\s*(bạn|mày|em|m|bot)\\s+(là\\s+ai|la\\s+ai|tên\\s+gì|ten\\s+gi|có\\s+thể\\s+làm\\s+gì|giúp\\s+được\\s+gì)\\b|"
            r"^\\s*(ai\\s+tạo\\s+ra\\s+(bạn|mày|em|bot)|who\\s+are\\s+you|what\\s+is\\s+your\\s+name|giới\\s+thiệu\\s+(về\\s+)?(bản\\s+thân|bạn|bot))\\b",
            re.IGNORECASE,
        ),
        (
            "Xin chào! Tôi là **FPTUniQA** — Trợ lý ảo tư vấn Quy chế đào tạo, Chương trình học và Học phí "
            "của Đại học FPT.\\n\\nTôi có thể hỗ trợ bạn:\\n"
            "- 💰 **Học phí & Biểu phí:** Tra cứu mức học phí theo khóa (K17–K22) và phân hiệu (Hà Nội, Cần Thơ, Quy Nhơn, Đà Nẵng, TP.HCM).\\n"
            "- 📚 **Môn học & Tiên quyết:** Tra cứu điều kiện tiên quyết (ví dụ: SWP391, PRO192), giáo trình và chuẩn đầu ra.\\n"
            "- 📜 **Quy chế học vụ:** Điều kiện thi, quy định điểm danh, cảnh cáo học vụ, thực tập OJT và xét tốt nghiệp.\\n\\n"
            "Bạn có câu hỏi học vụ nào cần tôi hỗ trợ không?"
        ),
    ),
    (
        "speed",
        re.compile(
            r"^\\s*(sao\\s+)?(m\\s+|mày\\s+|bạn\\s+|bot\\s+|em\\s+)?(nhanh\\s+(v|vậy|the|thế|qua|quá))\\b|"
            r"^\\s*sao\\s+nhanh\\s+(v|vậy|the|thế)\\b",
            re.IGNORECASE,
        ),
        (
            "FPTUniQA được tối ưu hóa với cơ chế truy xuất dữ liệu có cấu trúc (SSOT) và bộ chỉ mục Hybrid Retriever "
            "cục bộ, giúp tra cứu thông tin học vụ Đại học FPT chính xác với thời gian phản hồi gần như tức thì. "
            "Bạn cần tra cứu thêm thông tin gì về quy chế hay học phí không?"
        ),
    ),
    (
        "greeting",
        re.compile(
            r"^\\s*(xin\\s+chào|chào\\s+bạn|chào\\s+bot|chao\\s+ban|chao\\s+bot|hello|hi|hey)\\s*[!.]*$",
            re.IGNORECASE,
        ),
        (
            "Xin chào bạn! Tôi là FPTUniQA, trợ lý học vụ Đại học FPT. "
            "Tôi có thể hỗ trợ bạn tra cứu biểu phí, môn học hay quy chế đào tạo nào hôm nay?"
        ),
    ),
    (
        "thanks",
        re.compile(
            r"^\\s*(cảm\\s+ơn|cam\\s+on|thank\\s+you|thanks)(\\s+(bạn|bot|nhiều|nhe|nhé))?\\s*[!.]*$",
            re.IGNORECASE,
        ),
        (
            "Rất vui được hỗ trợ bạn! Nếu còn thắc mắc nào về học vụ hoặc quy chế ĐH FPT, bạn cứ hỏi nhé. "
            "Chúc bạn học tập thật tốt!"
        ),
    ),
]


def check_chitchat(query: str) -> Optional[Dict[str, Any]]:
    \"\"\"Nhận diện các truy vấn Chitchat / Greeting / Identity để phản hồi nhanh mà không qua RAG.\"\"\"
    if not query or not query.strip():
        return None
    q_strip = query.strip()
    for cat, pattern, reply in _CHITCHAT_PATTERNS:
        if pattern.search(q_strip):
            return {
                "category": cat,
                "answer": reply,
                "route": "chitchat",
            }
    return None
'''

    if "def check_chitchat" not in content:
        content += "\n" + chitchat_code
        file_path.write_text(content, encoding="utf-8")
        print("Patch safety_gate.py thành công!")


def patch_rag_pipeline():
    file_path = ROOT / "src" / "FPTUniQA" / "pipeline" / "rag_pipeline.py"
    content = file_path.read_text(encoding="utf-8")

    old_step0 = """            # Bước 0: Safety Pre-gate (tiền kiểm tra an toàn và Near-OOD <50ms)
            gate_res = safety_precheck(query)
            if gate_res and gate_res.get("blocked"):
                latency_ms = round((time.time() - start_time) * 1000, 2)
                log_query_event(
                    original_query=query,
                    rewritten_query=query,
                    parsed_query={"intent": "ood", "slots": {}},
                    answer=gate_res.get("answer", ""),
                    route_chosen="ood",
                    latency_ms=latency_ms,
                    session_id=session_id,
                )
                return {
                    "answer": gate_res.get("answer", ""),
                    "route": "ood",
                    "sources": [],
                    "latency_ms": latency_ms,
                    "confidence": 1.0,
                    "model": "safety_gate",
                    "history": [],
                }

            # Lấy lịch sử hội thoại của session (nếu có)"""

    new_step0 = """            # Bước 0: Safety Pre-gate (tiền kiểm tra an toàn và Near-OOD <50ms)
            gate_res = safety_precheck(query)
            if gate_res and gate_res.get("blocked"):
                latency_ms = round((time.time() - start_time) * 1000, 2)
                log_query_event(
                    original_query=query,
                    rewritten_query=query,
                    parsed_query={"intent": "ood", "slots": {}},
                    answer=gate_res.get("answer", ""),
                    route_chosen="ood",
                    latency_ms=latency_ms,
                    session_id=session_id,
                )
                return {
                    "answer": gate_res.get("answer", ""),
                    "route": "ood",
                    "sources": [],
                    "latency_ms": latency_ms,
                    "confidence": 1.0,
                    "model": "safety_gate",
                    "history": [],
                }

            # Bước 0.1: Chitchat / Persona Gate (<5ms, không làm bẩn ngữ cảnh đa lượt)
            from FPTUniQA.query.safety_gate import check_chitchat
            chitchat_res = check_chitchat(query)
            if chitchat_res:
                latency_ms = round((time.time() - start_time) * 1000, 2)
                if session_id:
                    self.session_manager.add_turn(
                        session_id=session_id,
                        query=query,
                        rewritten_query=query,
                        answer=chitchat_res["answer"],
                        route_chosen="chitchat",
                        parsed_query={"intent": "chitchat", "slots": {}},
                        topic_switch_detected=True,
                    )
                return {
                    "answer": chitchat_res["answer"],
                    "route": "chitchat",
                    "citations": [],
                    "sources": [],
                    "latency_ms": latency_ms,
                    "confidence": 1.0,
                    "model": "chitchat_gate",
                    "rewritten_query": query,
                    "session_id": session_id,
                    "possible_hallucination": False,
                }

            # Lấy lịch sử hội thoại của session (nếu có)"""

    assert old_step0 in content, "old_step0 not found in rag_pipeline.py"
    content = content.replace(old_step0, new_step0, 1)
    file_path.write_text(content, encoding="utf-8")
    print("Patch rag_pipeline.py thành công!")


def patch_rewriting():
    file_path = ROOT / "src" / "FPTUniQA" / "query" / "rewriting.py"
    content = file_path.read_text(encoding="utf-8")

    # 1. Thêm quy tắc 11 và 12 vào REWRITER_SYSTEM_PROMPT
    old_prompt = """9. KHÔNG thêm lời giải thích, lời chào hoặc bất kỳ văn bản phụ trợ nào.
10. Chỉ trả về DUY NHẤT một câu hỏi đã viết lại trên một dòng."""

    new_prompt = """9. KHÔNG thêm lời giải thích, lời chào hoặc bất kỳ văn bản phụ trợ nào.
10. Chỉ trả về DUY NHẤT một câu hỏi đã viết lại trên một dòng.
11. Khi câu hỏi hiện tại là câu chào hỏi, hỏi danh tính bot, cảm thán (ví dụ: "bạn là ai", "sao nhanh vậy", "xin chào"), TUYỆT ĐỐI KHÔNG ghép ngành, khóa hay mã môn từ lịch sử vào. Hãy giữ nguyên câu hỏi.
12. Khi sinh viên hỏi về một ngành học mới (ví dụ: "ngành AI học gì"), TUYỆT ĐỐI KHÔNG ghép cơ sở (Quy Nhơn, Cần Thơ...) hay ngành cũ từ lịch sử vào."""

    assert old_prompt in content, "old_prompt not found in rewriting.py"
    content = content.replace(old_prompt, new_prompt, 1)

    # 2. Thêm quy tắc câu hỏi chương trình học ngành tổng quan vào is_self_contained_query
    old_self_contained = """    # 5. Câu hỏi học phí đã đủ cả khóa + ngành + cơ sở
    has_cohort = bool(re.search(r"\\b(K1[7-9]|K2[0-2]|202[0-6])\\b", query, re.IGNORECASE))
    has_campus = bool(re.search(CAMPUS_NAMES_REGEX, q_clean) or re.search(CAMPUS_CODES_REGEX, q_clean))
    has_major = any(m.lower() in q_clean for m in MAJOR_NAMES) or bool(re.search(r"\\b(ai|cntt|ktpm|attt|qtkd|mkt|ib|ds)\\b", q_clean))
    if has_cohort and has_major and has_campus:
        return True

    return False"""

    new_self_contained = """    # 5. Câu hỏi học phí đã đủ cả khóa + ngành + cơ sở
    has_cohort = bool(re.search(r"\\b(K1[7-9]|K2[0-2]|202[0-6])\\b", query, re.IGNORECASE))
    has_campus = bool(re.search(CAMPUS_NAMES_REGEX, q_clean) or re.search(CAMPUS_CODES_REGEX, q_clean))
    has_major = any(m.lower() in q_clean for m in MAJOR_NAMES) or bool(re.search(r"\\b(ai|cntt|ktpm|attt|qtkd|mkt|ib|ds)\\b", q_clean))
    if has_cohort and has_major and has_campus:
        return True

    # 6. Câu hỏi tổng quan về chương trình học / nội dung đào tạo của một ngành cụ thể
    # Ví dụ: "ngành ai học những gì", "ngành AI học gì", "chương trình đào tạo ngành KTPM"
    has_curriculum_aspect = any(kw in q_clean for kw in [
        "học những gì", "học gì", "hoc gi", "hoc nhung gi",
        "chương trình học", "chuong trinh hoc", "khung chương trình", "khung chuong trinh",
        "đào tạo những gì", "dao tao nhung gi", "ra trường làm gì"
    ])
    if has_major and has_curriculum_aspect and not has_continuation_prefix:
        return True

    return False"""

    assert old_self_contained in content, "old_self_contained not found in rewriting.py"
    content = content.replace(old_self_contained, new_self_contained, 1)

    file_path.write_text(content, encoding="utf-8")
    print("Patch rewriting.py thành công!")


def patch_prompt():
    file_path = ROOT / "src" / "FPTUniQA" / "generation" / "prompt.py"
    content = file_path.read_text(encoding="utf-8")

    old_hist = """        for turn in history[-3:]:
            ans = (turn.get("answer") or "").strip()
            # Bỏ qua câu trả lời negative fallback để tránh LLM lặp lại nội dung cũ
            if "không tìm thấy thông tin này trong tài liệu" in ans:
                continue
            history_lines.append(f"Sinh viên: {turn.get('query', '')}")
            history_lines.append(f"Trợ lý: {ans}")"""

    new_hist = """        for turn in history[-3:]:
            ans = (turn.get("answer") or "").strip()
            # Bỏ qua câu trả lời negative fallback và OOD refusal để tránh LLM lặp lại lời từ chối cũ
            if any(phrase in ans.lower() for phrase in [
                "không tìm thấy thông tin này trong tài liệu",
                "nằm ngoài phạm vi",
                "ngoài phạm vi"
            ]):
                continue
            history_lines.append(f"Sinh viên: {turn.get('query', '')}")
            history_lines.append(f"Trợ lý: {ans}")"""

    assert old_hist in content, "old_hist not found in prompt.py"
    content = content.replace(old_hist, new_hist, 1)
    file_path.write_text(content, encoding="utf-8")
    print("Patch prompt.py thành công!")


if __name__ == "__main__":
    patch_semantic_parser()
    patch_safety_gate()
    patch_rag_pipeline()
    patch_rewriting()
    patch_prompt()
    print("HOÀN THÀNH TOÀN BỘ CÁC BƯỚC CẢI TIẾN!")

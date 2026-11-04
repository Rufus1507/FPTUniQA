"""Module Semantic Parsing chuyển đổi câu hỏi tự nhiên thành truy vấn có cấu trúc (Contract 3). Phụ trách: TV3.

Chiến lược:
1. LLM Structured Output (Chính): Gọi LLM sinh JSON có cấu trúc gồm intent, slots, confidence.
2. Regex / Rule-based (Fallback): Tự động kích hoạt khi lời gọi LLM gặp lỗi (mạng, JSON hỏng, thiếu field).
"""

import json
import re
from typing import Any, Dict, Optional
import requests

try:
    from contracts import ParsedQuery
except ImportError:
    import sys
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from contracts import ParsedQuery
from FPTUniQA.query.campus_matcher import match_campus
from FPTUniQA.query.constants import (
    MAJOR_TO_SHORT_CODE,
    OOD_KEYWORDS,
    PROGRAM_ALIAS_MAP,
)
from FPTUniQA.query.intent import QueryIntent, SUPPORTED_INTENTS
from FPTUniQA.query.normalizer import normalize_query
from FPTUniQA.utils.config import config
from FPTUniQA.utils.exceptions import CircuitBreaker, CircuitBreakerOpenError
from FPTUniQA.utils.logger import get_logger

# Regex chuẩn hóa mã môn học (3 chữ cái + 3 chữ số + hậu tố tùy chọn, ví dụ PRF192, AIL302m, NWC203c)
COURSE_CODE_REGEX = re.compile(r"\b([a-zA-Z]{3}\d{3}[a-zA-Z]?)\b")

def _get_known_course_codes():
    """Lấy danh sách mã môn học hợp lệ từ Curriculum Knowledge Base."""
    try:
        from FPTUniQA.data.structured import StructuredDataParser
        db = StructuredDataParser()
        return {c["course_code"].upper() for c in db.courses_data.get("courses", [])}
    except Exception:
        return set()


logger = get_logger("FPTUniQA.query.semantic_parser")
_parser_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0, name="parser_llm")

# System Prompt chỉ thị LLM trích xuất intent và slots chuẩn xác
PARSER_SYSTEM_PROMPT = """Bạn là bộ phân tích ngữ nghĩa (Semantic Parser) cho hệ thống hỏi đáp quy chế học vụ Đại học FPT.
Nhiệm vụ của bạn là đọc câu hỏi của sinh viên và trích xuất thông tin cấu trúc dưới dạng duy nhất một đối tượng JSON hợp lệ theo lược đồ:

{
  "intent": "policy_lookup" | "tuition_lookup" | "graduation_lookup" | "course_lookup" | "OOD",
  "slots": {
    "program": "string hoặc null (ví dụ: AI, CNTT, KTPM)",
    "cohort": "string hoặc null (ví dụ: 2026, 2023, K18)",
    "campus": "string hoặc null (ví dụ: Cần Thơ, Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Quy Nhơn)",
    "course_code": "string hoặc null (ví dụ: PRF192, PRO192, CSD201, DBI202, SEP490)",
    "course_aspect": "string hoặc null (ví dụ: objective, textbook, prerequisite, credits, assessment)",
    "topic": "string hoặc null (ví dụ: canh_bao_hoc_vu, tot_nghiep, hoc_phi, hoc_bong, mon_hoc)",
    "target": "string hoặc null (ví dụ: dieu_kien, muc_phi, ty_le_vang, tien_quyet)"
  },
  "confidence": float (từ 0.0 đến 1.0)
}

Quy tắc phân loại:
1. "tuition_lookup": Các câu hỏi về học phí, tiền học, chi phí theo ngành hoặc theo khóa hoặc theo phân hiệu/campus.
2. "graduation_lookup": Các câu hỏi về điều kiện tốt nghiệp, chuẩn ngoại ngữ ra trường, đồ án Capstone.
3. "course_lookup": Các câu hỏi về mã môn học cụ thể (ví dụ PRF192, PRO192, CSD201, DBI202, SEP490, SWP391...).
   Quy ước cụ thể cho `course_aspect`:
   - "textbook": hỏi về giáo trình, sách học tập, tài liệu học tập, tác giả (ví dụ: "giáo trình môn PRO192 là sách nào?", "dùng sách gì", "ai viết").
   - "objective": hỏi môn đó học những gì, nội dung học, kiến thức, các chủ đề đào tạo (ví dụ: "môn PRF192 học những gì?", "nội dung học môn DBI202").
   - "prerequisite": môn học tiên quyết.
   - "credits": số tín chỉ môn học.
   - "assessment": hình thức thi, đánh giá (PE, EOS, assignment, đồ án).
   - "semester": kỳ học môn này.
   - "programs": ngành áp dụng.
   - "general": thông tin tổng quan.
4. "policy_lookup": Các câu hỏi về quy chế học vụ chung, cảnh cáo, điểm thi, vắng mặt, học bổng.
5. "OOD": Các câu hỏi ngoài phạm vi đào tạo ĐH FPT (thời tiết, trường đại học khác, đời sống, nấu ăn...).

CHÚ Ý QUAN TRỌNG: Chỉ trả về duy nhất chuỗi JSON thuần túy (không bọc trong markdown ```json, không thêm văn bản phụ trợ)."""


def _parse_with_llm(question: str) -> Optional[Dict[str, Any]]:
    """Gọi LLM qua OpenAI-compatible API để trích xuất intent và slots có cấu trúc."""
    base_url = config.llm_base_url
    api_key = config.llm_api_key
    model_name = config.model_name
    timeout = config.llm_timeout or 30

    if not base_url or not api_key:
        logger.warning("Chưa cấu hình LLM_BASE_URL hoặc LLM_API_KEY. Chuyển sang fallback.")
        return None

    # Kiểm tra trạng thái Circuit Breaker để tránh nghẽn khi server offline
    try:
        _parser_breaker._check_state()
    except CircuitBreakerOpenError:
        return None

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Câu hỏi: {question}"},
        ],
        "temperature": config.temperature_parser,
        "max_tokens": config.max_tokens_parser,
        "stream": False,
        "response_format": {"type": "json_object"},
        "keep_alive": -1,
    }

    try:
        res = requests.post(endpoint, headers=headers, json=payload, timeout=min(timeout, 10))
        logger.info(f"LLM Status Code: {res.status_code}")

        if res.status_code != 200 or not res.text or not res.text.strip():
            logger.warning(f"LLM API trả về lỗi hoặc body rỗng (status {res.status_code}).")
            _parser_breaker._on_failure(Exception(f"HTTP {res.status_code}"))
            return None

        _parser_breaker._on_success()

        raw_text = res.text.strip()
        raw_content = ""

        # Trường hợp 1: Proxy trả về Server-Sent Events (SSE stream: data: {...})
        if "data:" in raw_text:
            for line in raw_text.splitlines():
                line = line.strip()
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data:"):
                    chunk_str = line[5:].strip()
                    try:
                        chunk = json.loads(chunk_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content_piece = delta.get("content") or ""
                        raw_content += content_piece
                    except Exception:
                        continue
        else:
            # Trường hợp 2: Proxy trả về đối tượng JSON hoàn chỉnh
            data = res.json()
            message = data["choices"][0]["message"]
            raw_content = message.get("content") or ""
            if not raw_content and "reasoning_content" in message:
                raw_content = message["reasoning_content"]

        raw_content = raw_content.strip()
        # Làm sạch nếu LLM lỡ bọc trong markdown code block
        raw_content = re.sub(r"^```json\s*", "", raw_content)
        raw_content = re.sub(r"\s*```$", "", raw_content).strip()

        if not raw_content:
            logger.warning("Không thể trích xuất nội dung văn bản từ phản hồi LLM.")
            return None

        parsed_json = json.loads(raw_content)

        # Kiểm tra tính hợp lệ của JSON
        if "intent" in parsed_json and parsed_json["intent"] in SUPPORTED_INTENTS:
            intent = parsed_json["intent"]
            slots = parsed_json.get("slots", {}) or {}
            # Sửa bug OOD slot-leak: nếu intent là OOD thì slots bắt buộc phải rỗng ({})
            if intent == QueryIntent.OOD.value:
                slots = {}
            else:
                # Chuẩn hóa & loại bỏ placeholder rò rỉ từ prompt (ví dụ: "ví dụ: CSD201", "string hoặc null")
                cleaned_slots = {}
                for sk, sv in slots.items():
                    if sv is None:
                        continue
                    sv_str = str(sv).strip()
                    if not sv_str or sv_str.lower() in ["none", "null", "string", "n/a", "string hoặc null"] or sv_str.startswith("ví dụ:"):
                        continue
                    if sk == "course_aspect" and sv_str.lower() in ["objective", "syllabus", "nội dung", "mục tiêu"]:
                        sv_str = "objective"
                    cleaned_slots[sk] = sv_str
                slots = cleaned_slots
                # Bổ sung trích xuất phân hiệu (campus) nếu LLM bỏ sót
                if not slots.get("campus"):
                    matched_c = match_campus(question)
                    if matched_c:
                        slots["campus"] = matched_c
                # Bổ sung trích xuất mã môn (course_code) nếu LLM bỏ sót và mã môn hợp lệ
                if not slots.get("course_code"):
                    c_match = re.search(r"\b([A-Z]{3}\d{3}[a-z]?)\b", question)
                    if c_match:
                        cand = c_match.group(1).upper()
                        if cand in _get_known_course_codes():
                            slots["course_code"] = cand

                # Điều chỉnh câu hỏi về học bổng luôn là policy_lookup
                if "học bổng" in question.lower():
                    intent = QueryIntent.POLICY_LOOKUP.value
                    slots["topic"] = "hoc_bong"

                # Điều chỉnh quy chế đăng ký tín chỉ tối đa -> policy_lookup
                if any(w in question.lower() for w in ["đăng ký tối đa", "tối đa bao nhiêu tín chỉ"]):
                    intent = QueryIntent.POLICY_LOOKUP.value
                    slots["topic"] = "tin_chi"
                    slots["target"] = "gioi_han"

            return {
                "intent": intent,
                "slots": slots,
                "confidence": float(parsed_json.get("confidence", 0.95)),
                "model_used": model_name,
                "raw_content": raw_content,
            }
        else:
            logger.warning(f"LLM trả về intent không hợp lệ: {parsed_json.get('intent')}")
            return None
    except Exception as exc:
        _parser_breaker._on_failure(exc)
        logger.warning(f"Lỗi khi gọi LLM cho Semantic Parsing: {exc}. Kích hoạt fallback.")
        return None


def _parse_with_regex(question: str, norm_res: Optional[Any] = None) -> Dict[str, Any]:
    """Phân tích dự phòng bằng Regex / Rule-based khi LLM gặp sự cố."""
    q_lower = question.lower()
    slots: Dict[str, Any] = {}

    # 1. Kiểm tra course_lookup trước (Nếu câu hỏi chứa mã môn học thuộc CKB hoặc nhận diện từ EntityNormalizer)
    course_match = COURSE_CODE_REGEX.search(question)
    c_code = None
    known_codes = _get_known_course_codes()
    if course_match and course_match.group(1).upper() in known_codes:
        c_code = course_match.group(1).upper()
    elif norm_res and norm_res.slots_hint.get('course_code') in known_codes:
        c_code = norm_res.slots_hint['course_code']

    if c_code:
        if any(w in q_lower for w in ["học những gì", "học gì", "nội dung", "kiến thức", "chủ đề", "kỹ năng", "dạy những gì", "học cái gì", "học môn này được gì"]):
            aspect = "objective"
        elif any(w in q_lower for w in ["giáo trình", "sách", "tài liệu", "sách giáo trình", "tác giả", "ai viết", "nhà xuất bản"]):
            aspect = "textbook"
        elif any(w in q_lower for w in ["tiên quyết", "trước", "cần qua môn", "yêu cầu"]):
            aspect = "prerequisite"
        elif any(w in q_lower for w in ["tín chỉ", "bao nhiêu tín", "số tín"]):
            aspect = "credits"
        elif any(w in q_lower for w in ["thi", "kiểm tra", "pe", "eos", "đánh giá", "thực hành", "hình thức", "bảo vệ"]):
            aspect = "assessment"
        elif any(w in q_lower for w in ["kỳ", "học kỳ", "kỳ mấy", "kỳ thứ"]):
            aspect = "semester"
        elif any(w in q_lower for w in ["ngành", "chuyên ngành"]):
            aspect = "programs"
        else:
            aspect = "general"

        slots["course_code"] = c_code
        slots["course_aspect"] = aspect
        return {
            "intent": QueryIntent.COURSE_LOOKUP.value,
            "slots": slots,
            "confidence": 0.95,
        }

    # 2. Kiểm tra OOD (các chủ đề ngoài miền học vụ FPT từ SSOT constants)
    if any(kw in q_lower for kw in OOD_KEYWORDS):
        return {
            "intent": QueryIntent.OOD.value,
            "slots": {},
            "confidence": 0.95,
        }

    # 3. Kiểm tra graduation_lookup (ngoại trừ khi hỏi cụ thể về lệ phí tốt nghiệp/cấp bằng)
    is_fee_query = any(kw in q_lower for kw in ["lệ phí", "bao nhiêu tiền", "hết bao nhiêu", "chi phí", "mức thu", "đóng bao nhiêu"])
    is_graduation = any(kw in q_lower for kw in ["tốt nghiệp", "ra trường", "chuẩn đầu ra", "đồ án", "khóa luận", "capstone", "sep490"])
    if is_graduation and not is_fee_query:
        if any(kw in q_lower for kw in ["đồ án", "capstone", "khóa luận"]):
            slots["topic"] = "do_an_capstone"
        else:
            slots["topic"] = "tot_nghiep"
        slots["target"] = "dieu_kien"
        return {
            "intent": QueryIntent.GRADUATION_LOOKUP.value,
            "slots": slots,
            "confidence": 0.88,
        }

    # 3. Kiểm tra kỷ luật / khiếu nại / đình chỉ (kể cả đình chỉ học tập có hoàn học phí không)
    is_ky_luat = any(kw in q_lower for kw in ["kỷ luật", "đình chỉ", "buộc thôi học", "thôi học", "khiếu nại", "vi phạm", "xử lý kỷ luật", "hình thức kỷ luật"])
    if is_ky_luat:
        slots["topic"] = "ky_luat"
        return {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "slots": slots,
            "confidence": 0.88,
        }

    # 3.5. Kiểm tra quy định điểm F hoặc quyền hạn học vụ khi nợ học phí -> policy_lookup
    if any(kw in q_lower for kw in ["điểm f", "diem f", "nợ học phí thì có", "nợ học phí có", "được đkm"]):
        slots["topic"] = "quy_che_chung"
        return {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "slots": slots,
            "confidence": 0.88,
        }

    # 4. Kiểm tra tuition_lookup (Học phí và Lệ phí có cấu trúc)
    is_common_fee = any(kw in q_lower for kw in [
        "lệ phí thi lại", "phí thi lại", "thi lại bao nhiêu", "lệ phí thi",
        "lệ phí học lại", "phí học lại", "học lại mỗi tín chỉ", "học lại bao nhiêu",
        "phí ký túc", "ký túc xá", "phí ktx", "ký túc xá một kỳ",
        "lệ phí tốt nghiệp", "phí tốt nghiệp", "cấp bằng là bao nhiêu"
    ])
    has_tuition_entity = False
    if norm_res and getattr(norm_res, "entities", None):
        has_tuition_entity = any(
            e.entity_id == "TERM_HOC_PHI" or getattr(e, "code", "") == "TUITION"
            for e in norm_res.entities
        )
    has_money_word = bool(re.search(r"\b(tiền|tien|phí|phi|mức phí|muc phi)\b", q_lower))
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
    )
    if is_tuition:
        if is_common_fee:
            slots["topic"] = "common_fee"
            slots["program"] = "chung"
        elif norm_res and norm_res.slots_hint.get("program"):
            slots["program"] = norm_res.slots_hint["program"]
        if norm_res and norm_res.slots_hint.get("cohort"):
            slots["cohort"] = norm_res.slots_hint["cohort"]
        if norm_res and norm_res.slots_hint.get("campus"):
            slots["campus"] = norm_res.slots_hint["campus"]

        # Trích xuất ngành học qua SSOT PROGRAM_ALIAS_MAP và MAJOR_TO_SHORT_CODE
        matched_prog = None
        sorted_aliases = sorted(PROGRAM_ALIAS_MAP.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
            if alias in ["luật", "luật kinh tế"]:
                continue
            full_major = PROGRAM_ALIAS_MAP[alias]
            if len(alias) <= 4:
                if re.search(rf"\b{re.escape(alias)}\b", q_lower):
                    matched_prog = MAJOR_TO_SHORT_CODE.get(full_major, full_major)
                    break
            else:
                if alias in q_lower:
                    matched_prog = MAJOR_TO_SHORT_CODE.get(full_major, full_major)
                    break
        if matched_prog:
            slots["program"] = matched_prog
        elif "chuyên ngành" in q_lower and not slots.get("program"):
            slots["program"] = "chuyên ngành"
        # Ngành Luật không gán mặc định để kích hoạt làm rõ (clarification giữa Luật vs Luật kinh tế hoặc khu vực)

        # Trích xuất phân hiệu (campus)
        matched_c = match_campus(q_lower)
        if matched_c:
            slots["campus"] = matched_c

        # Trích xuất khóa tuyển sinh
        cohort_match = re.search(r"\b(202[0-9]|203[0-9]|k1[0-9]|k2[0-9])\b", q_lower)
        if cohort_match:
            slots["cohort"] = cohort_match.group(1).upper()

        if "tín chỉ" in q_lower:
            slots["topic"] = "tin_chi"

        return {
            "intent": QueryIntent.TUITION_LOOKUP.value,
            "slots": slots,
            "confidence": 0.88,
        }

    # 5. Kiểm tra policy_lookup (Quy chế học vụ / đào tạo / học bổng)
    policy_keywords = [
        "cảnh cáo", "cảnh báo", "học vụ", "tiên quyết", "thi lại", "học lại", "chuyên cần",
        "vắng", "điểm liệt", "học bổng", "tín chỉ", "đăng ký", "học phần", "quy chế",
        "thang điểm", "điểm f", "điểm a", "điểm b", "điểm c", "điểm d", "điểm số", "xếp loại",
        "gpa", "cgpa", "học lực", "tích lũy", "bảo lưu", "chuyển ngành", "chuyển cơ sở",
        "chuyển campus", "nghỉ học", "học vượt", "miễn học", "công nhận", "2 ngành", "song bằng",
        "thời hạn", "hoàn thành", "rèn luyện", "điểm rèn luyện", "sinh viên", "học kỳ", "môn học",
        "đào tạo", "khảo thí", "phúc khảo", "kiểm tra", "giữa kỳ", "cuối kỳ", "nghiên cứu khoa học",
        "học cải thiện", "điểm"
    ]
    if any(kw in q_lower for kw in policy_keywords):
        if "cảnh cáo" in q_lower or "cảnh báo" in q_lower:
            slots["topic"] = "canh_bao_hoc_vu"
            slots["target"] = "dieu_kien"
        elif "chuyên cần" in q_lower or "vắng" in q_lower:
            slots["topic"] = "chuyen_can"
            slots["target"] = "ty_le_vang"
        elif "học bổng" in q_lower:
            slots["topic"] = "hoc_bong"
            slots["target"] = "dieu_kien"
        elif "tín chỉ" in q_lower or "học phần" in q_lower or "đăng ký" in q_lower:
            slots["topic"] = "tin_chi"
            slots["target"] = "dieu_kien"
        else:
            slots["topic"] = "quy_che_chung"

        return {
            "intent": QueryIntent.POLICY_LOOKUP.value,
            "slots": slots,
            "confidence": 0.88,
        }

    # 6. Fallback thông minh: nếu chứa từ khóa học đường FPT -> policy_lookup, ngược lại -> OOD
    has_academic_entities = False
    if norm_res and getattr(norm_res, "entities", None):
        has_academic_entities = any(
            e.entity_type in ["major", "course", "cohort", "campus", "academic_term"]
            for e in norm_res.entities
        )
    academic_keywords = [
        "học", "hoc", "sinh viên", "sinh vien", "trường", "truong", "thi", "điểm", "diem",
        "học kỳ", "hoc ky", "tiếng anh", "tieng anh", "ngoại ngữ", "ngoai ngu",
        "chương trình", "chuong trinh", "đào tạo", "dao tao", "chứng chỉ", "chung chi",
        "môn", "mon", "ngành", "nganh", "khóa", "khoa", "tín chỉ", "tin chi",
        "cntt", "ktpm", "attt", "qtkd", "mkt", "ib", "ds"
    ]
    if has_academic_entities or any(kw in q_lower for kw in academic_keywords) or re.search(r"\b(kỳ|ky|kỳ học|ky hoc|mức độ|muc do|k\d{2})\b", q_lower):
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
    }


def parse_query(question: str, force_regex: bool = False) -> ParsedQuery:
    """Chuyển đổi câu hỏi của sinh viên thành đối tượng ParsedQuery (Contract 3) và ghi log parsing_events.jsonl.

    Ưu tiên 1: LLM Structured Output.
    Ưu tiên 2: Regex Fallback nếu LLM thất bại.
    """
    import time
    from FPTUniQA.query.router import route_query
    from FPTUniQA.utils.logger import log_parsing_event

    start_time = time.time()
    clean_query = normalize_query(question)

    # Chuẩn hóa thực thể học vụ qua Domain Dictionary (EntityNormalizer)
    norm_res = None
    try:
        from FPTUniQA.normalization.engine import get_entity_normalizer
        norm_res = get_entity_normalizer().normalize(question)
    except Exception as e:
        logger.warning(f"Không thể khởi chạy EntityNormalizer: {e}")

    # 1. Thử phân tích bằng LLM Structured Output
    llm_result = None if force_regex else _parse_with_llm(question)

    if llm_result:
        parsed = ParsedQuery(
            intent=llm_result["intent"],
            slots=llm_result.get("slots", {}),
            confidence=llm_result["confidence"],
            parser_method="llm_structured_output",
            fallback_used=False,
            original_query=question,
            normalized_query=clean_query,
        )
    else:
        # 2. Tự động rơi về Regex Fallback khi LLM thất bại
        logger.info(f"Kích hoạt Regex Fallback cho câu hỏi: '{question}'")
        regex_result = _parse_with_regex(clean_query, norm_res=norm_res)

        parsed = ParsedQuery(
            intent=regex_result["intent"],
            slots=regex_result.get("slots", {}),
            confidence=regex_result["confidence"],
            parser_method="regex_fallback",
            fallback_used=True,
            original_query=question,
            normalized_query=clean_query,
        )

    # Bổ sung thực thể đã chuẩn hóa từ Domain Dictionary vào Contract 3
    if norm_res and norm_res.entities:
        parsed.entities = {e.entity_id: e.to_dict() for e in norm_res.entities}
        # Nếu đã tìm thấy thực thể học vụ trong từ điển và không chứa OOD_KEYWORDS, ngăn chặn OOD giả
        if parsed.intent == QueryIntent.OOD.value and not any(kw in clean_query.lower() for kw in OOD_KEYWORDS):
            if any(e.entity_id == "TERM_HOC_PHI" or getattr(e, "code", "") == "TUITION" for e in norm_res.entities):
                parsed.intent = QueryIntent.TUITION_LOOKUP.value
            else:
                parsed.intent = QueryIntent.POLICY_LOOKUP.value

        if parsed.intent != QueryIntent.OOD.value:
            dict_course = norm_res.slots_hint.get("course_code")
            if dict_course:
                parsed.slots["course_code"] = dict_course
                parsed.intent = QueryIntent.COURSE_LOOKUP.value
                if norm_res.slots_hint.get("course_aspect"):
                    parsed.slots["course_aspect"] = norm_res.slots_hint["course_aspect"]

            for k, v in norm_res.slots_hint.items():
                if k not in parsed.slots or not parsed.slots[k]:
                    parsed.slots[k] = v

    # Kiểm tra tính hợp lệ của course_lookup
    if parsed.intent == "course_lookup":
        known_codes = _get_known_course_codes()
        c_code = (parsed.slots.get("course_code") or "").upper() if parsed.slots else ""
        if c_code not in known_codes:
            # Nếu không có mã môn học hợp lệ mà bị LLM gán nhầm
            q_norm = clean_query.lower()
            if any(kw in q_norm for kw in OOD_KEYWORDS):
                parsed.intent = QueryIntent.OOD.value
            else:
                parsed.intent = QueryIntent.POLICY_LOOKUP.value
        elif parsed.slots:
            aspect = parsed.slots.get("course_aspect")
            q_norm = clean_query.lower()
            if any(w in q_norm for w in ["giáo trình", "sách", "tài liệu", "tác giả", "ai viết", "nhà xuất bản"]):
                parsed.slots["course_aspect"] = "textbook"
            elif any(w in q_norm for w in ["học những gì", "học gì", "nội dung", "kiến thức", "chủ đề", "kỹ năng", "dạy những gì"]):
                parsed.slots["course_aspect"] = "objective"
            elif aspect in ["topics", "content", "curriculum"]:
                parsed.slots["course_aspect"] = "objective"
            elif aspect in ["materials", "book", "books"]:
                parsed.slots["course_aspect"] = "textbook"
            elif aspect not in ["objective", "syllabus", "textbook", "prerequisite", "credits", "assessment", "semester", "programs", "general"]:
                parsed.slots["course_aspect"] = "general"

    # Đo latency và điều phối router
    latency_ms = (time.time() - start_time) * 1000.0
    route_chosen, _ = route_query(parsed)

    # Ghi log sự kiện phân tích cú pháp vào logs/parsing_events.jsonl (phục vụ Tuần 7)
    log_parsing_event(
        original_query=question,
        parsed_result=parsed.model_dump(),
        route_chosen=route_chosen,
        latency_ms=latency_ms,
    )

    return parsed


def try_rule_fast_parse(question: str) -> Optional[ParsedQuery]:
    """Bỏ qua LLM Parser đối với các câu hỏi rule-based có độ tin cậy cao để giảm p95 latency."""
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

    return None

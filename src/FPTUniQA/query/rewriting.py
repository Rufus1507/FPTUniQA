"""Module viết lại câu hỏi theo ngữ cảnh hội thoại đa lượt (Query Rewriting). Phụ trách: TV3.

Nhiệm vụ cốt lõi:
- Đứng trước Semantic Parser trong dòng chảy Pipeline.
- Tiếp nhận câu hỏi hiện tại và lịch sử hội thoại (session context).
- Sử dụng LLM để giải quyết hiện tượng đồng tham chiếu (coreference) và tỉnh lược (ellipsis),
  viết lại câu hỏi thành dạng đầy đủ, độc lập ngữ cảnh trước khi phân tích cú pháp.
"""

import json
import re
from typing import Any, Dict, List, Optional
import requests

from FPTUniQA.query.constants import (
    CAMPUS_CODES_REGEX,
    CAMPUS_NAMES_REGEX,
    COMMON_FEE_KEYWORDS,
    COURSE_CODE_REGEX,
    MAJOR_NAMES,
    OOD_KEYWORDS,
)
from FPTUniQA.utils.config import config
from FPTUniQA.utils.exceptions import CircuitBreaker, CircuitBreakerOpenError
from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.query.rewriting")
_rewriter_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0, name="rewriter_llm")

REWRITER_SYSTEM_PROMPT = """Bạn là trợ lý chuyên viết lại câu hỏi (Query Rewriter) trong hệ thống hỏi đáp học vụ Đại học FPT.
Nhiệm vụ của bạn: Dựa vào lịch sử hội thoại, viết lại câu hỏi hiện tại của sinh viên thành một câu hỏi duy nhất, độc lập, rõ ràng và đầy đủ ngữ cảnh (tự chứa đầy đủ thông tin: ngành học, khóa tuyển sinh, chủ đề học vụ).

Quy tắc bắt buộc:
1. Kế thừa ĐÚNG ngành học (ví dụ: Marketing, Quản trị kinh doanh, An toàn thông tin, Thiết kế đồ họa...), cơ sở đào tạo (ví dụ: Quy Nhơn, Cần Thơ, Đà Nẵng, TP.HCM, Hòa Lạc) và khóa học từ lịch sử hội thoại. TUYỆT ĐỐI KHÔNG tự động đổi ngành sang Công nghệ thông tin nếu sinh viên đang hỏi ngành khác.
2. Nếu câu hỏi hiện tại đã đầy đủ thông tin độc lập, hãy giữ nguyên nội dung.
3. Khi sinh viên đính chính hoặc phủ định (ví dụ: "không, mình hỏi khóa K21 cơ", "mình nhầm, mình hỏi ngành ATTT", "không phải Hà Nội đâu, mình đang hỏi ở Cần Thơ"), hãy thay thế thông tin cũ bằng thông tin mới tương ứng trong ngữ cảnh câu hỏi trước đó.
4. Khi câu hỏi trước hỏi về chuẩn đầu ra (như chuẩn đầu ra tiếng Anh, chuẩn đầu ra tin học), hãy bảo toàn cụ thể loại chuẩn đầu ra đó (ví dụ: "chuẩn đầu ra tiếng Anh").
5. Tuyệt đối KHÔNG tự ý bịa thêm thông tin, số tín chỉ, học kỳ, học phí nếu sinh viên không hỏi.
6. Khi sinh viên đổi khóa hoặc đổi cơ sở ở lượt gần nhất, phải giữ thông tin mới nhất của lượt gần nhất, không lấy lại thông tin cũ của các lượt trước.
7. Khi câu hỏi là câu hỏi chung (như ký túc xá, quy chế thi, nội quy phòng thi), tuyệt đối KHÔNG ghép ngành học hay mã môn vào.
8. KHÔNG trả lời câu hỏi.
9. KHÔNG thêm lời giải thích, lời chào hoặc bất kỳ văn bản phụ trợ nào.
10. Chỉ trả về DUY NHẤT một câu hỏi đã viết lại trên một dòng.
11. Khi câu hỏi hiện tại là câu chào hỏi, hỏi danh tính bot, cảm thán (ví dụ: "bạn là ai", "sao nhanh vậy", "xin chào"), TUYỆT ĐỐI KHÔNG ghép ngành, khóa hay mã môn từ lịch sử vào. Hãy giữ nguyên câu hỏi.
12. Khi sinh viên hỏi về một ngành học mới (ví dụ: "ngành AI học gì"), TUYỆT ĐỐI KHÔNG ghép cơ sở (Quy Nhơn, Cần Thơ...) hay ngành cũ từ lịch sử vào."""


def _call_llm_rewriter(prompt: str) -> Optional[str]:
    """Gọi LLM qua endpoint cục bộ để viết lại câu hỏi."""
    base_url = config.llm_base_url
    api_key = config.llm_api_key
    model_name = config.model_name
    timeout = config.llm_timeout or 30

    if not base_url or not api_key:
        logger.warning("Chưa cấu hình LLM_BASE_URL hoặc LLM_API_KEY. Bỏ qua rewriting.")
        return None

    # Kiểm tra trạng thái Circuit Breaker
    try:
        _rewriter_breaker._check_state()
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
            {"role": "system", "content": REWRITER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature_rewriter,
        "max_tokens": config.max_tokens_rewriter,
        "stream": False,
        "keep_alive": -1,
    }

    try:
        res = requests.post(endpoint, headers=headers, json=payload, timeout=min(timeout, 10))
        if res.status_code != 200 or not res.text or not res.text.strip():
            logger.warning(f"LLM Rewriter trả về lỗi hoặc rỗng (status {res.status_code}).")
            _rewriter_breaker._on_failure(Exception(f"HTTP {res.status_code}"))
            return None

        _rewriter_breaker._on_success()

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
        # Loại bỏ các đoạn prompt lặp lại nếu LLM echo lại prompt
        if "Câu hỏi viết lại đầy đủ ngữ cảnh:" in raw_content:
            raw_content = raw_content.split("Câu hỏi viết lại đầy đủ ngữ cảnh:")[-1].strip()
        if "Lịch sử hội thoại trước đó:" in raw_content:
            raw_content = raw_content.split("Lịch sử hội thoại trước đó:")[0].strip()
        if "Câu hỏi hiện tại của sinh viên:" in raw_content:
            raw_content = raw_content.split("Câu hỏi hiện tại của sinh viên:")[0].strip()

        # Loại bỏ các tiền tố thường gặp nếu LLM lỡ sinh ra
        raw_content = re.sub(r"^(Câu hỏi viết lại|Câu hỏi sau khi viết lại|Rewritten Query):\s*", "", raw_content, flags=re.IGNORECASE)
        # Lấy dòng đầu tiên có nội dung nếu trả về nhiều dòng
        lines = [line.strip() for line in raw_content.splitlines() if line.strip()]
        if lines:
            raw_content = lines[0]

        # Loại bỏ dấu ngoặc kép bọc ngoài nếu có
        if raw_content.startswith('"') and raw_content.endswith('"') and len(raw_content) > 1:
            raw_content = raw_content[1:-1].strip()

        return raw_content if raw_content else None
    except Exception as exc:
        _rewriter_breaker._on_failure(exc)
        logger.warning(f"Lỗi khi gọi LLM Rewriter: {exc}. Chuyển sang fallback theo luật.")
        return None


TOPIC_PATTERNS = {
    "discipline_warning": [
        "cảnh báo", "kỷ luật", "đình chỉ", "buộc thôi học", "học vụ",
        "điểm f", "nợ môn", "quá hạn", "vi phạm quy chế", "thi lại hay học lại"
    ],
    "tuition": [
        "học phí", "chi phí", "tiền học", "mức thu", "lệ phí", "nộp tiền",
        "kỳ định hướng", "học lại", "thi lại", "phí ký túc", "giá tín chỉ"
    ],
    "graduation": [
        "tốt nghiệp", "chuẩn đầu ra", "xét tốt nghiệp", "bằng tốt nghiệp",
        "tín chỉ tích lũy", "đồ án tốt nghiệp", "khóa luận", "chứng chỉ tiếng anh", "toeic", "ielts"
    ],
    "ojt_internship": [
        "ojt", "thực tập", "doanh nghiệp", "kỳ thực tập", "đi ojt", "để được đi", "môn dự án nào"
    ],
    "exam_appeal": [
        "phúc khảo", "khiếu nại", "chấm lại", "bài thi", "thời hạn phúc khảo", "lệ phí phúc khảo"
    ],
    "admin_services": [
        "bảng điểm", "bản sao", "giấy xác nhận", "thẻ sinh viên", "dịch vụ sinh viên"
    ],
    "exam_regulations": [
        "thi eos", "phòng thi", "quy chế thi", "mang tài liệu", "coi thi", "đình chỉ thi"
    ],
    "scholarship": [
        "học bổng", "tài trợ", "nguyễn văn đạo", "duy trì học bổng"
    ],
    "curriculum_credits": [
        "khung chương trình", "số tín chỉ", "tiến độ", "rút môn", "đăng ký môn", "chuyển ngành", "bảo lưu"
    ],
    "ood": OOD_KEYWORDS,
}

CONTINUATION_PATTERNS = [
    r"\b(để được đi|được đi|để đi|trong kỳ này|kỳ này|giai đoạn này)\b",
    r"^(thế\s+|the\s+)?(còn|con)\b",
    r"^(vậy|vay)\s+(nếu|neu|thì|thi|còn|con)\b",
    r"^(nếu|neu)\s+(vậy|vay|thế|the|bị|bi|học|hoc)\b",
    r"^(ở|tại|o|tai)\s+(đó|đấy|cơ sở|co so|phân hiệu|phan hieu|campus|do|day)\b",
    r"^(ở|tại|o|tai)\s+([A-Za-z0-9_\s]+)\b",
    r"^(ngành|khóa|năm|môn|học phần|nganh|khoa|nam|mon)\s+(đó|đấy|này|do|day|nay)\b",
    r"\b(môn|học phần|ngành|khóa|năm|phân hiệu|cơ sở|mon|nganh|khoa|nam)\s+(này|đó|đấy|kia|nay|do|day)\b",
    r"\b(môn|mon)\s+(này|đó|nay|do)\b",
    r"\b(thì\s+sao|thi\s+sao|thế\s+nào|the\s+nao|bao\s+nhiêu|bao\s+nhieu)\??$",
    r"^(bao\s+nhiêu|bao\s+nhieu|khi\s+nào|khi\s+nao|ở\s+đâu|o\s+dau)\??$",
    rf"\b(ở|o)\s+({CAMPUS_NAMES_REGEX}|{CAMPUS_CODES_REGEX}|quy nhon|can tho|da nang|ha noi|hcm)\s+(thì|thi)\s+sao\b",
    rf"\b(còn|con)\s+({CAMPUS_NAMES_REGEX}|{CAMPUS_CODES_REGEX}|quy nhon|can tho|da nang|ha noi|hcm)\b",
    r"\b(còn|con)\s+(k\d{2}|khóa\s+\d{2}|khoa\s+\d{2})\b",
    r"\b(còn|con)\s+[A-Za-z0-9_]+\s+(thì|thi)\s+sao\b",
]


def detect_topic_from_text(text: str) -> str:
    """Xác định chủ đề chính của câu dựa trên từ khóa (hỗ trợ cả có dấu và không dấu)."""
    t_lower = text.lower()
    t_unaccent = ""
    try:
        from FPTUniQA.normalization.engine import remove_accents
        t_unaccent = remove_accents(t_lower)
    except Exception:
        pass

    for topic, keywords in TOPIC_PATTERNS.items():
        if any(kw in t_lower for kw in keywords):
            return topic
        if t_unaccent:
            try:
                from FPTUniQA.normalization.engine import remove_accents
                if any(remove_accents(kw) in t_unaccent for kw in keywords):
                    return topic
            except Exception:
                pass
    return "general_policy"


def is_self_contained_query(query: str) -> bool:
    """Self-Containedness Gate: Kiểm tra xem câu hỏi có tự chứa đầy đủ ngữ cảnh độc lập hay không.
    Nếu câu hỏi tự chứa đầy đủ thông tin hoặc nêu chủ thể/thực thể mới rõ ràng,
    hệ thống TUYỆT ĐỐI KHÔNG ghép ngữ cảnh cũ từ các lượt trước (Context Decontamination).
    """
    q_clean = query.strip().lower()

    # 0. Nếu câu hỏi có chứa đại từ chỉ định môn học hoặc ngành học ("môn này", "môn đó", "học phần này", "ngành này"...),
    # thì câu hỏi KHÔNG THỂ là self-contained độc lập!
    if re.search(r"\b(môn này|môn đó|môn ấy|học phần này|học phần đó|ngành này|ngành đó|khóa này|khóa đó|ở đó|tại đó|cơ sở đó|phân hiệu đó)\b", q_clean):
        return False

    # 1. Câu hỏi chứa mã môn học rõ ràng (ví dụ: CSD201, PRF192, PRO192, MAS291...)
    if re.search(COURSE_CODE_REGEX, query, re.IGNORECASE):
        if not re.search(r"\b(môn này|môn đó|môn ấy|học phần này|học phần đó|mon nay|mon do)\b", q_clean):
            return True

    # 1b. Câu hỏi chứa tên môn học cụ thể được từ điển nhận diện
    try:
        from FPTUniQA.normalization.engine import get_entity_normalizer
        norm_c = get_entity_normalizer().normalize(query)
        if any(e.entity_type == "course" for e in norm_c.entities):
            if not any(q_clean.startswith(p) for p in ["còn", "con", "thế còn", "the con", "vậy còn", "vay con", "thế thì", "the thi"]):
                if not re.search(r"\b(môn này|môn đó|học phần này|học phần đó|mon nay|mon do)\b", q_clean):
                    return True
    except Exception:
        pass

    # 2. Câu hỏi tra cứu lệ phí chung độc lập (lệ phí thi lại, học lại, ký túc xá, bảng điểm...)
    has_continuation_prefix = any(q_clean.startswith(p) for p in [
        "còn", "con", "thế còn", "the con", "vậy còn", "vay con", "thế thì", "the thi", "vậy nếu", "vay neu"
    ])
    if any(kw in q_clean for kw in COMMON_FEE_KEYWORDS) and not has_continuation_prefix:
        return True

    # 3. Câu hỏi quy chế học vụ độc lập (điểm danh, cấm thi, tốt nghiệp, bảo lưu, kỷ luật, nợ học phí...) - hỗ trợ cả không dấu
    policy_standalone_keywords = [
        "vắng bao nhiêu", "nghỉ học quá", "cấm thi", "toang môn", "tạch môn", "điểm danh",
        "xét tốt nghiệp", "chuẩn đầu ra", "đồ án tốt nghiệp", "capstone", "khóa luận",
        "bảo lưu", "tạm ngừng học", "nghỉ học tạm thời",
        "nợ học phí", "đăng ký môn học", "rút môn",
        "phúc khảo", "khiếu nại", "kỷ luật", "đình chỉ",
        "thẻ sinh viên", "cấp lại thẻ", "giấy xác nhận", "giấy chứng nhận", "xe buýt", "buýt",
        "tot nghiep", "xet tot nghiep", "chuan dau ra", "diem danh", "cam thi", "bao luu"
    ]
    q_unaccent = ""
    try:
        from FPTUniQA.normalization.engine import remove_accents
        q_unaccent = remove_accents(q_clean)
    except Exception:
        pass

    if (any(kw in q_clean for kw in policy_standalone_keywords) or (q_unaccent and any(kw in q_unaccent for kw in policy_standalone_keywords))) and not has_continuation_prefix:
        return True

    # 3b. Câu hỏi OJT / thực tập hoặc điều kiện tốt nghiệp đã có Khóa cụ thể rõ ràng
    has_cohort_in_q = bool(re.search(r"\b(K1[7-9]|K2[0-2]|202[0-6])\b", query, re.IGNORECASE))
    if has_cohort_in_q and any(kw in q_clean or (q_unaccent and kw in q_unaccent) for kw in ["ojt", "thực tập", "thuc tap", "tốt nghiệp", "tot nghiep"]):
        return True

    # 4. Câu hỏi ngoài miền (OOD) hoặc lời chào
    if any(kw in q_clean for kw in OOD_KEYWORDS):
        return True

    # 5. Câu hỏi học phí đã đủ cả khóa + ngành + cơ sở
    has_cohort = bool(re.search(r"\b(K1[7-9]|K2[0-2]|202[0-6])\b", query, re.IGNORECASE))
    has_campus = bool(re.search(CAMPUS_NAMES_REGEX, q_clean) or re.search(CAMPUS_CODES_REGEX, q_clean))
    has_major = any(m.lower() in q_clean for m in MAJOR_NAMES) or bool(re.search(r"\b(ai|cntt|ktpm|attt|qtkd|mkt|ib|ds)\b", q_clean))
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

    return False


def is_continuation_query(query: str) -> bool:
    """Kiểm tra xem câu hỏi có dấu hiệu tỉnh lược/hỏi tiếp lượt trước hay không."""
    q_clean = query.strip().lower()

    # Nếu câu hỏi đã tự chứa độc lập -> KHÔNG phải continuation
    if is_self_contained_query(query):
        return False

    if re.search(r"\b(môn này|môn đó|học phần này|học phần đó|khóa này|khóa đó|ngành này|ngành đó|phân hiệu này|cơ sở này|campus này|cơ sở đó|phân hiệu đó)\b", q_clean, flags=re.IGNORECASE):
        return True

    # Nhận diện câu đính chính / phủ định đổi thực thể (ví dụ: "Không, mình muốn hỏi khóa K21 cơ", "mình nhầm, mình hỏi ngành ATTT")
    is_correction = any(re.search(pat, q_clean, re.IGNORECASE) for pat in [
        r"^(không|khong|ko|k)\b",
        r"\b(không phải|khong phai|ko phai)\b",
        r"\b(nhầm|nham|nhầm xíu|nham xiu)\b",
        r"\b(ý mình là|y minh la|mình muốn hỏi|minh muon hoi|mình hỏi|minh hoi|ý là|y la)\b",
        r"\b(chứ không phải|chu khong phai)\b",
    ])
    has_new_entity = bool(
        re.search(r"\b(k1[7-9]|k2[0-6]|202[0-6])\b", q_clean, re.IGNORECASE) or
        any(m.lower() in q_clean for m in MAJOR_NAMES) or
        re.search(CAMPUS_NAMES_REGEX, q_clean, re.IGNORECASE) or
        re.search(CAMPUS_CODES_REGEX, q_clean, re.IGNORECASE) or
        re.search(r"\b(ai|cntt|ktpm|attt|qtkd|mkt|ib|ds)\b", q_clean, re.IGNORECASE)
    )
    if is_correction and has_new_entity:
        return True

    # Nếu câu dài (>= 6 từ) và chứa danh từ thủ tục xác định, không match mẫu đuôi câu 'thế nào?'
    is_procedural = any(kw in q_clean for kw in ["thủ tục", "quy định", "hướng dẫn", "cách thức", "làm thế nào", "điều kiện", "xin cấp"])
    if not is_procedural:
        for pattern in CONTINUATION_PATTERNS:
            if re.search(pattern, q_clean, flags=re.IGNORECASE):
                return True
    else:
        for pattern in CONTINUATION_PATTERNS:
            if pattern == r"\b(thì\s+sao|thi\s+sao|thế\s+nào|the\s+nao|bao\s+nhiêu|bao\s+nhieu)\??$":
                continue
            if re.search(pattern, q_clean, flags=re.IGNORECASE):
                return True

    continuation_start_words = [
        "còn", "con", "thế còn", "the con", "vậy còn", "vay con", "thế thì", "the thi", 
        "vậy nếu", "vay neu", "thế ở", "the o", "vậy ở", "vay o", "thế ngành", "the nganh",
        "còn ngành", "con nganh", "còn khóa", "con khoa", "thế khóa", "the khoa"
    ]
    if any(q_clean.startswith(sw) for sw in continuation_start_words):
        return True

    return False


def detect_topic_switch(
    current_question: str,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Phát hiện xem lượt hiện tại có chuyển sang chủ đề khác (Topic Switch) hay không.
    
    Trả về dict:
        - is_topic_switch: bool
        - current_topic: str
        - previous_topic: Optional[str]
        - confidence: float
    """
    if not history:
        return {
            "is_topic_switch": False,
            "current_topic": detect_topic_from_text(current_question),
            "previous_topic": None,
            "confidence": 1.0,
        }

    # Nếu là câu hỏi tự chứa đầy đủ độc lập -> Luôn coi là Topic Switch, không kế thừa context
    if is_self_contained_query(current_question):
        return {
            "is_topic_switch": True,
            "current_topic": detect_topic_from_text(current_question),
            "previous_topic": detect_topic_from_text(history[-1].get("query", "")),
            "confidence": 0.98,
        }

    # Nếu câu hỏi có dấu hiệu tỉnh lược/kế thừa rõ rệt -> KHÔNG phải topic switch
    if is_continuation_query(current_question):
        return {
            "is_topic_switch": False,
            "current_topic": detect_topic_from_text(current_question),
            "previous_topic": detect_topic_from_text(history[-1].get("query", "")),
            "confidence": 0.95,
        }

    # Nếu câu hỏi hiện tại là lời chào hoặc OOD rõ rệt thì luôn là Topic Switch
    if any(re.search(rf"\b{w}\b", current_question.lower()) for w in ["hello", "hi", "hey", "chao", "xin chao", "tạm biệt", "bye"]) or current_question.strip().lower() in ["hello]", "hello", "hi", "hi!"]:
        return {
            "is_topic_switch": True,
            "current_topic": "ood",
            "previous_topic": detect_topic_from_text(history[-1].get("query", "")) if history else None,
            "confidence": 0.99,
        }

    # Nếu lượt trước là yêu cầu làm rõ (clarification), lượt này người dùng cung cấp thông tin bổ sung -> KHÔNG PHẢI TOPIC SWITCH
    last_turn = history[-1] if history else {}
    prev_route = str(last_turn.get("route_chosen", "")).lower()
    prev_ans = str(last_turn.get("answer", ""))
    if "clarification" in prev_route or "vui lòng cung cấp thêm" in prev_ans.lower() or "bạn đang hỏi về" in prev_ans.lower():
        return {
            "is_topic_switch": False,
            "current_topic": detect_topic_from_text(current_question),
            "previous_topic": detect_topic_from_text(last_turn.get("query", "")),
            "confidence": 0.95,
        }

    curr_topic = detect_topic_from_text(current_question)

    # Lấy chủ đề các lượt trước
    prev_topics = []
    for turn in history:
        prev_q = turn.get("query") or turn.get("rewritten_query") or ""
        prev_topics.append(detect_topic_from_text(prev_q))

    last_topic = prev_topics[-1] if prev_topics else "general_policy"

    # Nếu câu hỏi hiện tại có chủ đề xác định và khác hoàn toàn chủ đề trước đó
    # Nếu câu hỏi hiện tại khác chủ đề với câu trước (kể cả khi một câu là general_policy)
    if curr_topic != last_topic and not is_continuation_query(current_question):
        return {
            "is_topic_switch": True,
            "current_topic": curr_topic,
            "previous_topic": last_topic,
            "confidence": 0.9,
        }
    if curr_topic != "general_policy" and last_topic != "general_policy" and curr_topic != last_topic:
        return {
            "is_topic_switch": True,
            "current_topic": curr_topic,
            "previous_topic": last_topic,
            "confidence": 0.9,
        }

    # Nếu câu hỏi hiện tại là OOD
    if curr_topic == "ood":
        return {
            "is_topic_switch": True,
            "current_topic": "ood",
            "previous_topic": last_topic,
            "confidence": 0.99,
        }

    # Nếu câu hỏi độc lập dài (trên 7 từ), có đầy đủ chủ ngữ vị ngữ và không tham chiếu
    q_words = current_question.strip().split()
    if len(q_words) >= 8 and not is_continuation_query(current_question) and curr_topic != last_topic:
        return {
            "is_topic_switch": True,
            "current_topic": curr_topic,
            "previous_topic": last_topic,
            "confidence": 0.85,
        }

    return {
        "is_topic_switch": False,
        "current_topic": curr_topic,
        "previous_topic": last_topic,
        "confidence": 0.7,
    }


_TEENCODE_MAP = [
    (re.compile(r"\bktx\b", re.IGNORECASE), "ký túc xá"),
    (re.compile(r"\bhl\b", re.IGNORECASE), "Hòa Lạc"),
    (re.compile(r"\bhcm\b", re.IGNORECASE), "Hồ Chí Minh"),
    (re.compile(r"\btphcm\b", re.IGNORECASE), "TP. Hồ Chí Minh"),
    (re.compile(r"\bđn\b|\bdn\b", re.IGNORECASE), "Đà Nẵng"),
    (re.compile(r"\bct\b", re.IGNORECASE), "Cần Thơ"),
    (re.compile(r"\bqn\b", re.IGNORECASE), "Quy Nhơn"),
    (re.compile(r"\bbn\b", re.IGNORECASE), "bao nhiêu"),
    (re.compile(r"\bz\b|\bv\b", re.IGNORECASE), "vậy"),
    (re.compile(r"\bad\b", re.IGNORECASE), "admin"),
    (re.compile(r"\be\b", re.IGNORECASE), "em"),
    (re.compile(r"\b(k|ko)\b", re.IGNORECASE), "không"),
    (re.compile(r"\b(đc|dc)\b", re.IGNORECASE), "được"),
    (re.compile(r"\bcủ\b", re.IGNORECASE), "triệu đồng"),
    (re.compile(r"\b(đatn|kltn)\b", re.IGNORECASE), "đồ án tốt nghiệp"),
]


def _normalize_teencode(text: str) -> str:
    """Chuẩn hóa nhanh các từ viết tắt / teencode thông dụng."""
    if not text:
        return text
    res = text
    for pat, rep in _TEENCODE_MAP:
        res = pat.sub(rep, res)
    return res


def _rule_based_rewrite(
    clean_q: str,
    history: List[Dict[str, Any]],
    is_fast_path: bool = False,
) -> Optional[str]:
    """Fallback viết lại câu hỏi theo luật kết hợp EntityNormalizer khi LLM không khả dụng."""
    if not history:
        return clean_q

    last_turn = history[-1]
    prev_q = last_turn.get("rewritten_query") or last_turn.get("query") or ""
    q_lower = clean_q.lower()

    # Sử dụng EntityNormalizer để nhận diện thực thể trong câu hỏi hiện tại
    norm_res = None
    try:
        from FPTUniQA.normalization.engine import get_entity_normalizer
        norm_res = get_entity_normalizer().normalize(clean_q)
    except Exception:
        pass

    curr_slots = norm_res.slots_hint if norm_res else {}
    curr_program = curr_slots.get("program")
    curr_cohort = curr_slots.get("cohort")
    curr_campus = curr_slots.get("campus")
    curr_course = curr_slots.get("course_code")

    # Bổ sung regex tìm khóa hoặc ngành nếu normalizer chưa bắt
    if not curr_cohort:
        cm = re.search(r"\b(K1[7-9]|K2[0-2]|202[0-6])\b", clean_q, re.IGNORECASE)
        if cm:
            curr_cohort = cm.group(1).upper()
    if not curr_program:
        for m in MAJOR_NAMES:
            if m.lower() in q_lower:
                curr_program = m
                break
        if not curr_program:
            alias_match = re.search(r"\b(ai|cntt|ktpm|attt|qtkd|mkt|ib|ds)\b", clean_q, re.IGNORECASE)
            if alias_match:
                curr_program = alias_match.group(0).upper()

    # Thu thập thực thể tích lũy từ toàn bộ lịch sử (ưu tiên từ lượt gần nhất)
    hist_program = ""
    hist_cohort = ""
    hist_campus = ""
    hist_course = ""
    hist_base_topic = ""

    for turn in reversed(history):
        p_query = turn.get("parsed_query", {})
        slots = p_query.get("slots", {}) if isinstance(p_query, dict) else getattr(p_query, "slots", {})
        if not hist_program and slots.get("program"):
            hist_program = slots["program"]
        if not hist_cohort and slots.get("cohort"):
            hist_cohort = slots["cohort"]
        if not hist_campus and slots.get("campus"):
            hist_campus = slots["campus"]
        if not hist_course and slots.get("course_code"):
            hist_course = slots["course_code"]

        turn_text = (turn.get("rewritten_query") or turn.get("query") or "").lower()
        if not hist_cohort:
            cm = re.search(r"\b(K1[7-9]|K2[0-2]|202[0-6])\b", turn_text, re.IGNORECASE)
            if cm:
                hist_cohort = cm.group(1).upper()
        if not hist_program:
            for m in MAJOR_NAMES:
                if m.lower() in turn_text:
                    hist_program = m
                    break
            if not hist_program:
                alias_match = re.search(r"\b(ai|cntt|ktpm|attt|qtkd|mkt|ib|ds)\b", turn_text, re.IGNORECASE)
                if alias_match:
                    hist_program = alias_match.group(0).upper()
        if not hist_campus:
            cm = re.search(CAMPUS_NAMES_REGEX, turn_text, re.IGNORECASE) or re.search(CAMPUS_CODES_REGEX, turn_text, re.IGNORECASE)
            if cm:
                hist_campus = cm.group(0).title()

    for turn in reversed(history):
        turn_text = (turn.get("rewritten_query") or turn.get("query") or "").lower()
        if any(w in turn_text for w in ["học phí", "hoc phi", "tiền học", "chi phí", "mức thu", "lệ phí"]):
            hist_base_topic = "Học phí"
            break
        elif any(w in turn_text for w in [
            "điểm danh", "cấm thi", "tốt nghiệp", "cảnh cáo", "kỷ luật", "bảo lưu",
            "tín chỉ", "chuẩn đầu ra", "tiếng anh", "ielts", "toefl", "đồ án",
            "thực tập", "ojt", "học bổng", "giáo trình", "môn học", "tiên quyết"
        ]):
            hist_base_topic = "Quy chế"
            break

    last_turn = history[-1]
    prev_route = str(last_turn.get("route_chosen", "")).lower()
    prev_ans = str(last_turn.get("answer", ""))
    is_prev_clarification = "clarification" in prev_route or "vui lòng cung cấp thêm" in prev_ans.lower() or "bạn đang hỏi về" in prev_ans.lower()

    # ƯU TIÊN 0.1: Xử lý ngữ cảnh tiếp nối OJT (ví dụ: 'Trong kỳ này sinh viên có phải đóng học phí chuyên ngành không?' hoặc 'Cần tích lũy bao nhiêu tín chỉ... để được đi?')
    if any(w in q_lower for w in ["để được đi", "được đi", "để đi"]):
        if any(w in prev_q.lower() for w in ["ojt", "thực tập"]):
            eff_p = curr_program or hist_program or "Kỹ thuật phần mềm"
            res_q = re.sub(r"\b(để được đi|được đi|để đi)\b", f"để được đi thực tập OJT ngành {eff_p}", clean_q, flags=re.IGNORECASE)
            return res_q

    if any(w in q_lower for w in ["trong kỳ này", "kỳ này", "trong đợt này", "trong giai đoạn này"]):
        if any(w in prev_q.lower() for w in ["ojt", "thực tập"]):
            res_q = re.sub(r"\btrong kỳ này\b", "Trong kỳ thực tập OJT", clean_q, flags=re.IGNORECASE)
            res_q = re.sub(r"\bkỳ này\b", "kỳ thực tập OJT", res_q, flags=re.IGNORECASE)
            return res_q

    # ƯU TIÊN 0.2: Xử lý ký túc xá tiếp nối (ví dụ: 'Ở đó ký túc xá một kỳ bao nhiêu tiền?')
    if ("ký túc xá" in q_lower or "ktx" in q_lower) and any(w in q_lower for w in ["ở đó", "tại đó", "o do", "tai do"]):
        if hist_campus:
            res_q = re.sub(r"\b(ở đó|tại đó|o do|tai do)\b", f"tại phân hiệu {hist_campus}", clean_q, flags=re.IGNORECASE)
            return res_q

    # ƯU TIÊN 1: Tham chiếu đại từ môn học ("môn này", "môn đó", "học phần này", "học phần đó", "môn ấy")
    if hist_course and not curr_course:
        is_f_grade = any(w in q_lower for w in ["điểm f", "diem f", "trượt môn", "rớt môn", "thi lại hay học lại", "học tiếp", "kỳ sau", "tiếp theo"])
        is_fee_only = any(kw in q_lower for kw in ["học phí", "lệ phí", "ký túc", "bảng điểm"]) and not is_f_grade
        if not is_fee_only:
            for p_term in ["môn này", "môn đó", "học phần này", "học phần đó", "môn ấy", "mon nay", "mon do", "hoc phan nay", "hoc phan do"]:
                if p_term in q_lower:
                    return clean_q.replace(p_term, f"Môn {hist_course}")
            prev_has_course = bool(re.search(COURSE_CODE_REGEX, prev_q, re.IGNORECASE)) or "môn" in prev_q.lower()
            if prev_has_course:
                is_course_aspect = any(w in q_lower for w in [
                    "tiên quyết", "tien quyet", "giáo trình", "giao trinh",
                    "đánh giá", "danh gia", "thi cử", "thi cu", "học gì", "hoc gi"
                ])
                if is_course_aspect:
                    return f"Môn {hist_course} {clean_q}"

    # ƯU TIÊN 2: Tham chiếu đại từ ngành ("ngành này", "nganh nay", "ngành đó", "nganh do")
    if hist_program:
        for p in ["ngành này", "ngành đó", "nganh nay", "nganh do"]:
            if p in q_lower:
                return clean_q.replace(p, f"ngành {hist_program}")

    # ƯU TIÊN 3: Kế thừa quy chế học vụ / cảnh cáo (ví dụ: 'nếu bị 2 lần liên tiếp thì sao?')
    if any(w in prev_q.lower() for w in ["cảnh cáo", "cảnh báo", "canh bao", "kỷ luật"]) and any(w in q_lower for w in ["nếu bị", "neu bi", "lần", "lan"]):
        return f"Cảnh cáo học vụ {clean_q}"

    # ƯU TIÊN 4: Người dùng trả lời yêu cầu làm rõ (Clarification Response)
    if is_prev_clarification:
        eff_program = curr_program or hist_program
        eff_cohort = curr_cohort or hist_cohort
        eff_campus = curr_campus or hist_campus

        if eff_program or eff_cohort or eff_campus:
            parts = [hist_base_topic]
            if eff_cohort:
                parts.append(eff_cohort)
            if eff_program:
                parts.append(f"ngành {eff_program}")
            if eff_campus:
                parts.append(f"tại {eff_campus}")
            return " ".join(parts) + " là bao nhiêu?"

    # ƯU TIÊN 5: Câu hỏi tiếp nối / so sánh (Continuation Query)
    is_continuation = is_continuation_query(clean_q)
    if is_continuation:
        eff_program = curr_program if curr_program else hist_program
        eff_cohort = curr_cohort if curr_cohort else hist_cohort
        eff_campus = curr_campus if curr_campus else hist_campus

        # Nếu đang ở Fast-Path (trước khi gọi LLM):
        if is_fast_path:
            # Chỉ can thiệp khi câu hiện tại KHÔNG hỏi về các khía cạnh học vụ khác (chuẩn đầu ra, tín chỉ, môn học...)
            is_non_fee_aspect = any(w in q_lower for w in [
                "chuẩn đầu ra", "tín chỉ", "tiên quyết", "giáo trình", "nội dung", "điểm danh",
                "cấm thi", "tốt nghiệp", "đồ án", "thực tập", "ojt", "học bổng",
                "điểm f", "thi lại hay học lại", "học tiếp", "kỳ sau", "tiếp theo", "ký túc", "ktx"
            ])
            # Tái tạo câu hỏi chuẩn xác 100%, 0ms, chống ảo giác và chuẩn hóa cả câu gõ không dấu
            if hist_base_topic == "Học phí" and not is_non_fee_aspect and eff_program and (eff_campus or eff_cohort):
                parts = ["Học phí"]
                if eff_cohort:
                    parts.append(eff_cohort)
                if eff_program:
                    parts.append(f"ngành {eff_program}")
                if eff_campus:
                    parts.append(f"tại {eff_campus}")
                return " ".join(parts) + " là bao nhiêu?"
            # Các trường hợp khác nhường quyền cho LLM Rewriter
            return None

        # 5a. Nếu câu trước KHÔNG phải là hỏi học phí (hỏi quy chế, tốt nghiệp, đồ án, chuẩn tiếng Anh...)
        if hist_base_topic != "Học phí" and prev_q:
            replaced_q = prev_q
            applied = False
            # Thay thế cơ sở nếu có cơ sở mới
            if curr_campus:
                if hist_campus and hist_campus.lower() in replaced_q.lower():
                    replaced_q = re.sub(re.escape(hist_campus), curr_campus, replaced_q, flags=re.IGNORECASE)
                    applied = True
                elif re.search(CAMPUS_NAMES_REGEX, replaced_q, re.IGNORECASE):
                    replaced_q = re.sub(CAMPUS_NAMES_REGEX, curr_campus, replaced_q, flags=re.IGNORECASE)
                    applied = True
                else:
                    replaced_q = f"{replaced_q} tại {curr_campus}"
                    applied = True
            # Thay thế ngành nếu có ngành mới
            if curr_program:
                if any(w in q_lower for w in ["tín chỉ", "bao nhiêu tín", "số tín"]):
                    return f"Ngành {curr_program} học bao nhiêu tín chỉ?"
                if hist_program and hist_program.lower() in replaced_q.lower():
                    replaced_q = re.sub(re.escape(hist_program), curr_program, replaced_q, flags=re.IGNORECASE)
                    applied = True
                else:
                    replaced_q = f"{replaced_q} ngành {curr_program}"
                    applied = True
            # Thay thế khóa nếu có khóa mới
            if curr_cohort:
                if hist_cohort and hist_cohort.lower() in replaced_q.lower():
                    replaced_q = re.sub(re.escape(hist_cohort), curr_cohort, replaced_q, flags=re.IGNORECASE)
                    applied = True
                else:
                    replaced_q = f"{replaced_q} khóa {curr_cohort}"
                    applied = True

            if applied:
                return replaced_q

        # 5b. Nếu câu trước là hỏi học phí / lệ phí
        if eff_program or eff_cohort or eff_campus:
            parts = [hist_base_topic]
            if eff_cohort:
                parts.append(eff_cohort)
            if eff_program:
                parts.append(f"ngành {eff_program}")
            if eff_campus:
                parts.append(f"tại {eff_campus}")
            return " ".join(parts) + " là bao nhiêu?"

    return None

def _post_process_rewritten(text: str) -> str:
    """Chuẩn hóa định dạng chuỗi sau khi viết lại (viết hoa chuẩn mã khóa học, ngành viết tắt)."""
    if not text:
        return text
    # Loại bỏ tiền tố 'lịch sử ' nếu LLM lỡ sinh ra
    text = re.sub(r"^lịch sử\s+", "", text, flags=re.IGNORECASE)
    # Chuẩn hóa khóa 20xx hoặc khóa xx -> Kxx (ví dụ khóa 2020 -> K20, khóa 20 -> K20)
    text = re.sub(r"\b(khóa|khoá)\s+20(\d{2})\b", lambda m: f"K{m.group(2)}", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(khóa|khoá)\s+(\d{2})\b", lambda m: f"K{m.group(2)}", text, flags=re.IGNORECASE)
    # Chuẩn hóa k20 -> K20, k21 -> K21, k22 -> K22
    text = re.sub(r"\b([kK])(\d{2})\b", lambda m: f"K{m.group(2)}", text)
    # Chuẩn hóa viết tắt ngành
    text = re.sub(r"\b(cntt)\b", "CNTT", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(ktpm)\b", "KTPM", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(attt)\b", "ATTT", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(qtkd)\b", "QTKD", text, flags=re.IGNORECASE)
    return text.strip()


def rewrite_query(current_question: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Viết lại câu hỏi hiện tại dựa trên toàn bộ lịch sử hội thoại để tạo thành câu hỏi tự chứa đầy đủ ngữ cảnh.
    Tự động phát hiện Topic Switch để ngăn chặn nhiễm độc ngữ cảnh cũ (Context Bleeding).
    """
    raw_q = current_question.strip()
    if not raw_q:
        return ""

    # Chuẩn hóa các từ viết tắt / teencode cơ bản
    clean_q = _normalize_teencode(raw_q)

    if not history:
        logger.debug(f"Không có lịch sử hội thoại. Giữ nguyên câu hỏi: '{clean_q}'")
        return _post_process_rewritten(clean_q)

    # BƯỚC 0: Self-Containedness Gate
    # Nếu câu hỏi đã tự chứa đầy đủ thực thể hoặc độc lập ngữ cảnh, giữ nguyên câu hỏi
    if is_self_contained_query(clean_q):
        logger.info(f"Self-Containedness Gate: Câu hỏi '{clean_q}' tự chứa đầy đủ ngữ cảnh độc lập. Giữ nguyên câu hỏi.")
        return _post_process_rewritten(clean_q)

    # Bước phát hiện chuyển đổi chủ đề (Topic Switch Detection)
    topic_switch_info = detect_topic_switch(clean_q, history)
    if topic_switch_info["is_topic_switch"]:
        logger.info(
            f"Phát hiện TOPIC SWITCH: '{topic_switch_info.get('previous_topic')}' -> "
            f"'{topic_switch_info.get('current_topic')}'. Giữ nguyên câu hỏi độc lập, không ghép ngữ cảnh cũ."
        )
        return _post_process_rewritten(clean_q)

    # BƯỚC 1: Rule-based & EntityNormalizer Fast-Path (chỉ xử lý các ca chắc chắn 100%)
    rule_rewritten = _rule_based_rewrite(clean_q, history, is_fast_path=True)
    if rule_rewritten and rule_rewritten.strip() != clean_q:
        logger.info(f"Viết lại thành công qua Entity Rule Fast-Path: '{clean_q}' -> '{rule_rewritten}'")
        return _post_process_rewritten(rule_rewritten)

    # BƯỚC 2: Gọi LLM Rewriter cho các câu hỏi ngữ nghĩa phức tạp & tỉnh lược (ellipsis)
    recent_history = history[-5:]
    history_lines = []
    for idx, turn in enumerate(recent_history, start=1):
        q = turn.get("query") or turn.get("rewritten_query") or ""
        a = turn.get("answer") or ""
        short_a = a[:150] + "..." if len(a) > 150 else a
        history_lines.append(f"Lượt {idx}:")
        history_lines.append(f"- Sinh viên: {q}")
        if short_a:
            history_lines.append(f"- Trợ lý: {short_a}")

    history_text = "\n".join(history_lines)
    user_prompt = (
        f"Lịch sử hội thoại trước đó:\n{history_text}\n\n"
        f"Câu hỏi hiện tại của sinh viên: {clean_q}\n"
        f"Câu hỏi viết lại đầy đủ ngữ cảnh:"
    )

    logger.info(f"Bắt đầu viết lại câu hỏi: '{clean_q}' với lịch sử {len(recent_history)} lượt.")
    rewritten = _call_llm_rewriter(user_prompt)

    if rewritten:
        logger.info(f"Viết lại thành công qua LLM: '{clean_q}' -> '{rewritten}'")
        return _post_process_rewritten(rewritten)

    # BƯỚC 3: Fallback quy tắc nếu LLM offline / mock
    rule_rewritten = _rule_based_rewrite(clean_q, history, is_fast_path=False)
    if rule_rewritten:
        logger.info(f"Viết lại thành công qua Rule Fallback: '{clean_q}' -> '{rule_rewritten}'")
        return _post_process_rewritten(rule_rewritten)

    logger.info(f"Giữ nguyên câu hỏi gốc: '{clean_q}'")
    return _post_process_rewritten(clean_q)

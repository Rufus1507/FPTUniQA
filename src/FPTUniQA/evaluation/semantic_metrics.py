"""Bộ chỉ số đánh giá năng lực Semantic Parsing (Nhóm 2 Metrics).
Đo lường:
1. Intent Accuracy: Tỷ lệ nhận diện đúng QueryIntent.
2. Slot Accuracy: Tỷ lệ trích xuất đúng các thực thể (program, cohort, campus, course_code, aspect).
3. Exact Match (EM): Tỷ lệ parsing khớp hoàn toàn cả Intent và mọi Slot.
4. Fallback Rate: Tỷ lệ Semantic Parser phải kích hoạt Regex Fallback.
"""

from typing import Any, Dict, List, Optional, Set


def normalize_value(val: Any) -> str:
    """Chuẩn hóa giá trị thực thể để so khớp công bằng."""
    if val is None:
        return ""
    v = str(val).strip().lower()
    # Chuẩn hóa một số alias phổ biến
    aliases = {
        "kỹ thuật phần mềm": "se",
        "phần mềm": "se",
        "trí tuệ nhân tạo": "ai",
        "an toàn thông tin": "ia",
        "thiết kế đồ họa": "gd",
        "hà nội": "hanoi",
        "tp.hồ chí minh": "hcm",
        "hồ chí minh": "hcm",
        "đà nẵng": "danang",
        "cần thơ": "cantho",
        "quy nhơn": "quynhon",
    }
    return aliases.get(v, v)


def compute_intent_accuracy(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
) -> float:
    """Tính tỷ lệ nhận diện đúng Intent (QueryIntent Accuracy)."""
    if not predictions or len(predictions) != len(ground_truths):
        return 0.0

    correct = 0
    for pred, gold in zip(predictions, ground_truths):
        p_intent = str(pred.get("intent", "")).lower()
        g_intent = str(gold.get("intent", "")).lower()
        # Chuẩn hóa intent tên tương đương
        if p_intent == g_intent:
            correct += 1
        elif ("tuition" in p_intent and "tuition" in g_intent) or \
             ("course" in p_intent and "course" in g_intent) or \
             ("ood" in p_intent and "ood" in g_intent) or \
             ("policy" in p_intent and "policy" in g_intent):
            correct += 1

    return round(correct / len(predictions), 4)


def compute_slot_accuracy(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
    tracked_slots: Optional[List[str]] = None,
) -> float:
    """Tính độ chính xác trên toàn bộ các slots được trích xuất (Micro-accuracy)."""
    if not predictions or len(predictions) != len(ground_truths):
        return 0.0

    if tracked_slots is None:
        tracked_slots = ["program", "cohort", "campus", "course_code", "course_aspect"]

    total_slots = 0
    correct_slots = 0

    for pred, gold in zip(predictions, ground_truths):
        p_slots = pred.get("slots", {}) or {}
        g_slots = gold.get("slots", {}) or {}

        # Duyệt qua các slot cần theo dõi
        all_keys = set(tracked_slots) | set(p_slots.keys()) | set(g_slots.keys())
        for key in all_keys:
            p_val = normalize_value(p_slots.get(key))
            g_val = normalize_value(g_slots.get(key))

            # Chỉ tính khi ít nhất một bên có giá trị hoặc nằm trong tracked_slots của gold
            if g_val or p_val:
                total_slots += 1
                if p_val == g_val:
                    correct_slots += 1

    if total_slots == 0:
        return 1.0

    return round(correct_slots / total_slots, 4)


def compute_exact_match(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
    tracked_slots: Optional[List[str]] = None,
) -> float:
    """Tính tỷ lệ Exact Match (EM): Cả intent và toàn bộ slots đều khớp hoàn toàn."""
    if not predictions or len(predictions) != len(ground_truths):
        return 0.0

    if tracked_slots is None:
        tracked_slots = ["program", "cohort", "campus", "course_code", "course_aspect"]

    em_count = 0
    for pred, gold in zip(predictions, ground_truths):
        # 1. So intent
        p_intent = str(pred.get("intent", "")).lower()
        g_intent = str(gold.get("intent", "")).lower()
        intent_match = (p_intent == g_intent) or \
            ("tuition" in p_intent and "tuition" in g_intent) or \
            ("course" in p_intent and "course" in g_intent) or \
            ("ood" in p_intent and "ood" in g_intent)

        if not intent_match:
            continue

        # 2. So slots
        p_slots = pred.get("slots", {}) or {}
        g_slots = gold.get("slots", {}) or {}

        slots_match = True
        all_keys = set(tracked_slots) | set(p_slots.keys()) | set(g_slots.keys())
        for key in all_keys:
            p_val = normalize_value(p_slots.get(key))
            g_val = normalize_value(g_slots.get(key))
            if p_val != g_val:
                slots_match = False
                break

        if slots_match:
            em_count += 1

    return round(em_count / len(predictions), 4)


def compute_fallback_rate(predictions: List[Dict[str, Any]]) -> float:
    """Tính tỷ lệ Semantic Parser phải rơi về regex fallback."""
    if not predictions:
        return 0.0

    fallback_count = 0
    for pred in predictions:
        is_fallback = (
            pred.get("fallback_used", False) is True
            or pred.get("parser_method") == "regex_fallback"
        )
        if is_fallback:
            fallback_count += 1

    return round(fallback_count / len(predictions), 4)


def evaluate_semantic_parsing_suite(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Tổng hợp 4 chỉ số Semantic Parsing."""
    return {
        "intent_accuracy": compute_intent_accuracy(predictions, ground_truths),
        "slot_accuracy": compute_slot_accuracy(predictions, ground_truths),
        "exact_match": compute_exact_match(predictions, ground_truths),
        "fallback_rate": compute_fallback_rate(predictions),
    }

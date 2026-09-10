"""Đo lường tỷ lệ ảo giác và tỷ lệ từ chối câu hỏi ngoài miền (OOD). Cả nhóm."""

from typing import Any, Dict, List


def compute_ood_rejection_accuracy(results: List[Dict[str, Any]]) -> float:
    """Đo tỷ lệ hệ thống từ chối thành công các câu hỏi ngoài miền (OOD questions)."""
    if not results:
        return 0.0

    correct_rejections = 0
    for r in results:
        # Nếu hệ thống nhận diện đúng intent ood hoặc câu trả lời chứa thông điệp từ chối
        if r.get("intent") == "ood" or "nằm ngoài phạm vi" in r.get("answer", "").lower():
            correct_rejections += 1

    return correct_rejections / len(results)


def compute_hallucination_rate(faithfulness_scores: List[float], threshold: float = 0.5) -> float:
    """Tỷ lệ câu trả lời bị coi là ảo giác (có faithfulness thấp hơn ngưỡng threshold)."""
    if not faithfulness_scores:
        return 0.0

    hallucinated_count = sum(1 for s in faithfulness_scores if s < threshold)
    return hallucinated_count / len(faithfulness_scores)

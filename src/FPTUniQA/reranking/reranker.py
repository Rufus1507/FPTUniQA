"""Interface chung của bộ reranker."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class BaseReranker(ABC):
    """Lớp cơ sở trừu tượng cho tất cả các mô hình Reranker."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Nhận vào query và danh sách docs ứng viên, trả về danh sách top_n đã xếp hạng lại kèm điểm."""
        pass

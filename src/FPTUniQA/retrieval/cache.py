"""Retrieval caching layer (in-memory with optional Redis support and configurable TTL). Phụ trách: TV2."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.retrieval.cache")


class RetrievalCache:
    """Cache thread-safe lưu kết quả truy xuất để giảm tải cho BM25, FAISS và Reranker."""

    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_entries: int = 1000,
        redis_url: Optional[str] = None,
    ):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self.redis_url = redis_url
        self._lock = threading.Lock()
        self._memory_cache: Dict[str, Tuple[float, Any]] = {}
        self._redis_client = None
        self._hits: int = 0
        self._misses: int = 0

        if self.redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(self.redis_url)
                self._redis_client.ping()
                logger.info(f"Kết nối Redis cache thành công: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Không thể kết nối Redis ({e}). Dùng in-memory cache dự phòng.")
                self._redis_client = None

    @staticmethod
    def make_cache_key(
        query: str,
        top_k: int = 10,
        candidate_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        score_threshold: Optional[float] = None,
    ) -> str:
        """Tạo khóa băm duy nhất cho tham số truy vấn."""
        data = {
            "query": query.strip().lower(),
            "top_k": top_k,
            "candidate_k": candidate_k,
            "metadata_filter": metadata_filter,
            "rerank": rerank,
            "score_threshold": score_threshold,
        }
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Lấy dữ liệu từ cache nếu còn hạn (TTL)."""
        if self._redis_client:
            try:
                raw = self._redis_client.get(f"fptuniqa:retrieval:{key}")
                if raw:
                    logger.debug(f"Cache HIT (Redis) cho key: {key[:8]}")
                    with self._lock:
                        self._hits += 1
                    return json.loads(raw.decode("utf-8"))
            except Exception as e:
                logger.warning(f"Lỗi khi đọc Redis cache: {e}")

        # In-memory lookup
        with self._lock:
            if key in self._memory_cache:
                timestamp, value = self._memory_cache[key]
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"Cache HIT (In-Memory) cho key: {key[:8]}")
                    self._hits += 1
                    return value
                else:
                    # Hết hạn
                    del self._memory_cache[key]
            self._misses += 1
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Trả về thống kê hoạt động của Cache (hits, misses, hit rate)."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = round(self._hits / total, 4) if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_lookups": total,
                "hit_rate": hit_rate,
                "cached_entries": len(self._memory_cache),
            }

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Lưu kết quả vào cache với TTL."""
        expiry = ttl or self.ttl

        if self._redis_client:
            try:
                serialized = json.dumps(value, ensure_ascii=False)
                self._redis_client.setex(f"fptuniqa:retrieval:{key}", expiry, serialized)
                return
            except Exception as e:
                logger.warning(f"Lỗi khi ghi Redis cache: {e}")

        with self._lock:
            # Dọn dẹp LRU đơn giản nếu vượt quá max_entries
            if len(self._memory_cache) >= self.max_entries:
                # Xóa 20% entries cũ nhất
                now = time.time()
                # Xóa các mục đã hết hạn trước
                expired = [k for k, (ts, _) in self._memory_cache.items() if now - ts >= self.ttl]
                for k in expired:
                    del self._memory_cache[k]
                if len(self._memory_cache) >= self.max_entries:
                    sorted_keys = sorted(self._memory_cache.keys(), key=lambda k: self._memory_cache[k][0])
                    for k in sorted_keys[: len(sorted_keys) // 5 + 1]:
                        self._memory_cache.pop(k, None)

            self._memory_cache[key] = (time.time(), value)

    def clear(self) -> None:
        """Xóa toàn bộ cache."""
        with self._lock:
            self._memory_cache.clear()
        if self._redis_client:
            try:
                keys = self._redis_client.keys("fptuniqa:retrieval:*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Lỗi khi xóa Redis cache: {e}")

    def __len__(self) -> int:
        with self._lock:
            return len(self._memory_cache)

    def __bool__(self) -> bool:
        return True

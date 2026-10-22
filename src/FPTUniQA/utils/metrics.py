"""Module quản lý Metrics và Structured Observability cho hệ thống FPTUniQA."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from FPTUniQA.utils.logger import get_logger

logger = get_logger("FPTUniQA.utils.metrics")


class MetricsTracker:
    """Bộ thu thập và tổng hợp chỉ số hiệu năng (Latency, Request Counts, Error Rates)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._requests_by_route: Dict[str, int] = {}
        self._errors_by_route: Dict[str, int] = {}
        self._latencies_by_stage: Dict[str, List[float]] = {}
        self._start_time: float = time.time()

    def record_request(
        self,
        route: str,
        latency_ms: float,
        success: bool = True,
        stage: Optional[str] = None,
    ) -> None:
        """Ghi nhận một lượt gọi request kèm độ trễ và tuyến đường."""
        with self._lock:
            self._total_requests += 1
            self._requests_by_route[route] = self._requests_by_route.get(route, 0) + 1

            if not success:
                self._total_errors += 1
                self._errors_by_route[route] = self._errors_by_route.get(route, 0) + 1

            stage_name = stage or route
            if stage_name not in self._latencies_by_stage:
                self._latencies_by_stage[stage_name] = []
            
            # Giữ tối đa 1000 mẫu độ trễ gần nhất để tính toán percentile
            if len(self._latencies_by_stage[stage_name]) >= 1000:
                self._latencies_by_stage[stage_name].pop(0)
            self._latencies_by_stage[stage_name].append(latency_ms)

    @contextmanager
    def measure_time(self, stage_name: str) -> Generator[Dict[str, float], None, None]:
        """Context manager đo thời gian thực thi (milliseconds) của một công đoạn."""
        start = time.perf_counter()
        timing_info: Dict[str, float] = {"duration_ms": 0.0}
        try:
            yield timing_info
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            timing_info["duration_ms"] = elapsed_ms
            with self._lock:
                if stage_name not in self._latencies_by_stage:
                    self._latencies_by_stage[stage_name] = []
                if len(self._latencies_by_stage[stage_name]) >= 1000:
                    self._latencies_by_stage[stage_name].pop(0)
                self._latencies_by_stage[stage_name].append(elapsed_ms)

    def get_summary(self) -> Dict[str, Any]:
        """Xuất thông tin tổng hợp dạng dictionary."""
        with self._lock:
            uptime_seconds = time.time() - self._start_time
            stage_stats: Dict[str, Any] = {}

            for stage, latencies in self._latencies_by_stage.items():
                if not latencies:
                    continue
                sorted_l = sorted(latencies)
                n = len(sorted_l)
                p95_idx = min(int(n * 0.95), n - 1)
                stage_stats[stage] = {
                    "count": n,
                    "avg_ms": round(sum(sorted_l) / n, 2),
                    "min_ms": round(sorted_l[0], 2),
                    "max_ms": round(sorted_l[-1], 2),
                    "p95_ms": round(sorted_l[p95_idx], 2),
                }

            return {
                "uptime_seconds": round(uptime_seconds, 2),
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "error_rate": round(self._total_errors / self._total_requests, 4) if self._total_requests > 0 else 0.0,
                "requests_by_route": dict(self._requests_by_route),
                "errors_by_route": dict(self._errors_by_route),
                "stages": stage_stats,
            }

    def export_prometheus(self) -> str:
        """Xuất chỉ số theo định dạng Prometheus Exposition format."""
        summary = self.get_summary()
        lines: List[str] = [
            "# HELP fptuniqa_requests_total Total number of processed requests",
            "# TYPE fptuniqa_requests_total counter",
            f"fptuniqa_requests_total {summary['total_requests']}",
            "",
            "# HELP fptuniqa_errors_total Total number of failed requests",
            "# TYPE fptuniqa_errors_total counter",
            f"fptuniqa_errors_total {summary['total_errors']}",
            "",
            "# HELP fptuniqa_uptime_seconds Server uptime in seconds",
            "# TYPE fptuniqa_uptime_seconds gauge",
            f"fptuniqa_uptime_seconds {summary['uptime_seconds']}",
        ]

        for route, count in summary["requests_by_route"].items():
            lines.append(f'fptuniqa_route_requests_total{{route="{route}"}} {count}')

        for stage, stats in summary["stages"].items():
            lines.append(f'fptuniqa_latency_avg_ms{{stage="{stage}"}} {stats["avg_ms"]}')
            lines.append(f'fptuniqa_latency_p95_ms{{stage="{stage}"}} {stats["p95_ms"]}')

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Đặt lại toàn bộ metrics."""
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._requests_by_route.clear()
            self._errors_by_route.clear()
            self._latencies_by_stage.clear()
            self._start_time = time.time()


# Singleton metrics tracker cho toàn hệ thống
metrics = MetricsTracker()

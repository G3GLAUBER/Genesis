from __future__ import annotations

from collections import Counter
from threading import RLock

from Engines.Intelligence.models import IntelligenceMetricsSnapshot, RoutingMode


class IntelligenceMetrics:
    def __init__(self) -> None:
        self._selections = 0
        self._successes = 0
        self._failures = 0
        self._by_mode: Counter[str] = Counter()
        self._by_provider: Counter[str] = Counter()
        self._lock = RLock()

    def record_selection(self, provider_id: str, mode: RoutingMode) -> None:
        with self._lock:
            self._selections += 1
            self._by_mode[mode.value] += 1
            self._by_provider[provider_id] += 1

    def record_success(self) -> None:
        with self._lock:
            self._successes += 1

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1

    def snapshot(self) -> IntelligenceMetricsSnapshot:
        with self._lock:
            return IntelligenceMetricsSnapshot(
                selections=self._selections,
                successes=self._successes,
                failures=self._failures,
                by_mode=self._by_mode,
                by_provider=self._by_provider,
            )

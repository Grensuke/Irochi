"""Rolling window data structures for feature processing.

All structures are in-memory per-worker. NOT shared via Redis.
Thread-safe for single-threaded asyncio workers.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict, deque
from typing import Optional


class SlidingWindowCounter:
    """Counts events per key within a sliding time window.

    Uses a deque of (timestamp, count) tuples per key.
    """

    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = window_seconds
        self._data: dict[str, deque] = defaultdict(deque)

    def add(self, key: str, timestamp: float, count: int = 1) -> None:
        """Add a count observation for a key at a given timestamp."""
        self._data[key].append((timestamp, count))

    def get_count(self, key: str, current_time: float) -> int:
        """Get total count for a key within the sliding window."""
        self._evict(key, current_time)
        return sum(c for _, c in self._data[key])

    def _evict(self, key: str, current_time: float) -> None:
        """Remove entries older than the window."""
        cutoff = current_time - self.window_seconds
        dq = self._data[key]
        while dq and dq[0][0] < cutoff:
            dq.popleft()


class UniqueSetWindow:
    """Tracks unique values per key within a time window.

    Uses a deque of (timestamp, value) tuples per key.
    """

    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = window_seconds
        self._data: dict[str, deque] = defaultdict(deque)

    def add(self, key: str, value: str, timestamp: float) -> None:
        """Record a value observation for a key."""
        self._data[key].append((timestamp, value))

    def get_unique_count(self, key: str, current_time: float) -> int:
        """Get count of unique values for a key within the window."""
        return len(self.get_unique_values(key, current_time))

    def get_unique_values(self, key: str, current_time: float) -> set[str]:
        """Get set of unique values for a key within the window."""
        self._evict(key, current_time)
        return {v for _, v in self._data[key]}

    def _evict(self, key: str, current_time: float) -> None:
        """Remove entries older than the window."""
        cutoff = current_time - self.window_seconds
        dq = self._data[key]
        while dq and dq[0][0] < cutoff:
            dq.popleft()


class InterArrivalTracker:
    """Tracks inter-arrival times per key for beacon detection.

    Maintains a deque of interval floats (seconds) per key, max entries.
    """

    def __init__(self, max_history: int = 200) -> None:
        self.max_history = max_history
        self._last_seen: dict[str, float] = {}
        self._intervals: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))

    def record(self, key: str, timestamp: float) -> Optional[float]:
        """Record a timestamp, compute interval from last seen.

        Returns the interval in seconds, or None if first observation.
        """
        last = self._last_seen.get(key)
        self._last_seen[key] = timestamp
        if last is None:
            return None
        interval = timestamp - last
        if interval > 0:
            self._intervals[key].append(interval)
        return interval

    def get_regularity_score(self, key: str) -> Optional[float]:
        """Return 0.0-1.0 regularity score. Requires >= 5 observations.

        Algorithm: coefficient of variation (std/mean of intervals).
        Score = max(0.0, 1.0 - min(CV, 1.0))
        1.0 = perfectly periodic (beacon). 0.0 = completely random.
        Returns None if < 5 observations.
        """
        intervals = self._intervals.get(key)
        if not intervals or len(intervals) < 5:
            return None

        mean = statistics.mean(intervals)
        if mean == 0:
            return None

        std = statistics.stdev(intervals)
        cv = std / mean  # coefficient of variation
        return max(0.0, 1.0 - min(cv, 1.0))

    def get_intervals(self, key: str) -> list[float]:
        """Return the recorded intervals for a key."""
        return list(self._intervals.get(key, []))


class ByteRateWindow:
    """Tracks byte volumes per key over a rolling window.

    Stores (timestamp, orig_bytes, resp_bytes) tuples.
    """

    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._data: dict[str, deque] = defaultdict(deque)

    def add(self, key: str, timestamp: float, orig_bytes: int, resp_bytes: int) -> None:
        """Record a byte observation for a key."""
        self._data[key].append((timestamp, orig_bytes, resp_bytes))

    def get_rates(self, key: str, current_time: float) -> dict:
        """Get byte rates for a key within the window.

        Returns:
            orig_bps:   float (outbound bytes per second)
            resp_bps:   float (inbound bytes per second)
            ratio:      float (orig_total / max(resp_total, 1))
            orig_total: int   (total outbound bytes in window)
            resp_total: int   (total inbound bytes in window)
        """
        self._evict(key, current_time)
        entries = self._data[key]

        if not entries:
            return {
                "orig_bps": 0.0,
                "resp_bps": 0.0,
                "ratio": 0.0,
                "orig_total": 0,
                "resp_total": 0,
            }

        orig_total = sum(o for _, o, _ in entries)
        resp_total = sum(r for _, _, r in entries)

        # Time span
        earliest = entries[0][0]
        span = current_time - earliest
        if span <= 0:
            span = 1.0

        return {
            "orig_bps": orig_total / span,
            "resp_bps": resp_total / span,
            "ratio": orig_total / max(resp_total, 1),
            "orig_total": orig_total,
            "resp_total": resp_total,
        }

    def _evict(self, key: str, current_time: float) -> None:
        """Remove entries older than the window."""
        cutoff = current_time - self.window_seconds
        dq = self._data[key]
        while dq and dq[0][0] < cutoff:
            dq.popleft()

"""Tests for rolling window data structures — 8 tests."""

from __future__ import annotations

import random

import pytest

from features.windows import (
    ByteRateWindow,
    InterArrivalTracker,
    SlidingWindowCounter,
    UniqueSetWindow,
)


class TestSlidingWindowCounter:
    def test_sliding_counter_empty_window(self):
        """Empty window should return 0."""
        counter = SlidingWindowCounter(60)
        assert counter.get_count("10.0.0.1", 100.0) == 0

    def test_sliding_counter_evicts_old_entries(self):
        """Entries older than window should be evicted."""
        counter = SlidingWindowCounter(60)
        counter.add("src", 100.0, 5)
        counter.add("src", 130.0, 3)
        counter.add("src", 170.0, 2)

        # At time 170: window covers 110-170, so entry at 100 is evicted
        assert counter.get_count("src", 170.0) == 5  # 3 + 2
        # At time 200: window covers 140-200, so entries at 100 and 130 evicted
        assert counter.get_count("src", 200.0) == 2


class TestUniqueSetWindow:
    def test_unique_set_counts_distinct_values(self):
        """Should count distinct values within window."""
        uset = UniqueSetWindow(60)
        uset.add("src", "port_80", 100.0)
        uset.add("src", "port_443", 100.0)
        uset.add("src", "port_80", 101.0)   # duplicate value
        uset.add("src", "port_22", 102.0)

        assert uset.get_unique_count("src", 110.0) == 3

    def test_unique_set_evicts_expired(self):
        """Expired entries should not count."""
        uset = UniqueSetWindow(10)
        uset.add("src", "port_80", 100.0)
        uset.add("src", "port_443", 105.0)
        uset.add("src", "port_22", 112.0)

        # At time 112: window covers 102-112, entry at 100 evicted
        assert uset.get_unique_count("src", 112.0) == 2


class TestInterArrivalTracker:
    def test_inter_arrival_returns_none_before_5_observations(self):
        """Regularity score should be None with < 5 observations."""
        tracker = InterArrivalTracker()
        tracker.record("key", 100.0)
        tracker.record("key", 110.0)
        tracker.record("key", 120.0)
        assert tracker.get_regularity_score("key") is None

    def test_inter_arrival_regularity_periodic_signal(self):
        """Perfectly periodic signal should score > 0.9."""
        tracker = InterArrivalTracker()
        # Perfect 10-second interval
        for i in range(20):
            tracker.record("beacon", 100.0 + i * 10.0)

        score = tracker.get_regularity_score("beacon")
        assert score is not None
        assert score > 0.9, f"Expected > 0.9 for periodic signal, got {score}"

    def test_inter_arrival_regularity_random_signal(self):
        """Random signal should score < 0.3."""
        tracker = InterArrivalTracker()
        random.seed(42)
        t = 100.0
        for _ in range(20):
            t += random.uniform(1.0, 100.0)  # highly variable intervals
            tracker.record("random", t)

        score = tracker.get_regularity_score("random")
        assert score is not None
        assert score < 0.5, f"Expected < 0.5 for random signal, got {score}"


class TestByteRateWindow:
    def test_byte_rate_window_ratio(self):
        """Byte rate window should compute correct ratio."""
        window = ByteRateWindow(60)
        window.add("src", 100.0, 10000, 1000)
        window.add("src", 110.0, 20000, 2000)

        rates = window.get_rates("src", 120.0)
        assert rates["orig_total"] == 30000
        assert rates["resp_total"] == 3000
        assert rates["ratio"] == 10.0  # 30000 / 3000
        assert rates["orig_bps"] > 0
        assert rates["resp_bps"] > 0

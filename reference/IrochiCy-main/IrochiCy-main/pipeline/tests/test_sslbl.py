"""Tests for SSLBL feed — 4 tests."""

from __future__ import annotations

import json
import time

import pytest

from intel.sslbl import SSLBLFeed


class TestSSLBLFeed:
    def test_is_malicious_returns_false_empty_blacklist(self):
        """Empty blacklist should return False for any hash."""
        feed = SSLBLFeed()
        assert feed.is_malicious("abc123") is False
        assert feed.is_malicious(None) is False

    def test_is_malicious_returns_true_on_known_hash(self):
        """Known hash in blacklist should return True."""
        feed = SSLBLFeed()
        feed._blacklist = {"abc123", "def456", "deadbeef"}
        assert feed.is_malicious("abc123") is True
        assert feed.is_malicious("ABC123") is True  # case-insensitive
        assert feed.is_malicious("unknown") is False

    @pytest.mark.asyncio
    async def test_load_from_cache_populates_blacklist(self, tmp_path):
        """Loading from cache should populate the blacklist."""
        feed = SSLBLFeed()
        cache_data = {
            "updated": int(time.time()),
            "hashes": ["hash1", "hash2", "hash3"],
            "count": 3,
        }
        cache_path = tmp_path / "sslbl_cache.json"
        cache_path.write_text(json.dumps(cache_data))
        feed.CACHE_PATH = cache_path

        await feed._load_from_cache()
        assert len(feed._blacklist) == 3
        assert "hash1" in feed._blacklist

    def test_cache_freshness_check(self, tmp_path):
        """Cache should be considered fresh within TTL."""
        feed = SSLBLFeed()

        # Fresh cache
        cache_data = {"updated": int(time.time()), "hashes": [], "count": 0}
        cache_path = tmp_path / "sslbl_cache.json"
        cache_path.write_text(json.dumps(cache_data))
        feed.CACHE_PATH = cache_path
        assert feed._is_cache_fresh() is True

        # Stale cache
        cache_data = {"updated": int(time.time()) - 90000, "hashes": [], "count": 0}
        cache_path.write_text(json.dumps(cache_data))
        assert feed._is_cache_fresh() is False

"""Abuse.ch SSLBL JA3 blacklist fetcher and cache.

URL: https://sslbl.abuse.ch/blacklist/ja3_fingerprints.json
Cache TTL: 24 hours. Cache path: intel/sslbl_cache.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class SSLBLFeed:
    """Fetches and caches the Abuse.ch SSLBL JA3 blacklist."""

    FEED_URL = "https://sslbl.abuse.ch/blacklist/ja3_fingerprints.json"
    CACHE_PATH = Path(__file__).parent / "sslbl_cache.json"
    CACHE_TTL_HOURS = 24

    def __init__(self) -> None:
        self._blacklist: set[str] = set()
        self._loaded = False

    async def ensure_loaded(self) -> None:
        """Load the blacklist from cache or fetch from SSLBL."""
        if self._loaded:
            return

        if self._is_cache_fresh():
            await self._load_from_cache()
        else:
            await self._fetch_and_cache()

        self._loaded = True

    async def _fetch_and_cache(self) -> None:
        """Fetch from SSLBL and update cache."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(self.FEED_URL)
                resp.raise_for_status()
                data = resp.json()

            if data.get("query_status") == "ok" and "data" in data:
                hashes = [
                    entry["ja3_md5"].lower()
                    for entry in data["data"]
                    if "ja3_md5" in entry
                ]
                self._blacklist = set(hashes)

                # Write cache
                cache_data = {
                    "updated": int(time.time()),
                    "hashes": list(self._blacklist),
                    "count": len(self._blacklist),
                }
                self.CACHE_PATH.write_text(json.dumps(cache_data, indent=2))
                logger.info("sslbl_feed_updated", count=len(self._blacklist))
            else:
                logger.warning("sslbl_feed_bad_response", status=data.get("query_status"))
                await self._load_from_cache()

        except Exception as exc:
            logger.warning("sslbl_fetch_failed", error=str(exc))
            await self._load_from_cache()

    async def _load_from_cache(self) -> None:
        """Load from local cache file."""
        try:
            if self.CACHE_PATH.exists():
                data = json.loads(self.CACHE_PATH.read_text())
                self._blacklist = set(h.lower() for h in data.get("hashes", []))
                logger.info("sslbl_loaded_from_cache", count=len(self._blacklist))
            else:
                logger.warning("sslbl_no_cache_available")
                self._blacklist = set()
        except Exception as exc:
            logger.error("sslbl_cache_load_failed", error=str(exc))
            self._blacklist = set()

    def is_malicious(self, ja3_hash: Optional[str]) -> bool:
        """Check if a JA3 hash is in the SSLBL blacklist."""
        if not ja3_hash or not self._blacklist:
            return False
        return ja3_hash.lower() in self._blacklist

    def _is_cache_fresh(self) -> bool:
        """Check if cache exists and was updated within TTL."""
        try:
            if not self.CACHE_PATH.exists():
                return False
            data = json.loads(self.CACHE_PATH.read_text())
            updated = data.get("updated", 0)
            age_hours = (time.time() - updated) / 3600
            return age_hours < self.CACHE_TTL_HOURS
        except Exception:
            return False


# Global singleton
sslbl_feed = SSLBLFeed()

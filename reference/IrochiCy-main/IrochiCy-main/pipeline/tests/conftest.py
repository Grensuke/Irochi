"""Pytest fixtures for pipeline tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_conn_log(fixtures_dir: Path) -> Path:
    """Return path to sample_conn.log fixture."""
    return fixtures_dir / "sample_conn.log"


@pytest.fixture
def sample_dns_log(fixtures_dir: Path) -> Path:
    """Return path to sample_dns.log fixture."""
    return fixtures_dir / "sample_dns.log"


@pytest.fixture
def sample_ssl_log(fixtures_dir: Path) -> Path:
    """Return path to sample_ssl.log fixture."""
    return fixtures_dir / "sample_ssl.log"


@pytest.fixture
def mock_producer() -> AsyncMock:
    """Create a mock NormalizerProducer."""
    producer = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.produce_event = AsyncMock()
    producer.produce_dead_letter = AsyncMock()
    producer.produce_metrics = AsyncMock()
    producer.stats = {"produced": 0, "errors": 0}
    producer._produced_count = 0
    producer._error_count = 0
    return producer

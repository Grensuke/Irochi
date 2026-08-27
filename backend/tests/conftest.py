"""Pytest fixtures for Irochi backend tests."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Synchronous test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


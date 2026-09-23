import json
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
import requests
from aiokafka import AIOKafkaProducer

from app.config import settings

BASE_URL = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"


@pytest_asyncio.fixture
async def live_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def admin_token() -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": settings.initial_admin_username,
            "password": settings.initial_admin_password,
        },
    )
    if response.status_code != 200:
        pytest.exit(f"Failed to login as admin: {response.text}")
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def analyst_user(admin_token: str) -> dict:
    username = f"e2e_analyst_{uuid4().hex[:8]}"
    password = "E2eTestPass123!"
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create analyst
    response = requests.post(
        f"{BASE_URL}/users/",
        json={
            "username": username,
            "email": f"{username}@test.local",
            "password": password,
            "role": "analyst",
        },
        headers=admin_headers,
    )
    if response.status_code != 201:
        pytest.exit(f"Failed to create analyst user: {response.text}")
    
    user_data = response.json()
    
    # Login as analyst to get token
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
    )
    if login_response.status_code != 200:
        pytest.exit(f"Failed to login with new analyst user: {login_response.text}")
        
    user_data["token"] = login_response.json()["access_token"]
    
    yield user_data
    
    # Teardown: deactivate analyst
    requests.delete(f"{BASE_URL}/users/{user_data['id']}", headers=admin_headers)


@pytest.fixture
def analyst_headers(analyst_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {analyst_user['token']}"}


@pytest_asyncio.fixture
async def redpanda_producer() -> AsyncGenerator[AIOKafkaProducer, None]:
    producer = AIOKafkaProducer(bootstrap_servers=settings.redpanda_brokers)
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()

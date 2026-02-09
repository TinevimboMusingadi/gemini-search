import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from multimodal_search.main import app
from multimodal_search.core.config import get_settings, Settings

# --- Fixtures ---

@pytest.fixture(scope="session")
def settings_override():
    """
    Override settings for tests.
    We can set specific env vars or mock values here.
    """
    # Example: Use an in-memory DB or a test-specific project ID if needed
    # os.environ["VECTOR_STORE_BACKEND"] = "memory"
    # return get_settings()
    pass

@pytest.fixture(scope="module")
def test_client() -> Generator[TestClient, None, None]:
    """
    Synchronous TestClient for standard endpoint testing.
    """
    with TestClient(app) as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous client for async endpoint testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

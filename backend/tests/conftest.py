import os
import sys
from typing import Generator
import pytest
from starlette.testclient import TestClient

# Ensure backend directory is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set test environment variables
os.environ["APP_ENV"] = "test"
os.environ["HINDSIGHT_TIMEOUT"] = "0.5"
os.environ["HINDSIGHT_BASE_URL"] = "http://127.0.0.1:59999"
os.environ["HINDSIGHT_BANK_ID"] = "test-incident-bank"

from app.core.config import Settings
from app.main import app


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing isolated Settings instance for testing."""
    return Settings(
        app_name="Test Incident Agent",
        app_env="test",
        hindsight_base_url="http://127.0.0.1:59999",
        hindsight_bank_id="test-incident-bank",
        hindsight_timeout=0.5,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Synchronous Starlette TestClient fixture for testing endpoints."""
    with TestClient(app) as test_client:
        yield test_client

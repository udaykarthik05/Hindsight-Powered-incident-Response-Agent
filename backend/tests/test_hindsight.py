from unittest.mock import AsyncMock, MagicMock
import pytest
from starlette.testclient import TestClient

from hindsight_client_api.models.retain_response import RetainResponse
from hindsight_client_api.models.recall_response import RecallResponse
from hindsight_client_api.models.reflect_response import ReflectResponse
from hindsight_client_api.models.version_response import VersionResponse

from app.core.config import Settings
from app.hindsight.client import HindsightClientManager
from app.hindsight.memory import (
    HindsightMemoryService,
    HindsightOperationError,
    MemoryRecallInput,
    MemoryReflectInput,
    MemoryRetainInput,
)


@pytest.mark.asyncio
async def test_client_manager_initialization() -> None:
    """Test HindsightClientManager correctly initializes Hindsight client with config."""
    settings = Settings(
        hindsight_base_url="https://api.hindsight.vectorize.io",
        hindsight_api_key="test-api-key",
        hindsight_bank_id="unit-test-bank",
        hindsight_timeout=5.0,
    )
    manager = HindsightClientManager(settings)
    client = manager.get_client()

    assert client is not None
    await manager.close()


@pytest.mark.asyncio
async def test_check_connection_unreachable() -> None:
    """
    Test check_connection when the Hindsight server is unreachable.
    Must return connected=False without raising an unhandled exception or faking success.
    """
    settings = Settings(
        hindsight_base_url="http://127.0.0.1:59999",  # Port where nothing is listening
        hindsight_timeout=0.5,
    )
    manager = HindsightClientManager(settings)
    status = await manager.check_connection()
    await manager.close()

    assert status.connected is False
    assert status.base_url == "http://127.0.0.1:59999"
    assert status.error is not None
    assert "Verify the server is running" in status.message or "Ensure the Hindsight server is running" in status.message


@pytest.mark.asyncio
async def test_check_connection_success_mocked() -> None:
    """Test check_connection reporting when the server is reachable."""
    settings = Settings(
        hindsight_base_url="http://mocked-hindsight:8888",
        hindsight_bank_id="incident-bank",
    )
    manager = HindsightClientManager(settings)

    mock_client = MagicMock()
    mock_version = MagicMock(spec=VersionResponse)
    mock_version.version = "0.10.1"
    mock_client.aget_version = AsyncMock(return_value=mock_version)
    mock_client.aclose = AsyncMock()

    manager._client = mock_client
    status = await manager.check_connection()
    await manager.close()

    assert status.connected is True
    assert status.server_version == "0.10.1"
    assert status.error is None
    assert "successfully" in status.message.lower()


@pytest.mark.asyncio
async def test_memory_service_retain() -> None:
    """Test retain operation passes correct arguments to official Hindsight client."""
    mock_client = MagicMock()
    mock_retain_response = MagicMock(spec=RetainResponse)
    mock_retain_response.success = True
    mock_retain_response.bank_id = "test-bank"
    mock_client.aretain = AsyncMock(return_value=mock_retain_response)

    manager = MagicMock()
    manager.get_client.return_value = mock_client

    service = HindsightMemoryService(manager=manager)
    input_data = MemoryRetainInput(
        content="Incident INC-501: DB Connection pool exhausted due to unindexed query.",
        context="Postmortem",
        metadata={"service": "auth-service", "severity": "P1"},
        tags=["database", "p1"],
        bank_id="test-bank",
    )

    result = await service.retain(input_data)
    assert result == mock_retain_response
    mock_client.aretain.assert_awaited_once_with(
        bank_id="test-bank",
        content="Incident INC-501: DB Connection pool exhausted due to unindexed query.",
        context="Postmortem",
        metadata={"service": "auth-service", "severity": "P1"},
        tags=["database", "p1"],
    )


@pytest.mark.asyncio
async def test_memory_service_retain_failure_raises_error() -> None:
    """Test retain error wraps underlying exception in HindsightOperationError."""
    mock_client = MagicMock()
    mock_client.aretain = AsyncMock(side_effect=RuntimeError("Connection refused by peer"))

    manager = MagicMock()
    manager.get_client.return_value = mock_client

    service = HindsightMemoryService(manager=manager)
    input_data = MemoryRetainInput(content="Test content", bank_id="test-bank")

    with pytest.raises(HindsightOperationError) as exc_info:
        await service.retain(input_data)
    assert "Connection refused by peer" in str(exc_info.value)


@pytest.mark.asyncio
async def test_memory_service_recall() -> None:
    """Test recall operation passes query and parameters to official Hindsight client."""
    mock_client = MagicMock()
    mock_recall_response = MagicMock(spec=RecallResponse)
    mock_recall_response.results = []
    mock_client.arecall = AsyncMock(return_value=mock_recall_response)

    manager = MagicMock()
    manager.get_client.return_value = mock_client

    service = HindsightMemoryService(manager=manager)
    input_data = MemoryRecallInput(
        query="database connection pool timeout",
        budget="high",
        max_tokens=2048,
        tags=["database"],
        bank_id="test-bank",
    )

    result = await service.recall(input_data)
    assert result == mock_recall_response
    mock_client.arecall.assert_awaited_once_with(
        bank_id="test-bank",
        query="database connection pool timeout",
        types=None,
        max_tokens=2048,
        budget="high",
        tags=["database"],
    )


@pytest.mark.asyncio
async def test_memory_service_reflect() -> None:
    """Test reflect operation passes query and budget to official Hindsight client."""
    mock_client = MagicMock()
    mock_reflect_response = MagicMock(spec=ReflectResponse)
    mock_reflect_response.text = "Synthesized hypothesis: Past incidents show DB connection pool exhaustion."
    mock_client.areflect = AsyncMock(return_value=mock_reflect_response)

    manager = MagicMock()
    manager.get_client.return_value = mock_client

    service = HindsightMemoryService(manager=manager)
    input_data = MemoryReflectInput(
        query="What root causes have triggered auth-service outages previously?",
        budget="mid",
        bank_id="test-bank",
    )

    result = await service.reflect(input_data)
    assert result == mock_reflect_response
    mock_client.areflect.assert_awaited_once_with(
        bank_id="test-bank",
        query="What root causes have triggered auth-service outages previously?",
        budget="mid",
        context=None,
        tags=None,
    )


def test_api_hindsight_status_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/hindsight/status returns structured status without failing."""
    response = client.get("/api/v1/hindsight/status")
    assert response.status_code == 200

    data = response.json()
    assert "connected" in data
    assert "base_url" in data
    assert "bank_id" in data
    assert "message" in data

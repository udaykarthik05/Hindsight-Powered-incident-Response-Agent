from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from hindsight_client_api.models.recall_response import RecallResponse
from hindsight_client_api.models.retain_response import RetainResponse

from app.core.config import Settings
from app.hindsight.client import HindsightConnectionStatus
from app.hindsight.seed import run_hindsight_seeding


@pytest.mark.asyncio
async def test_seed_script_offline_handling() -> None:
    """Ensure run_hindsight_seeding returns False cleanly when Hindsight is unreachable."""
    test_settings = Settings(
        hindsight_base_url="http://127.0.0.1:59998",  # unreachable port
        hindsight_timeout=0.2,
    )
    result = await run_hindsight_seeding(settings=test_settings)
    assert result is False


@pytest.mark.asyncio
async def test_seed_script_success_flow_mocked() -> None:
    """Ensure run_hindsight_seeding exercises RETAIN for all seed incidents and performs RECALL."""
    test_settings = Settings(
        hindsight_base_url="http://mocked-hindsight:8888",
        hindsight_bank_id="test-bank",
    )

    mock_status = HindsightConnectionStatus(
        connected=True,
        base_url="http://mocked-hindsight:8888",
        bank_id="test-bank",
        server_version="0.10.1",
        message="Connected",
    )

    mock_retain_res = MagicMock(spec=RetainResponse)
    mock_retain_res.success = True
    mock_retain_res.operation_id = "op-mock-123"

    mock_recall_res = MagicMock(spec=RecallResponse)
    mock_recall_res.results = [
        MagicMock(
            text="Historical Incident Report: INC-2025-101 - Auth Service DB Connection Pool Exhaustion",
            scores={"combined": 0.92},
            tags=["database", "connection-pool"],
        )
    ]

    with (
        patch("app.hindsight.seed.HindsightClientManager") as MockManagerClass,
        patch("app.hindsight.seed.HindsightMemoryService") as MockServiceClass,
    ):
        mock_manager = MockManagerClass.return_value
        mock_manager.check_connection = AsyncMock(return_value=mock_status)
        mock_manager.close = AsyncMock()

        mock_service = MockServiceClass.return_value
        mock_service.retain = AsyncMock(return_value=mock_retain_res)
        mock_service.recall = AsyncMock(return_value=mock_recall_res)

        success = await run_hindsight_seeding(settings=test_settings)
        assert success is True

        # Verify retain was called 10 times (once for each seed incident)
        assert mock_service.retain.await_count == 10

        # Verify recall was called with the target query
        assert mock_service.recall.await_count == 1
        recall_args = mock_service.recall.call_args[0][0]
        assert "database connection" in recall_args.query.lower()

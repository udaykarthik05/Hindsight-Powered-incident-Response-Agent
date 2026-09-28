from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest

from hindsight_client_api.models.recall_response import RecallResponse
from hindsight_client_api.models.reflect_response import ReflectResponse

from app.agent.incident_agent import IncidentResponseAgent
from app.agent.models import InvestigationResult
from app.core.config import Settings
from app.hindsight.memory import HindsightConnectionError, HindsightMemoryService
from app.schemas.incident import Incident, IncidentStatus, Severity


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        incident_id="INC-2026-901",
        title="Payment Service Gateway Timeout and Connection Errors",
        description="Users experiencing 504 Gateway Timeouts during checkout. Database connections failing.",
        severity=Severity.CRITICAL,
        affected_service="payment-service",
        timestamp=datetime.now(timezone.utc),
        logs=[
            "ERROR: psycopg2.OperationalError: FATAL: remaining connection slots are reserved",
            "WARN: ReadTimeout: HTTPSConnectionPool read timed out (read timeout=5.0)",
        ],
        error_messages=["Connection slots exhausted", "ReadTimeout"],
        status=IncidentStatus.OPEN,
    )


@pytest.mark.asyncio
async def test_agent_investigate_hindsight_offline_graceful(sample_incident: Incident) -> None:
    """Ensure agent produces valid investigation when Hindsight is offline without faking memory."""
    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    mock_memory_service.recall = AsyncMock(
        side_effect=HindsightConnectionError("Connection to Hindsight server refused")
    )

    settings = Settings(llm_provider="heuristic")
    agent = IncidentResponseAgent(
        memory_service=mock_memory_service,
        settings=settings,
    )

    result = await agent.investigate(sample_incident)

    assert isinstance(result, InvestigationResult)
    assert result.incident_id == sample_incident.incident_id
    assert result.historical_context.available is False
    assert len(result.historical_context.recalled_incidents) == 0
    assert result.historical_context.reflection_summary is None
    assert "offline" in result.historical_context.status_message.lower()

    # Verify hypotheses and steps still generated from current evidence
    assert len(result.hypotheses) > 0
    assert len(result.investigation_steps) > 0
    assert len(result.remediation_recommendations.immediate_mitigation) > 0
    assert len(result.remediation_recommendations.long_term_fix) > 0
    assert any("offline" in lim.lower() for lim in result.limitations)


@pytest.mark.asyncio
async def test_agent_investigate_hindsight_online_flow(sample_incident: Incident) -> None:
    """Ensure agent incorporates recalled memories and reflection when Hindsight is reachable."""
    mock_memory_service = MagicMock(spec=HindsightMemoryService)

    # Mock recall results
    mock_item = MagicMock()
    mock_item.text = "Historical Incident: INC-2025-101 Auth Service DB pool exhaustion"
    mock_item.scores = {"combined": 0.94}
    mock_item.tags = ["database", "connection-pool"]
    mock_item.metadata = {
        "incident_id": "INC-2025-101",
        "title": "Auth Service DB Pool Exhaustion",
        "service": "auth-service",
    }

    mock_recall_res = MagicMock(spec=RecallResponse)
    mock_recall_res.results = [mock_item]
    mock_memory_service.recall = AsyncMock(return_value=mock_recall_res)

    # Mock reflect results
    mock_reflect_res = MagicMock(spec=ReflectResponse)
    mock_reflect_res.text = "Historical pattern shows connection pool leaks occurred in token validation."
    mock_memory_service.reflect = AsyncMock(return_value=mock_reflect_res)

    settings = Settings(llm_provider="heuristic")
    agent = IncidentResponseAgent(
        memory_service=mock_memory_service,
        settings=settings,
    )

    result = await agent.investigate(sample_incident)

    assert result.historical_context.available is True
    assert len(result.historical_context.recalled_incidents) == 1
    assert result.historical_context.recalled_incidents[0].incident_id == "INC-2025-101"
    assert result.historical_context.reflection_summary == mock_reflect_res.text

    # Verify that hypotheses reference the historical incident
    all_related = []
    for h in result.hypotheses:
        all_related.extend(h.related_historical_incidents)
    assert "INC-2025-101" in all_related


@pytest.mark.asyncio
async def test_investigation_result_structured_validation(sample_incident: Incident) -> None:
    """Verify structured output constraints and types on InvestigationResult."""
    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    mock_memory_service.recall = AsyncMock(side_effect=HindsightConnectionError("offline"))

    agent = IncidentResponseAgent(
        memory_service=mock_memory_service,
        settings=Settings(llm_provider="heuristic"),
    )
    result = await agent.investigate(sample_incident)

    assert 0.0 <= result.confidence <= 1.0
    for h in result.hypotheses:
        assert 0.0 <= h.confidence <= 1.0
        assert len(h.supporting_evidence) > 0
    for step in result.investigation_steps:
        assert step.step_number > 0
        assert step.action != ""
        assert step.target_system != ""

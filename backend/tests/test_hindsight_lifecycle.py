from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.hindsight.lifecycle import (
    HindsightMemoryLifecycle,
    IncidentMemoryBuilder,
    MemoryRetentionResult,
    RetentionStatus,
)
from app.hindsight.memory import (
    HindsightMemoryService,
    HindsightOperationError,
    MemoryRetainInput,
)
from app.repositories.incident_repository import InMemoryIncidentRepository
from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentResolve,
    IncidentStatus,
    Severity,
)


@pytest.fixture
def sample_resolved_incident() -> Incident:
    return Incident(
        incident_id="INC-2026-TEST-001",
        title="Payment Gateway Timeout Outage",
        description="Checkout service failing with 504 gateway timeout under peak loads.",
        severity=Severity.CRITICAL,
        affected_service="payment-service",
        timestamp=datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc),
        logs=[
            "ERROR: Connection pool exhausted (active=50/50)",
            "WARN: Request timed out after 5000ms",
        ],
        error_messages=["ConnectionTimeoutError: Pool exhausted"],
        status=IncidentStatus.RESOLVED,
        root_cause="Leaked database connections in HTTP checkout session handler.",
        mitigation="Enforced strict session context managers and doubled connection pool size.",
        created_at=datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc),
        resolved_at=datetime(2026, 9, 28, 13, 0, 0, tzinfo=timezone.utc),
    )


def test_incident_memory_builder_structure(sample_resolved_incident: Incident) -> None:
    """Verify memory builder constructs rich, structured 5-section narrative."""
    retain_input: MemoryRetainInput = IncidentMemoryBuilder.build(sample_resolved_incident)

    content = str(retain_input.content)
    assert "POSTMORTEM RECORD: INC-2026-TEST-001" in content
    assert "1. WHAT HAPPENED" in content
    assert "2. WHAT WAS OBSERVED" in content
    assert "3. WHAT WAS CONFIRMED" in content
    assert "4. WHAT FIXED IT" in content
    assert "5. WHAT SHOULD BE REMEMBERED" in content

    assert sample_resolved_incident.root_cause in content
    assert sample_resolved_incident.mitigation in content
    assert "payment-service" in content

    # Check metadata
    assert retain_input.metadata["incident_id"] == "INC-2026-TEST-001"
    assert retain_input.metadata["service"] == "payment-service"
    assert retain_input.metadata["status"] == "resolved"

    # Check tags
    assert "payment-service" in retain_input.tags
    assert "postmortem" in retain_input.tags
    assert "resolved" in retain_input.tags


@pytest.mark.asyncio
async def test_retain_resolved_incident_success_mocked(sample_resolved_incident: Incident) -> None:
    """Test successful retention flow into Hindsight."""
    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    mock_response = MagicMock()
    mock_response.units_retained = 3
    mock_memory_service.retain = AsyncMock(return_value=mock_response)

    lifecycle = HindsightMemoryLifecycle(memory_service=mock_memory_service)
    result: MemoryRetentionResult = await lifecycle.retain_resolved_incident(sample_resolved_incident)

    assert result.status == RetentionStatus.RETAINED
    assert result.incident_id == sample_resolved_incident.incident_id
    assert result.memory_units_count == 3
    assert "successfully retained" in result.message.lower()
    mock_memory_service.retain.assert_called_once()


@pytest.mark.asyncio
async def test_retain_unresolved_incident_not_attempted() -> None:
    """Test that open/investigating incidents are not retained as postmortems."""
    open_incident = Incident(
        incident_id="INC-OPEN-001",
        title="Active Incident",
        description="Ongoing outage description",
        severity=Severity.HIGH,
        affected_service="auth-service",
        timestamp=datetime.now(timezone.utc),
        status=IncidentStatus.OPEN,
    )

    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    lifecycle = HindsightMemoryLifecycle(memory_service=mock_memory_service)
    result = await lifecycle.retain_resolved_incident(open_incident)

    assert result.status == RetentionStatus.NOT_ATTEMPTED
    assert "not resolved" in result.message.lower()
    mock_memory_service.retain.assert_not_called()


@pytest.mark.asyncio
async def test_retain_missing_root_cause_not_attempted() -> None:
    """Test that resolved incidents missing root cause or mitigation are skipped."""
    incomplete_incident = Incident(
        incident_id="INC-INCOMPLETE-001",
        title="Resolved but no postmortem",
        description="Outage description",
        severity=Severity.LOW,
        affected_service="worker-service",
        timestamp=datetime.now(timezone.utc),
        status=IncidentStatus.RESOLVED,
        root_cause=None,
        mitigation=None,
    )

    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    lifecycle = HindsightMemoryLifecycle(memory_service=mock_memory_service)
    result = await lifecycle.retain_resolved_incident(incomplete_incident)

    assert result.status == RetentionStatus.NOT_ATTEMPTED
    assert "without confirmed root cause" in result.message.lower()
    mock_memory_service.retain.assert_not_called()


@pytest.mark.asyncio
async def test_retain_idempotency_prevents_duplicate(sample_resolved_incident: Incident) -> None:
    """Test that already-retained incidents are not retained a second time."""
    sample_resolved_incident.memory_status = RetentionStatus.RETAINED.value

    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    lifecycle = HindsightMemoryLifecycle(memory_service=mock_memory_service)
    result = await lifecycle.retain_resolved_incident(sample_resolved_incident)

    assert result.status == RetentionStatus.ALREADY_RETAINED
    assert "previously retained" in result.message.lower()
    mock_memory_service.retain.assert_not_called()


@pytest.mark.asyncio
async def test_retain_hindsight_offline_graceful_degrade(sample_resolved_incident: Incident) -> None:
    """Test that Hindsight connection failure produces RETENTION_FAILED without raising an unhandled exception."""
    mock_memory_service = MagicMock(spec=HindsightMemoryService)
    mock_memory_service.retain = AsyncMock(
        side_effect=HindsightOperationError("Cannot connect to host localhost:8888")
    )

    lifecycle = HindsightMemoryLifecycle(memory_service=mock_memory_service)
    result = await lifecycle.retain_resolved_incident(sample_resolved_incident)

    assert result.status == RetentionStatus.RETENTION_FAILED
    assert "offline or unreachable" in result.message.lower()
    assert result.error is not None


def test_resolve_endpoint_with_retention_mocked_success(client: TestClient) -> None:
    """Test POST /api/v1/incidents/{id}/resolve triggers RETAIN and returns memory status."""
    # 1. Create incident
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Incident with Memory Lifecycle",
            "description": "Critical database deadlock under concurrency.",
            "severity": "critical",
            "affected_service": "billing-service",
            "error_messages": ["psycopg2.OperationalError: deadlock detected"],
        },
    )
    incident_id = create_res.json()["incident_id"]

    # 2. Resolve incident with mocked Hindsight memory service
    with patch("app.hindsight.lifecycle.HindsightMemoryService.retain", new_callable=AsyncMock) as mock_retain:
        mock_res = MagicMock()
        mock_res.units_retained = 2
        mock_retain.return_value = mock_res

        resolve_res = client.post(
            f"/api/v1/incidents/{incident_id}/resolve",
            json={
                "root_cause": "Unordered row locks during concurrent invoice processing.",
                "mitigation": "Enforced strict alphabetical lock ordering in transaction.",
            },
        )
        assert resolve_res.status_code == 200
        data = resolve_res.json()

        assert data["status"] == "resolved"
        assert data["memory_status"] == "retained"
        assert "successfully retained" in data["memory_message"].lower()
        mock_retain.assert_called_once()

    # 3. Verify GET /api/v1/incidents/{id} reflects retained memory status
    get_res = client.get(f"/api/v1/incidents/{incident_id}")
    assert get_res.status_code == 200
    assert get_res.json()["memory_status"] == "retained"


def test_resolve_endpoint_idempotency_second_call_avoids_duplicate_retain(client: TestClient) -> None:
    """Test calling resolve twice does not duplicate retention when already retained."""
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Idempotent Resolution Test",
            "description": "Worker memory exhaustion test.",
            "severity": "medium",
            "affected_service": "worker-service",
        },
    )
    incident_id = create_res.json()["incident_id"]

    with patch("app.hindsight.lifecycle.HindsightMemoryService.retain", new_callable=AsyncMock) as mock_retain:
        mock_res = MagicMock()
        mock_res.units_retained = 1
        mock_retain.return_value = mock_res

        # First resolve: should retain
        res1 = client.post(
            f"/api/v1/incidents/{incident_id}/resolve",
            json={"root_cause": "Memory leak in task generator.", "mitigation": "Added garbage collection trigger."},
        )
        assert res1.status_code == 200
        assert res1.json()["memory_status"] == "retained"
        assert mock_retain.call_count == 1

        # Second resolve: should detect already retained
        res2 = client.post(
            f"/api/v1/incidents/{incident_id}/resolve",
            json={"root_cause": "Memory leak in task generator.", "mitigation": "Added garbage collection trigger."},
        )
        assert res2.status_code == 200
        assert res2.json()["memory_status"] == "already_retained"
        # Mock retain should NOT have been called a second time
        assert mock_retain.call_count == 1

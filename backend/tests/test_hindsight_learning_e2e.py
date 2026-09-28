from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agent.incident_agent import IncidentResponseAgent
from app.agent.models import InvestigationResult
from app.hindsight.lifecycle import (
    HindsightMemoryLifecycle,
    IncidentMemoryBuilder,
    RetentionStatus,
)
from app.hindsight.memory import (
    HindsightMemoryService,
    MemoryRecallInput,
    MemoryReflectInput,
    MemoryRetainInput,
)
from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentStatus,
    Severity,
)


@pytest.mark.asyncio
async def test_complete_learning_lifecycle_mocked() -> None:
    """
    Demonstrate and verify the complete Hindsight Learning Lifecycle (mocked verification):
    
    1. Incident A (Historical):
       - Occurs on payment-service with 504 Gateway Timeouts
       - Resolved with confirmed root cause ("Connection pool leak in session handler")
       - Retained into Hindsight via RETAIN
    
    2. Incident B (Future Incident):
       - Occurs later on payment-service with similar pool timeout symptoms
       - Investigation Agent queries Hindsight via RECALL
       - Retrieves Incident A's postmortem
       - Runs REFLECT to extract comparative lessons
       - Synthesizes hypotheses: cites Incident A as historical precedent
       - Strict Evidence Separation: Does NOT blindly claim Incident A is the confirmed cause.
    """
    mock_memory_service = MagicMock(spec=HindsightMemoryService)

    # --------------------------------------------------------------------------
    # Step 1: Retain Incident A Postmortem
    # --------------------------------------------------------------------------
    incident_a = Incident(
        incident_id="INC-2025-099",
        title="Payment Gateway Connection Exhaustion Outage",
        description="Checkout service failing with 504 Gateway Timeout during flash promo.",
        severity=Severity.CRITICAL,
        affected_service="payment-service",
        timestamp=datetime(2025, 9, 10, 14, 0, 0, tzinfo=timezone.utc),
        logs=["ERROR: Connection pool exhausted (active=50/50)"],
        error_messages=["ConnectionTimeoutError: Pool exhausted after 5000ms"],
        status=IncidentStatus.RESOLVED,
        root_cause="Leaked database connection slots in unclosed transaction session context.",
        mitigation="Increased max_connections to 150 and wrapped checkout calls in strict finally block.",
        resolved_at=datetime(2025, 9, 10, 15, 30, 0, tzinfo=timezone.utc),
    )

    retain_response_mock = MagicMock()
    retain_response_mock.units_retained = 2
    mock_memory_service.retain = AsyncMock(return_value=retain_response_mock)

    lifecycle = HindsightMemoryLifecycle(memory_service=mock_memory_service)
    retain_result = await lifecycle.retain_resolved_incident(incident_a)

    assert retain_result.status == RetentionStatus.RETAINED
    mock_memory_service.retain.assert_called_once()
    retained_call_args = mock_memory_service.retain.call_args[0][0]
    assert isinstance(retained_call_args, MemoryRetainInput)
    assert "POSTMORTEM RECORD: INC-2025-099" in str(retained_call_args.content)
    assert "Leaked database connection slots" in str(retained_call_args.content)

    # --------------------------------------------------------------------------
    # Step 2: New Incident B Occurs
    # --------------------------------------------------------------------------
    incident_b = Incident(
        incident_id="INC-2026-200",
        title="Spike in 504 Timeouts on Checkout API",
        description="Payment service reporting client gateway timeouts under heavy shopping volume.",
        severity=Severity.HIGH,
        affected_service="payment-service",
        timestamp=datetime(2026, 9, 28, 18, 0, 0, tzinfo=timezone.utc),
        logs=[
            "ERROR: HikariPool-1 - Connection is not available, request timed out after 5000ms.",
            "WARN: 504 Gateway Timeout returned to checkout frontend",
        ],
        error_messages=["504 Gateway Timeout", "Connection is not available"],
        status=IncidentStatus.OPEN,
    )

    # --------------------------------------------------------------------------
    # Step 3: Mock RECALL to return Incident A
    # --------------------------------------------------------------------------
    mock_match = MagicMock()
    mock_match.text = (
        "POSTMORTEM RECORD: INC-2025-099 - Payment Gateway Connection Exhaustion Outage. "
        "Root cause: Leaked database connection slots in unclosed transaction session context. "
        "Mitigation: Increased max_connections to 150."
    )
    mock_match.scores = {"combined": 0.94}
    mock_match.tags = ["payment-service", "connection-pool", "postmortem"]
    mock_match.metadata = {
        "incident_id": "INC-2025-099",
        "title": "Payment Gateway Connection Exhaustion Outage",
        "service": "payment-service",
    }

    mock_recall_response = MagicMock()
    mock_recall_response.results = [mock_match]
    mock_memory_service.recall = AsyncMock(return_value=mock_recall_response)

    # --------------------------------------------------------------------------
    # Step 4: Mock REFLECT to synthesize comparative insight
    # --------------------------------------------------------------------------
    mock_reflect_response = MagicMock()
    mock_reflect_response.text = (
        "Comparative reflection: Both INC-2026-200 and historical INC-2025-099 share "
        "identical connection pool timeout signatures on payment-service under load. "
        "In INC-2025-099, connection leaks in checkout sessions were confirmed. "
        "Recommendation: Prioritize connection pool utilization diagnostics."
    )
    mock_memory_service.reflect = AsyncMock(return_value=mock_reflect_response)

    # --------------------------------------------------------------------------
    # Step 5: Run Investigation Agent
    # --------------------------------------------------------------------------
    agent = IncidentResponseAgent(memory_service=mock_memory_service)
    investigation: InvestigationResult = await agent.investigate(incident_b)

    # --------------------------------------------------------------------------
    # Step 6: Verify Investigation Uses Recalled Context with Strict Separation
    # --------------------------------------------------------------------------
    # RECALL was invoked with evidence query
    mock_memory_service.recall.assert_called_once()
    recall_query_arg = mock_memory_service.recall.call_args[0][0].query
    assert "payment-service" in recall_query_arg

    # Historical context was populated
    assert investigation.historical_context.available is True
    assert len(investigation.historical_context.recalled_incidents) == 1
    assert investigation.historical_context.recalled_incidents[0].incident_id == "INC-2025-099"
    assert "INC-2025-099" in str(investigation.historical_context.reflection_summary)

    # Hypotheses cite INC-2025-099 as historical precedent
    assert len(investigation.hypotheses) > 0
    top_hypothesis = investigation.hypotheses[0]
    assert "INC-2025-099" in top_hypothesis.related_historical_incidents

    # Strict Evidence Separation: Top hypothesis remains framed as a hypothesis, not confirmed root cause
    assert "hypothesis" in top_hypothesis.hypothesis.lower() or "saturation" in top_hypothesis.hypothesis.lower()
    assert top_hypothesis.confidence < 1.0  # Empirical verification required

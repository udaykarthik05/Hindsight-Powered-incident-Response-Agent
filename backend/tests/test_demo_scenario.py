from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest

from hindsight_client_api.models.recall_response import RecallResponse
from hindsight_client_api.models.reflect_response import ReflectResponse

from app.agent.incident_agent import IncidentResponseAgent
from app.core.config import Settings
from app.hindsight.memory import HindsightMemoryService
from app.schemas.incident import Incident, IncidentStatus, Severity


@pytest.mark.asyncio
async def test_demo_scenario_payment_api_investigation() -> None:
    """
    Test the exact end-to-end scenario specified in Phase 3 Section 13:
    
    NEW INCIDENT:
    'Payment API is returning 504 errors.
     Database connections are timing out.
     Latency increased sharply after a deployment.'
    """
    demo_incident = Incident(
        incident_id="INC-DEMO-PAYMENT",
        title="Payment API 504 Error Spike and Database Latency",
        description=(
            "Payment API is returning 504 errors. Database connections are timing out. "
            "Latency increased sharply after a deployment."
        ),
        severity=Severity.CRITICAL,
        affected_service="payment-service",
        timestamp=datetime.now(timezone.utc),
        logs=[
            "2026-03-10 14:02:11 ERROR [pool.py:90] HikariPool-1 - Connection is not available, request timed out after 30005ms.",
            "2026-03-10 14:02:40 ERROR [server.py:112] 504 Gateway Timeout on POST /api/v1/charge",
            "2026-03-10 14:03:00 WARN  [deploy.py:55] Release v3.4.1 finished deployment 12 minutes before error spike.",
        ],
        error_messages=[
            "504 Gateway Timeout",
            "Connection is not available, request timed out after 30005ms.",
        ],
        status=IncidentStatus.OPEN,
    )

    # Mock Hindsight memory returning historical incidents (INC-2025-101 and INC-2025-102)
    mock_memory_service = MagicMock(spec=HindsightMemoryService)

    mock_res_1 = MagicMock()
    mock_res_1.text = "Historical Incident INC-2025-101: Auth DB pool exhaustion after middleware release"
    mock_res_1.scores = {"combined": 0.95}
    mock_res_1.tags = ["database", "connection-pool", "auth-service"]
    mock_res_1.metadata = {
        "incident_id": "INC-2025-101",
        "title": "Auth Service Database Connection Pool Exhaustion",
        "service": "auth-service",
    }

    mock_res_2 = MagicMock()
    mock_res_2.text = "Historical Incident INC-2025-102: Payment gateway latency spike and thread starvation"
    mock_res_2.scores = {"combined": 0.91}
    mock_res_2.tags = ["payment", "latency", "timeout"]
    mock_res_2.metadata = {
        "incident_id": "INC-2025-102",
        "title": "Payment Gateway API Latency Spike & Cascading Worker Starvation",
        "service": "payment-service",
    }

    mock_recall_response = MagicMock(spec=RecallResponse)
    mock_recall_response.results = [mock_res_1, mock_res_2]
    mock_memory_service.recall = AsyncMock(return_value=mock_recall_response)

    mock_reflect_response = MagicMock(spec=ReflectResponse)
    mock_reflect_response.text = (
        "Comparative synthesis: Similar symptoms in INC-2025-101 involved leaked connections after a release. "
        "Recommend inspecting connection pool saturation and evaluating deployment rollback."
    )
    mock_memory_service.reflect = AsyncMock(return_value=mock_reflect_response)

    # Run agent investigation
    agent = IncidentResponseAgent(
        memory_service=mock_memory_service,
        settings=Settings(llm_provider="heuristic"),
    )

    result = await agent.investigate(demo_incident)

    # 1. Verify Observed Signals
    signals = result.observed_signals
    assert "payment" in signals.affected_service.lower() or "payment" in str(signals.infrastructure_components).lower()
    assert any("504" in err for err in signals.error_types)
    assert any("connection" in comp.lower() or "database" in comp.lower() for comp in signals.infrastructure_components)
    assert signals.deployment_correlated is True

    # 2. Verify Historical Context
    assert result.historical_context.available is True
    recalled_ids = [m.incident_id for m in result.historical_context.recalled_incidents]
    assert "INC-2025-101" in recalled_ids
    assert "INC-2025-102" in recalled_ids
    assert result.historical_context.reflection_summary is not None

    # 3. Verify Hypotheses
    hypotheses_text = " ".join([h.hypothesis.lower() for h in result.hypotheses])
    assert "connection pool" in hypotheses_text
    assert "deployment regression" in hypotheses_text
    assert "timeout" in hypotheses_text or "latency" in hypotheses_text

    # 4. Verify Investigation Steps
    steps_actions = " ".join([s.action.lower() for s in result.investigation_steps])
    assert "connection pool" in steps_actions or "pool" in steps_actions
    assert "deployment" in steps_actions or "diff" in steps_actions
    assert "latency" in steps_actions or "metrics" in steps_actions

    # 5. Verify Remediation Recommendations
    all_remediations = " ".join(
        result.remediation_recommendations.immediate_mitigation +
        result.remediation_recommendations.long_term_fix
    ).lower()
    assert "rollback" in all_remediations
    assert "connection" in all_remediations
    assert "timeout" in all_remediations or "circuit" in all_remediations

    # 6. Verify Evidence vs Hypothesis Separation
    for h in result.hypotheses:
        assert len(h.supporting_evidence) > 0
        assert h.confidence > 0.0

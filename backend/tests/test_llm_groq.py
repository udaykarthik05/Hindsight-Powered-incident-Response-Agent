from datetime import datetime, timezone
import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.agent.incident_agent import IncidentResponseAgent
from app.agent.llm import HeuristicReasoningEngine, LLMClient
from app.agent.models import (
    HistoricalContext,
    HistoricalIncidentMatch,
    Hypothesis,
    InvestigationResult,
    ObservedSignals,
)
from app.agent.prompts import SYSTEM_PROMPT, build_investigation_user_prompt
from app.core.config import Settings
from app.schemas.incident import Incident, Severity, IncidentStatus


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        incident_id="INC-2026-TEST-001",
        title="Payment Service Checkout Degradation",
        description="Checkout service failing with 504 Gateway Timeouts under flash sale load.",
        severity=Severity.CRITICAL,
        affected_service="payment-service",
        timestamp=datetime.now(timezone.utc),
        logs=["[ERROR] connection pool exhausted (active=50/50, waiting=240)"],
        error_messages=["ConnectionTimeoutError: Client unable to acquire database connection"],
        status=IncidentStatus.INVESTIGATING,
    )


@pytest.fixture
def sample_signals() -> ObservedSignals:
    return ObservedSignals(
        affected_service="payment-service",
        error_types=["ConnectionTimeoutError"],
        infrastructure_components=["database", "connection_pool"],
        suspected_categories=["Database Connection Pool Exhaustion"],
        deployment_correlated=True,
        extracted_keywords=["connection_pool", "timeout", "payment-service"],
    )


@pytest.fixture
def sample_historical() -> HistoricalContext:
    return HistoricalContext(
        available=True,
        query_used="payment-service ConnectionTimeoutError database",
        recalled_incidents=[
            HistoricalIncidentMatch(
                incident_id="INC-2025-101",
                title="Postgres Connection Leak",
                service="payment-service",
                similarity_score=0.88,
                summary="Connection pool saturated due to unindexed transaction queries.",
                tags=["database", "connection_pool"],
            )
        ],
        reflection_summary="Historical precedent shows pool exhaustion caused by unindexed queries.",
        status_message="Retrieved 1 historical precedent from Hindsight.",
    )


def test_groq_configuration_defaults():
    """Verify Groq default configuration and model."""
    settings = Settings(llm_api_key=None)
    assert settings.llm_provider == "groq"
    assert settings.llm_model == "openai/gpt-oss-20b"
    assert "api.groq.com" in settings.llm_base_url
    assert not settings.llm_api_key


def test_groq_api_key_alias(monkeypatch):
    """Verify GROQ_API_KEY alias populates llm_api_key."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_mock_key_12345")
    settings = Settings()
    assert settings.llm_api_key == "gsk_test_mock_key_12345"


def test_heuristic_fallback_when_key_missing(sample_incident, sample_signals, sample_historical):
    """Verify that absence of LLM API key safely triggers heuristic reasoning."""
    settings = Settings(llm_provider="groq", llm_api_key=None)
    client = LLMClient(settings=settings)

    result = HeuristicReasoningEngine.generate(sample_incident, sample_signals, sample_historical)
    assert isinstance(result, InvestigationResult)
    assert result.reasoning_mode == "heuristic_fallback"
    assert result.llm_provider is None
    assert result.llm_model is None
    assert len(result.hypotheses) > 0
    assert result.confidence > 0.0


@pytest.mark.asyncio
async def test_groq_llm_success_mocked(sample_incident, sample_signals, sample_historical):
    """Verify successful Groq LLM reasoning dispatch, parsing, and reasoning_mode = 'llm'."""
    settings = Settings(
        llm_provider="groq",
        llm_api_key="gsk_mock_valid_key",
        llm_model="openai/gpt-oss-20b",
        llm_base_url="https://api.groq.com/openai/v1",
    )
    client = LLMClient(settings=settings)

    mock_llm_json = {
        "incident_id": sample_incident.incident_id,
        "summary": "Groq LLM analysis indicates database pool exhaustion on payment-service.",
        "hypotheses": [
            {
                "hypothesis": "Database connection pool exhausted by runaway catalog queries.",
                "supporting_evidence": ["ConnectionTimeoutError", "active=50/50 connections"],
                "contradicting_evidence": ["No database disk space alerts reported"],
                "related_historical_incidents": ["INC-2025-101"],
                "confidence": 0.89,
            }
        ],
        "investigation_steps": [
            {
                "step_number": 1,
                "action": "Run pg_stat_activity query to inspect active transaction locks.",
                "rationale": "Identify queries holding connection pool slots.",
                "target_system": "PostgreSQL",
            }
        ],
        "remediation_recommendations": {
            "immediate_mitigation": ["Increase connection pool ceiling to 150"],
            "long_term_fix": ["Add index on catalog transaction tables"],
        },
        "confidence": 0.89,
        "limitations": ["APM traces for individual worker threads were not provided."],
    }

    mock_response = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await client.generate_investigation(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="Investigate incident",
            incident=sample_incident,
            signals=sample_signals,
            historical=sample_historical,
        )

        assert isinstance(result, InvestigationResult)
        assert result.reasoning_mode == "llm"
        assert result.llm_provider == "groq"
        assert result.llm_model == "openai/gpt-oss-20b"
        assert len(result.hypotheses) == 1
        assert result.hypotheses[0].confidence == 0.89
        assert result.hypotheses[0].related_historical_incidents == ["INC-2025-101"]


@pytest.mark.asyncio
async def test_groq_rate_limit_429_graceful_fallback(sample_incident, sample_signals, sample_historical):
    """Verify Groq HTTP 429 rate limit triggers graceful heuristic fallback."""
    settings = Settings(
        llm_provider="groq",
        llm_api_key="gsk_mock_valid_key",
    )
    client = LLMClient(settings=settings)

    mock_req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    mock_resp = httpx.Response(status_code=429, json={"error": {"message": "Rate limit exceeded"}}, request=mock_req)
    err = httpx.HTTPStatusError("429 Too Many Requests", request=mock_req, response=mock_resp)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = err

        result = await client.generate_investigation(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="Investigate incident",
            incident=sample_incident,
            signals=sample_signals,
            historical=sample_historical,
        )

        assert isinstance(result, InvestigationResult)
        assert result.reasoning_mode == "heuristic_fallback"
        assert result.llm_provider is None
        assert len(result.hypotheses) > 0


@pytest.mark.asyncio
async def test_groq_timeout_graceful_fallback(sample_incident, sample_signals, sample_historical):
    """Verify Groq timeout triggers graceful heuristic fallback."""
    settings = Settings(llm_provider="groq", llm_api_key="gsk_mock_valid_key")
    client = LLMClient(settings=settings)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out after 45s")

        result = await client.generate_investigation(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="Investigate incident",
            incident=sample_incident,
            signals=sample_signals,
            historical=sample_historical,
        )

        assert isinstance(result, InvestigationResult)
        assert result.reasoning_mode == "heuristic_fallback"


@pytest.mark.asyncio
async def test_evidence_boundary_sanitizes_hallucinated_incident_ids(sample_incident, sample_signals, sample_historical):
    """Verify that hallucinated historical incident IDs not present in Hindsight recall are filtered out."""
    settings = Settings(llm_provider="groq", llm_api_key="gsk_mock_valid_key")
    client = LLMClient(settings=settings)

    # LLM hallucinates an unverified incident ID 'INC-FAKE-999' alongside genuine 'INC-2025-101'
    mock_llm_json = {
        "incident_id": sample_incident.incident_id,
        "summary": "Summary with fabricated precedent",
        "hypotheses": [
            {
                "hypothesis": "Candidate hypothesis",
                "supporting_evidence": ["Log traces"],
                "contradicting_evidence": [],
                "related_historical_incidents": ["INC-2025-101", "INC-FAKE-999"],
                "confidence": 0.80,
            }
        ],
        "investigation_steps": [
            {
                "step_number": 1,
                "action": "Check metrics",
                "rationale": "Verify load",
                "target_system": "System",
            }
        ],
        "remediation_recommendations": {
            "immediate_mitigation": ["Scale"],
            "long_term_fix": ["Refactor"],
        },
        "confidence": 0.80,
        "limitations": [],
    }

    mock_response = httpx.Response(
        status_code=200,
        json={"choices": [{"message": {"content": json.dumps(mock_llm_json)}}]},
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await client.generate_investigation(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="Investigate",
            incident=sample_incident,
            signals=sample_signals,
            historical=sample_historical,
        )

        # INC-FAKE-999 must have been filtered out by evidence boundary enforcement
        assert "INC-2025-101" in result.hypotheses[0].related_historical_incidents
        assert "INC-FAKE-999" not in result.hypotheses[0].related_historical_incidents


def test_security_no_api_key_in_model_dumps(sample_incident, sample_signals, sample_historical):
    """Verify secrets are never present in model serialization or string outputs."""
    result = HeuristicReasoningEngine.generate(sample_incident, sample_signals, sample_historical)
    dumped = result.model_dump_json()
    assert "gsk_" not in dumped
    assert "api_key" not in dumped


def test_prompt_includes_hindsight_recall_and_reflect(sample_incident, sample_signals, sample_historical):
    """Verify that build_investigation_user_prompt injects Hindsight RECALL items and REFLECT synthesis."""
    prompt = build_investigation_user_prompt(sample_incident, sample_signals, sample_historical)
    assert sample_incident.incident_id in prompt
    assert "INC-2025-101" in prompt
    assert "Postgres Connection Leak" in prompt
    assert "Historical precedent shows pool exhaustion caused by unindexed queries." in prompt

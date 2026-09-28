"""
Live demonstration and verification runner for the AI Incident Response Agent.

Usage:
    python backend/verify_investigation.py
"""

import asyncio
import sys
from datetime import datetime, timezone

from app.agent.incident_agent import get_incident_agent
from app.agent.models import InvestigationResult
from app.core.config import get_settings
from app.repositories.incident_repository import get_incident_repository
from app.schemas.incident import Incident, IncidentStatus, Severity


async def run_investigation_demo() -> InvestigationResult:
    settings = get_settings()
    repo = get_incident_repository()
    agent = get_incident_agent()

    # Load from repository or create demo incident
    incident = repo.get("INC-2025-101")
    if not incident:
        incident = Incident(
            incident_id="INC-DEMO-LIVE",
            title="Payment API 504 Timeout and Database Latency Spike",
            description=(
                "Payment API is returning 504 errors. Database connections are timing out. "
                "Latency increased sharply 15 minutes after a backend deployment."
            ),
            severity=Severity.CRITICAL,
            affected_service="payment-service",
            timestamp=datetime.now(timezone.utc),
            logs=[
                "2026-03-28 14:02:11 ERROR [pool.py:90] HikariPool-1 - Connection is not available, request timed out after 30005ms.",
                "2026-03-28 14:02:40 ERROR [server.py:112] 504 Gateway Timeout on POST /api/v1/charge",
                "2026-03-28 14:03:00 WARN  [deploy.py:55] Release v3.4.1 finished rollout 15 minutes before error spike.",
            ],
            error_messages=[
                "504 Gateway Timeout",
                "Connection is not available, request timed out after 30005ms.",
            ],
            status=IncidentStatus.OPEN,
        )

    print("=" * 78)
    print(" AI INCIDENT RESPONSE AGENT — INVESTIGATION PIPELINE")
    print("=" * 78)
    print(f"Target Incident : {incident.incident_id} - '{incident.title}'")
    print(f"Service         : {incident.affected_service}")
    print(f"Severity        : {incident.severity.value.upper()}")
    print(f"LLM Provider    : {settings.llm_provider} (Model: {settings.llm_model})")
    print(f"API Key Set     : {'Yes' if settings.llm_api_key else 'No (using built-in reasoning)'}")
    print("-" * 78)
    print("Running deterministic analysis, Hindsight query, and reasoning engine...")

    try:
        result = await agent.investigate(incident)
    finally:
        await agent.memory_service.manager.close()

    print("-" * 78)
    print(" INVESTIGATION EXECUTIVE SUMMARY")
    print("-" * 78)
    print(result.summary)
    print(f"\nOverall Confidence: {result.confidence * 100:.0f}%")

    print("\n" + "-" * 78)
    print(" OBSERVED SIGNALS (Deterministic Analysis)")
    print("-" * 78)
    print(f"  • Classified Errors : {', '.join(result.observed_signals.error_types) or 'None'}")
    print(f"  • Subsystems        : {', '.join(result.observed_signals.infrastructure_components) or 'None'}")
    print(f"  • Suspected Causes  : {', '.join(result.observed_signals.suspected_categories)}")
    print(f"  • Deployment Link   : {'YES (correlates with recent release)' if result.observed_signals.deployment_correlated else 'NO'}")
    print(f"  • Salient Keywords  : {', '.join(result.observed_signals.extracted_keywords)}")

    print("\n" + "-" * 78)
    print(" HINDSIGHT HISTORICAL MEMORY CONTEXT")
    print("-" * 78)
    print(f"  • Memory Status     : {'ONLINE - Memories Recalled' if result.historical_context.available else 'OFFLINE - Unreachable'}")
    print(f"  • Query Used        : \"{result.historical_context.query_used}\"")
    print(f"  • Status Message    : {result.historical_context.status_message}")
    if result.historical_context.recalled_incidents:
        print("  • Recalled Matches  :")
        for m in result.historical_context.recalled_incidents:
            print(f"    - [{m.incident_id}] {m.title} (Service: {m.service})")
    if result.historical_context.reflection_summary:
        print(f"  • Synthesis/Reflect : {result.historical_context.reflection_summary}")

    print("\n" + "-" * 78)
    print(" RANKED ROOT-CAUSE HYPOTHESES")
    print("-" * 78)
    for idx, h in enumerate(result.hypotheses, start=1):
        print(f"  [{idx}] Hypothesis ({h.confidence * 100:.0f}% confidence):")
        print(f"      {h.hypothesis}")
        print(f"      Supporting Evidence   : {', '.join(h.supporting_evidence)}")
        if h.contradicting_evidence:
            print(f"      Contradicting Evidence: {', '.join(h.contradicting_evidence)}")
        if h.related_historical_incidents:
            print(f"      Historical Precedent  : {', '.join(h.related_historical_incidents)}")
        print()

    print("-" * 78)
    print(" RECOMMENDED NON-DESTRUCTIVE INVESTIGATION STEPS")
    print("-" * 78)
    for step in result.investigation_steps:
        print(f"  Step {step.step_number} [{step.target_system}]:")
        print(f"    Action   : {step.action}")
        print(f"    Rationale: {step.rationale}")

    print("\n" + "-" * 78)
    print(" REMEDIATION RECOMMENDATIONS")
    print("-" * 78)
    print("  Immediate Mitigation (Stop Customer Impact):")
    for imm in result.remediation_recommendations.immediate_mitigation:
        print(f"    • {imm}")
    print("\n  Long-Term Architectural Fixes (Prevent Recurrence):")
    for fix in result.remediation_recommendations.long_term_fix:
        print(f"    • {fix}")

    print("\n" + "-" * 78)
    print(" LIMITATIONS & ASSUMPTIONS")
    print("-" * 78)
    for lim in result.limitations:
        print(f"  * {lim}")
    print("=" * 78)

    return result


def main() -> None:
    asyncio.run(run_investigation_demo())


if __name__ == "__main__":
    main()

import json
from typing import Any, Dict, List, Optional
import httpx

from app.agent.models import (
    HistoricalContext,
    Hypothesis,
    InvestigationResult,
    InvestigationStep,
    ObservedSignals,
    RemediationPlan,
)
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.incident import Incident

logger = get_logger("agent.llm")


class HeuristicReasoningEngine:
    """
    Built-in intelligent rule-based reasoning engine.
    
    Used when no external LLM API key is configured or as a high-reliability
    offline fallback, synthesizing deterministic signals and Hindsight memory.
    """

    @classmethod
    def generate(
        cls,
        incident: Incident,
        signals: ObservedSignals,
        historical: HistoricalContext,
    ) -> InvestigationResult:
        logger.info("Generating investigation reasoning via heuristic engine for %s", incident.incident_id)

        # 1. Generate ranked hypotheses
        hypotheses: List[Hypothesis] = []
        historical_ids = [m.incident_id for m in historical.recalled_incidents]

        if "Database Connection Pool Exhaustion" in signals.suspected_categories:
            db_history = [hid for hid in historical_ids if "101" in hid or "pool" in hid.lower()]
            hypotheses.append(
                Hypothesis(
                    hypothesis=(
                        "Database connection pool saturation: idle or leaked connections under load "
                        f"have exhausted available connection slots on {incident.affected_service}."
                    ),
                    supporting_evidence=[
                        *signals.error_types,
                        f"Subsystems involved: {', '.join(signals.infrastructure_components)}",
                        *([f"Correlated with recent code/deployment changes"] if signals.deployment_correlated else []),
                    ],
                    contradicting_evidence=["Database server CPU or memory utilization may still appear normal."],
                    related_historical_incidents=db_history or (["INC-2025-101"] if historical.available else []),
                    confidence=0.88 if signals.deployment_correlated else 0.80,
                )
            )

        if signals.deployment_correlated:
            hypotheses.append(
                Hypothesis(
                    hypothesis=(
                        f"Deployment regression in {incident.affected_service}: recently shipped release or schema "
                        "migration introduced an unindexed query, lock contention, or connection leak."
                    ),
                    supporting_evidence=[
                        "Incident description/logs explicitly correlate onset with recent deployment/rollout",
                        f"Affected service: {incident.affected_service}",
                    ],
                    contradicting_evidence=["Errors might stem from an external third-party or infrastructure provider."],
                    related_historical_incidents=[hid for hid in historical_ids if "105" in hid or "deploy" in hid.lower()],
                    confidence=0.75,
                )
            )

        if "API Latency & Timeout Spike" in signals.suspected_categories or "payment_gateway" in signals.infrastructure_components:
            hypotheses.append(
                Hypothesis(
                    hypothesis=(
                        "Upstream dependency latency spike: slow responses from a downstream or external dependency "
                        f"are causing worker thread starvation in {incident.affected_service}."
                    ),
                    supporting_evidence=[
                        f"Observed timeout indicators: {', '.join(signals.error_types)}",
                        "High latency or 504 Gateway Timeouts reported by clients",
                    ],
                    contradicting_evidence=["Local application CPU load remains low without internal crashes."],
                    related_historical_incidents=[hid for hid in historical_ids if "102" in hid],
                    confidence=0.72,
                )
            )

        # Fallback default hypothesis if specific patterns not matched
        if not hypotheses:
            hypotheses.append(
                Hypothesis(
                    hypothesis=f"Transient resource exhaustion or network degradation affecting {incident.affected_service}.",
                    supporting_evidence=signals.error_types or [f"Observed error logs: {len(incident.logs)} entries"],
                    contradicting_evidence=["Limited telemetry available in initial incident description."],
                    related_historical_incidents=historical_ids[:2],
                    confidence=0.60,
                )
            )

        # 2. Generate concrete, non-destructive investigation steps
        steps: List[InvestigationStep] = []
        step_num = 1

        if "database" in signals.infrastructure_components or "connection_pool" in signals.infrastructure_components:
            steps.append(
                InvestigationStep(
                    step_number=step_num,
                    action="Inspect connection pool metrics: check active vs idle connections and queue wait duration.",
                    rationale="Confirm if connection pool ceiling is saturated and identify leaking client threads.",
                    target_system="PostgreSQL / Database Pool",
                )
            )
            step_num += 1

        if signals.deployment_correlated:
            steps.append(
                InvestigationStep(
                    step_number=step_num,
                    action="Check git commit diff and recent deployment log for the last release to the service.",
                    rationale="Isolate newly introduced middleware, database queries, or configuration changes.",
                    target_system="CI/CD Pipeline / GitHub",
                )
            )
            step_num += 1

        steps.append(
            InvestigationStep(
                step_number=step_num,
                action=f"Correlate request latency and error rate spikes in application APM for {incident.affected_service}.",
                rationale="Determine exact timeline onset and whether specific endpoints are uniquely impacted.",
                target_system="APM / Prometheus Metrics",
            )
        )
        step_num += 1

        # 3. Generate remediation recommendations (immediate vs long-term)
        immediate = []
        long_term = []

        if signals.deployment_correlated:
            immediate.append(
                f"Prepare and evaluate immediate rollback of the latest deployment to {incident.affected_service} "
                "if connection saturation or error rate started concurrently."
            )
        if "connection_pool" in signals.infrastructure_components or "database" in signals.infrastructure_components:
            immediate.append("Temporarily increase connection pool capacity or restart starved service pods to flush idle sockets.")
            long_term.append("Enforce strict context-manager lifecycle handling (RAII) for all database sessions.")
            long_term.append("Configure Prometheus alert threshold at 80% connection pool saturation.")
        if "API Latency & Timeout Spike" in signals.suspected_categories:
            immediate.append("Tune client timeouts to aggressive ceilings (< 5s) and trip circuit breaker on degraded downstreams.")
            long_term.append("Implement asynchronous queueing for long-running downstream interactions.")

        if not immediate:
            immediate.append("Restart unhealthy pods or service instances to restore baseline availability.")
        if not long_term:
            long_term.append("Implement automated synthetic health checks and metric alarms on error rates.")

        # 4. Limitations
        limitations: List[str] = []
        if not historical.available:
            limitations.append(
                "Hindsight memory was offline; analysis generated solely from current incident telemetry without historical cross-referencing."
            )
        else:
            limitations.append(f"Retrieved {len(historical.recalled_incidents)} historical incidents for context; patterns should be verified empirically.")
        limitations.append("Investigative recommendations are informational and require verification by the on-call engineer.")

        summary = (
            f"Investigation into {incident.title} ({incident.incident_id}) on service '{incident.affected_service}'. "
            f"Observed signals indicate {', '.join(signals.suspected_categories)}. "
            f"Primary hypothesis ({hypotheses[0].confidence * 100:.0f}% confidence): {hypotheses[0].hypothesis}"
        )

        return InvestigationResult(
            incident_id=incident.incident_id,
            summary=summary,
            observed_signals=signals,
            historical_context=historical,
            hypotheses=hypotheses,
            investigation_steps=steps,
            remediation_recommendations=RemediationPlan(
                immediate_mitigation=immediate,
                long_term_fix=long_term,
            ),
            confidence=round(hypotheses[0].confidence, 2),
            limitations=limitations,
        )


class LLMClient:
    """Manages reasoning engine requests, dispatching to OpenAI-compatible LLM or heuristic fallback."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def generate_investigation(
        self,
        system_prompt: str,
        user_prompt: str,
        incident: Incident,
        signals: ObservedSignals,
        historical: HistoricalContext,
    ) -> InvestigationResult:
        """
        Produce a structured InvestigationResult.
        
        If an API key is present and provider is configured, calls the external LLM.
        Otherwise, seamlessly uses the HeuristicReasoningEngine.
        """
        api_key = self.settings.llm_api_key
        provider = self.settings.llm_provider.lower()

        # If no API key or provider set to heuristic, use built-in reasoning
        if not api_key or provider == "heuristic":
            logger.info("Using built-in reasoning engine (provider: %s, API key configured: %s)", provider, bool(api_key))
            return HeuristicReasoningEngine.generate(incident, signals, historical)

        # Call OpenAI-compatible endpoint
        endpoint = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.settings.llm_model,
            "temperature": self.settings.llm_temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        logger.info("Dispatching incident reasoning to LLM endpoint: %s (model: %s)", endpoint, self.settings.llm_model)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                parsed_json = json.loads(raw_content)

                # Ensure observed_signals and historical_context are attached
                parsed_json["incident_id"] = incident.incident_id
                parsed_json["observed_signals"] = signals.model_dump()
                parsed_json["historical_context"] = historical.model_dump()

                return InvestigationResult(**parsed_json)
        except Exception as err:
            logger.warning(
                "LLM API request failed (%s: %s). Falling back gracefully to built-in reasoning engine.",
                type(err).__name__,
                err,
            )
            return HeuristicReasoningEngine.generate(incident, signals, historical)

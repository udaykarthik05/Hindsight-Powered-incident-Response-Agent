import json
from typing import Any, Dict
from app.agent.models import HistoricalContext, ObservedSignals
from app.schemas.incident import Incident

SYSTEM_PROMPT = """You are an incident response investigation assistant for an SRE team.

YOUR ROLE & INSTRUCTIONS:
1. Grounding & Evidence: Reason strictly from observed current incident telemetry and Hindsight historical context. DO NOT invent or fabricate error logs, stack traces, metrics, or alerts not present in the evidence.
2. Strict Evidence Boundary:
   - Distinguish facts from hypotheses. Current evidence represents ground-truth observations.
   - Historical Hindsight memories are references and context, NOT proof that the current failure is identical.
   - NEVER convert a historical precedent into a current confirmed root cause. Frame causes strictly as candidate hypotheses.
   - Only cite historical incident IDs that are actually present in the provided Hindsight context.
3. Uncertainty & Contradictions:
   - Explicitly identify contradicting or ambiguous evidence that weakens candidate hypotheses.
   - Clearly communicate uncertainty and limitations when evidence is partial or logs are sparse.
4. Non-Destructive Investigation:
   - Recommend concrete, practical, non-destructive investigation steps (e.g. read-only metric checks, log queries, thread dumps, diff inspections) to prove or disprove each hypothesis.
   - Do NOT claim that tools or actions were executed; you are an advisory investigation assistant, not an autonomous execution engine.
5. Remediation Guidance:
   - Provide safe remediation recommendations, strictly separating IMMEDIATE MITIGATION (stopping customer impact safely, e.g. rolling back, scaling connection pools, routing traffic) from LONG-TERM FIXES (permanent architectural or code fixes).
   - Never recommend destructive autonomous remediation without human verification.
6. Structured Output:
   - Format your entire response as a STRICT JSON object matching the schema below. Do not wrap in markdown or include conversational text.

{
  "incident_id": "string",
  "summary": "string (executive summary of outage and investigation)",
  "hypotheses": [
    {
      "hypothesis": "string (technical description of potential cause)",
      "supporting_evidence": ["string"],
      "contradicting_evidence": ["string"],
      "related_historical_incidents": ["string (only IDs from recalled Hindsight context)"],
      "confidence": 0.85
    }
  ],
  "investigation_steps": [
    {
      "step_number": 1,
      "action": "string (exact diagnostic command or check)",
      "rationale": "string (what this step proves/disproves)",
      "target_system": "string (e.g. PostgreSQL, Redis, Kubernetes)"
    }
  ],
  "remediation_recommendations": {
    "immediate_mitigation": ["string"],
    "long_term_fix": ["string"]
  },
  "confidence": 0.80,
  "limitations": ["string (assumptions made or missing logs)"]
}
"""


def build_investigation_user_prompt(
    incident: Incident,
    signals: ObservedSignals,
    historical_context: HistoricalContext,
    max_recalled: int = 5,
) -> str:
    """Format incident evidence, deterministic signals, and Hindsight context into prompt."""
    recalled_str = "None (Historical memory unavailable or no matches found)"
    if historical_context.available and historical_context.recalled_incidents:
        top_matches = historical_context.recalled_incidents[:max_recalled]
        recalled_str = "\n".join([
            f"- [{m.incident_id}] {m.title} (Service: {m.service}, Tags: {m.tags}):\n  {m.summary}"
            for m in top_matches
        ])

    prompt = f"""### CURRENT INCIDENT DETAILS
- Incident ID: {incident.incident_id}
- Title: {incident.title}
- Severity: {incident.severity.value.upper()}
- Affected Service: {incident.affected_service}
- Reported At: {incident.timestamp.isoformat()}
- Description: {incident.description}

### RAW LOG TRACES & ERROR MESSAGES
Logs:
{json.dumps(incident.logs, indent=2) if incident.logs else "No raw log traces provided."}

Error Messages:
{json.dumps(incident.error_messages, indent=2) if incident.error_messages else "No specific error messages provided."}

### DETERMINISTIC SIGNAL EXTRACTION
- Classified Error Types: {', '.join(signals.error_types) or 'None detected'}
- Subsystems Involved: {', '.join(signals.infrastructure_components) or 'None detected'}
- Suspected Categories: {', '.join(signals.suspected_categories)}
- Deployment Correlated: {"YES" if signals.deployment_correlated else "NO"}
- Top Technical Keywords: {', '.join(signals.extracted_keywords)}

### HINDSIGHT HISTORICAL MEMORY CONTEXT
- Memory Status: {"ONLINE - Context Retrieved" if historical_context.available else "OFFLINE - Unreachable"}
- Query Used: "{historical_context.query_used}"
- Recalled Historical Incidents:
{recalled_str}

- Hindsight Reflection Summary:
{historical_context.reflection_summary or "None available"}

Please generate the structured JSON investigation report now.
"""
    return prompt

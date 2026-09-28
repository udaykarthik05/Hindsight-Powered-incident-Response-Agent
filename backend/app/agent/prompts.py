import json
from typing import Any, Dict
from app.agent.models import HistoricalContext, ObservedSignals
from app.schemas.incident import Incident

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and AI Incident Commander assisting an engineering team in diagnosing and mitigating software outages.

YOUR ROLE & INSTRUCTIONS:
1. Thoroughly examine the current incident evidence, extracted technical signals, and historical memory from past incidents.
2. DO NOT claim a confirmed root cause unless explicit verified proof is present. Frame conclusions as technical HYPOTHESES ranked by probability, noting supporting evidence, contradicting evidence, and related historical precedent.
3. Distinguish between current observations and historical memory:
   - Historical incidents are evidence and context, NOT proof that the current failure is identical.
   - Note key similarities as well as differences.
   - If historical memory was offline/unavailable, clearly acknowledge that analysis is based solely on current telemetry.
4. Recommend concrete, NON-DESTRUCTIVE investigation steps that an engineer can execute immediately to confirm or refute each hypothesis.
5. Provide actionable remediation recommendations clearly separating IMMEDIATE MITIGATION (stopping customer impact, e.g. rollbacks, rate limiting, temporary scaling) from LONG-TERM FIXES (permanent code or architectural changes).
6. Format your final response as a STRICT JSON object matching this schema:

{
  "incident_id": "string",
  "summary": "string (executive summary of outage and investigation)",
  "hypotheses": [
    {
      "hypothesis": "string (technical description of potential cause)",
      "supporting_evidence": ["string"],
      "contradicting_evidence": ["string"],
      "related_historical_incidents": ["string (e.g. INC-2025-101)"],
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
) -> str:
    """Format incident evidence, deterministic signals, and Hindsight context into prompt."""
    recalled_str = "None (Historical memory unavailable or no matches found)"
    if historical_context.available and historical_context.recalled_incidents:
        recalled_str = "\n".join([
            f"- [{m.incident_id}] {m.title} (Service: {m.service}, Tags: {m.tags}):\n  {m.summary}"
            for m in historical_context.recalled_incidents
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

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ObservedSignals(BaseModel):
    """Signals extracted from deterministic analysis of current incident evidence."""
    affected_service: str = Field(..., description="Service identified from incident reports")
    error_types: List[str] = Field(default_factory=list, description="Classified error patterns and exceptions")
    infrastructure_components: List[str] = Field(
        default_factory=list,
        description="Subsystems involved, e.g. ['database', 'connection_pool', 'redis']",
    )
    suspected_categories: List[str] = Field(
        default_factory=list,
        description="Candidate incident types based on observed symptoms",
    )
    deployment_correlated: bool = Field(
        default=False,
        description="Indicates whether recent deployments, migrations, or rollouts are correlated",
    )
    extracted_keywords: List[str] = Field(
        default_factory=list,
        description="Salient technical terms extracted from logs and descriptions",
    )


class HistoricalIncidentMatch(BaseModel):
    """A relevant historical incident retrieved from Hindsight memory."""
    incident_id: str = Field(..., description="Historical incident identifier")
    title: str = Field(..., description="Title of the previous incident")
    service: str = Field(..., description="Service affected in the previous incident")
    similarity_score: Optional[float] = Field(default=None, description="Memory retrieval score if available")
    summary: str = Field(..., description="Summary of root cause, symptoms, or resolution")
    tags: List[str] = Field(default_factory=list, description="Tags associated with historical memory unit")


class HistoricalContext(BaseModel):
    """Historical incident context retrieved and synthesized via Hindsight."""
    available: bool = Field(..., description="True if Hindsight memory was reachable and queried")
    query_used: str = Field(..., description="Exact search query dispatched to Hindsight RECALL")
    recalled_incidents: List[HistoricalIncidentMatch] = Field(
        default_factory=list,
        description="List of relevant previous incidents retrieved from Hindsight",
    )
    reflection_summary: Optional[str] = Field(
        default=None,
        description="High-level synthesized reasoning from Hindsight REFLECT (if available)",
    )
    status_message: str = Field(..., description="Human-readable status of the memory lookup")


class Hypothesis(BaseModel):
    """A plausible root-cause hypothesis with supporting and contradicting evidence."""
    hypothesis: str = Field(..., description="Technical hypothesis for the outage")
    supporting_evidence: List[str] = Field(..., description="Current logs, errors, or metric signals supporting this")
    contradicting_evidence: List[str] = Field(
        default_factory=list,
        description="Signals that may dispute or weaken this hypothesis",
    )
    related_historical_incidents: List[str] = Field(
        default_factory=list,
        description="Historical incident IDs showing precedent for this hypothesis",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence estimate between 0.0 (unlikely) and 1.0 (highly probable)",
    )


class InvestigationStep(BaseModel):
    """Concrete, non-destructive step recommended for an on-call engineer to verify cause."""
    step_number: int = Field(..., description="Execution sequence")
    action: str = Field(..., description="Specific command, metric check, or log search to perform")
    rationale: str = Field(..., description="What this step aims to prove or disprove")
    target_system: str = Field(..., description="Target component (e.g. 'PostgreSQL', 'Kubernetes pod', 'Datadog')")


class RemediationPlan(BaseModel):
    """Recommended remediation plan clearly distinguishing immediate mitigation from permanent fixes."""
    immediate_mitigation: List[str] = Field(
        ...,
        description="Rapid actions to halt customer impact (e.g. rollback, scale pool, toggle feature flag)",
    )
    long_term_fix: List[str] = Field(
        ...,
        description="Permanent architectural or code fixes to prevent recurrence",
    )


class InvestigationResult(BaseModel):
    """Complete, structured output produced by the Incident Response Agent."""
    incident_id: str = Field(..., description="Target incident identifier")
    summary: str = Field(..., description="High-level executive summary of current situation and findings")
    observed_signals: ObservedSignals = Field(..., description="Extracted technical signals from current evidence")
    historical_context: HistoricalContext = Field(..., description="Hindsight memory recall and reflection results")
    hypotheses: List[Hypothesis] = Field(..., description="Ranked potential root causes")
    investigation_steps: List[InvestigationStep] = Field(..., description="Concrete non-destructive diagnostic steps")
    remediation_recommendations: RemediationPlan = Field(..., description="Mitigation and permanent resolution guidance")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall investigation confidence score")
    limitations: List[str] = Field(
        default_factory=list,
        description="Caveats, missing evidence, or assumptions made during analysis",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the investigation was completed",
    )

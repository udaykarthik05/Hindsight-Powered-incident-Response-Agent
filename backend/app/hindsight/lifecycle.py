from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agent.analysis import DeterministicAnalyzer
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.hindsight.memory import (
    HindsightError,
    HindsightMemoryService,
    MemoryRetainInput,
    get_memory_service,
)
from app.schemas.incident import Incident, IncidentStatus

logger = get_logger("hindsight.lifecycle")


class RetentionStatus(str, Enum):
    """Status classification for Hindsight memory retention."""
    RETAINED = "retained"
    RETENTION_FAILED = "retention_failed"
    ALREADY_RETAINED = "already_retained"
    NOT_ATTEMPTED = "not_attempted"


class MemoryRetentionResult(BaseModel):
    """Structured report returned after attempting to retain an incident into Hindsight."""
    status: RetentionStatus
    incident_id: str
    bank_id: str
    retained_at: Optional[datetime] = None
    message: str
    error: Optional[str] = None
    memory_units_count: Optional[int] = None


class IncidentMemoryBuilder:
    """
    Constructs rich, structured postmortem memory records from resolved incidents.
    
    Adheres to the structured knowledge schema:
    1. What happened (Incident timeline, scope, impact)
    2. What was observed (Error signatures, logs, deterministic signals)
    3. What was confirmed (Root cause analysis)
    4. What fixed it (Applied mitigations and remediation)
    5. What should be remembered (Key organizational takeaways)
    """

    @classmethod
    def build(cls, incident: Incident) -> MemoryRetainInput:
        """Transform a resolved incident into a MemoryRetainInput suitable for Hindsight."""
        # Extract deterministic signals from logs and text
        signals, _ = DeterministicAnalyzer.analyze(incident)

        occurred_str = incident.timestamp.isoformat() if incident.timestamp else "Unknown"
        resolved_str = incident.resolved_at.isoformat() if incident.resolved_at else datetime.now(timezone.utc).isoformat()
        root_cause = incident.root_cause or "No confirmed root cause provided."
        mitigation = incident.mitigation or "No mitigation steps documented."

        # 1. Format logs (sample up to 8 representative lines)
        log_sample = incident.logs[:8] if incident.logs else ["No raw logs recorded."]
        logs_text = "\n".join(f"  - {line}" for line in log_sample)

        # 2. Format error messages
        errors_text = "\n".join(f"  - {err}" for err in incident.error_messages) if incident.error_messages else "  - None explicitly classified."

        # 3. Format observed signals
        components_str = ", ".join(signals.infrastructure_components) or "None isolated"
        categories_str = ", ".join(signals.suspected_categories) or "General Outage"
        deploy_str = "YES (correlated with recent release or migration)" if signals.deployment_correlated else "NO"

        # 4. Formulate takeaways
        takeaway = (
            f"When encountering future incidents in {incident.affected_service} with similar "
            f"symptoms ({categories_str}; components: {components_str}), verify whether "
            f"the root cause aligns with '{root_cause[:120]}...'. "
            f"Previously successful mitigation: '{mitigation[:120]}...'."
        )

        content = (
            f"POSTMORTEM RECORD: {incident.incident_id} — {incident.title}\n"
            f"Service: {incident.affected_service} | Severity: {incident.severity.value.upper()}\n"
            f"Timeline: Occurred at {occurred_str} | Resolved at {resolved_str}\n\n"
            f"1. WHAT HAPPENED (SYMPTOMS & IMPACT):\n"
            f"{incident.description}\n\n"
            f"2. WHAT WAS OBSERVED (TELEMETRY SIGNALS & LOGS):\n"
            f"- Suspected Categories: {categories_str}\n"
            f"- Subsystems Involved: {components_str}\n"
            f"- Deployment Correlation: {deploy_str}\n"
            f"- Classified Error Signatures:\n{errors_text}\n"
            f"- Key Log Traces:\n{logs_text}\n\n"
            f"3. WHAT WAS CONFIRMED (CONFIRMED ROOT CAUSE):\n"
            f"{root_cause}\n\n"
            f"4. WHAT FIXED IT (APPLIED MITIGATION & REMEDIATION):\n"
            f"{mitigation}\n\n"
            f"5. WHAT SHOULD BE REMEMBERED (LESSONS & INVESTIGATION GUIDANCE):\n"
            f"{takeaway}"
        )

        # Build clean search metadata
        metadata: Dict[str, str] = {
            "incident_id": incident.incident_id,
            "title": incident.title[:100],
            "service": incident.affected_service,
            "severity": incident.severity.value,
            "category": signals.suspected_categories[0] if signals.suspected_categories else "Outage",
            "status": "resolved",
            "resolved_at": resolved_str,
        }

        # Build indexed tags for multi-dimensional recall
        tags: List[str] = [
            incident.affected_service.lower(),
            f"sev-{incident.severity.value.lower()}",
            "postmortem",
            "resolved",
        ]
        for comp in signals.infrastructure_components:
            tags.append(comp.lower().replace(" ", "-"))
        for err_type in signals.error_types:
            tags.append(err_type.lower().replace(" ", "-"))
        for cat in signals.suspected_categories:
            tags.append(cat.lower().replace(" ", "-"))

        # Deduplicate tags preserving order
        unique_tags = list(dict.fromkeys(tags))

        return MemoryRetainInput(
            content=content,
            context=f"Postmortem Incident Report {incident.incident_id}",
            metadata=metadata,
            tags=unique_tags,
        )


class HindsightMemoryLifecycle:
    """
    Orchestrates the Hindsight long-term organizational memory lifecycle:
    - Retaining postmortems upon incident resolution
    - Idempotency guarding against duplicate memory injection
    - Non-destructive graceful error handling when Hindsight is offline.
    """

    def __init__(
        self,
        memory_service: Optional[HindsightMemoryService] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.memory_service = memory_service or get_memory_service()

    async def retain_resolved_incident(
        self,
        incident: Incident,
        force: bool = False,
    ) -> MemoryRetentionResult:
        """
        Retain a resolved incident into Hindsight organizational memory.
        
        Guarantees:
        1. Only resolved incidents with root cause and mitigation are retained.
        2. Idempotent: Does not create duplicate memories if already retained (unless force=True).
        3. Never raises an unhandled exception: Hindsight connection failures or timeouts
           are returned as RetentionStatus.RETENTION_FAILED without corrupting incident resolution.
        """
        bank_id = self.settings.hindsight_bank_id

        # 1. Validation check
        if incident.status != IncidentStatus.RESOLVED:
            logger.info("Skipping retention for incident %s: status is '%s', not 'resolved'", incident.incident_id, incident.status)
            return MemoryRetentionResult(
                status=RetentionStatus.NOT_ATTEMPTED,
                incident_id=incident.incident_id,
                bank_id=bank_id,
                message=f"Incident {incident.incident_id} is '{incident.status.value}', not resolved.",
            )

        if not incident.root_cause or not incident.mitigation:
            logger.warning("Skipping retention for incident %s: missing root cause or mitigation", incident.incident_id)
            return MemoryRetentionResult(
                status=RetentionStatus.NOT_ATTEMPTED,
                incident_id=incident.incident_id,
                bank_id=bank_id,
                message="Cannot retain incident without confirmed root cause and mitigation.",
            )

        # 2. Idempotency check
        if not force and getattr(incident, "memory_status", None) == RetentionStatus.RETAINED.value:
            logger.info(
                "Incident %s is already marked as retained in Hindsight. Skipping duplicate retention.",
                incident.incident_id,
            )
            return MemoryRetentionResult(
                status=RetentionStatus.ALREADY_RETAINED,
                incident_id=incident.incident_id,
                bank_id=bank_id,
                retained_at=incident.resolved_at or datetime.now(timezone.utc),
                message=f"Incident {incident.incident_id} was previously retained in Hindsight memory.",
            )

        # 3. Construct structured memory payload
        try:
            retain_input = IncidentMemoryBuilder.build(incident)
            retain_input.bank_id = bank_id
        except Exception as build_err:
            logger.error("Failed to build memory record for %s: %s", incident.incident_id, build_err, exc_info=True)
            return MemoryRetentionResult(
                status=RetentionStatus.RETENTION_FAILED,
                incident_id=incident.incident_id,
                bank_id=bank_id,
                message="Failed to format incident into memory record.",
                error=str(build_err),
            )

        # 4. Ingest into Hindsight
        logger.info("Executing Hindsight RETAIN for resolved incident %s...", incident.incident_id)
        try:
            response = await self.memory_service.retain(retain_input)
            now = datetime.now(timezone.utc)
            units_count = getattr(response, "units_retained", None) or (len(response.results) if hasattr(response, "results") and response.results else 1)

            logger.info(
                "Successfully retained incident %s in Hindsight bank '%s'",
                incident.incident_id,
                bank_id,
            )
            return MemoryRetentionResult(
                status=RetentionStatus.RETAINED,
                incident_id=incident.incident_id,
                bank_id=bank_id,
                retained_at=now,
                memory_units_count=units_count,
                message=f"Incident {incident.incident_id} successfully retained in Hindsight organizational memory.",
            )
        except (HindsightError, Exception) as retain_err:
            err_msg = f"{type(retain_err).__name__}: {str(retain_err)}"
            logger.warning(
                "Hindsight RETAIN failed for incident %s (%s). Incident resolution remains intact.",
                incident.incident_id,
                err_msg,
            )
            return MemoryRetentionResult(
                status=RetentionStatus.RETENTION_FAILED,
                incident_id=incident.incident_id,
                bank_id=bank_id,
                message=(
                    "Historical memory retention failed: Hindsight service is currently offline or unreachable. "
                    "Incident resolution was recorded successfully."
                ),
                error=err_msg,
            )


# Global singleton instance
_memory_lifecycle: Optional[HindsightMemoryLifecycle] = None


def get_memory_lifecycle() -> HindsightMemoryLifecycle:
    """Dependency provider for HindsightMemoryLifecycle."""
    global _memory_lifecycle
    if _memory_lifecycle is None:
        _memory_lifecycle = HindsightMemoryLifecycle()
    return _memory_lifecycle

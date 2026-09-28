from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Incident severity classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident lifecycle status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class IncidentBase(BaseModel):
    """Base incident properties shared across requests and responses."""
    title: str = Field(..., min_length=3, max_length=200, description="Short summary of the incident")
    description: str = Field(..., min_length=5, description="Detailed description of symptoms and impact")
    severity: Severity = Field(default=Severity.MEDIUM, description="Incident severity level")
    affected_service: str = Field(..., min_length=2, max_length=100, description="Service or component affected")
    logs: List[str] = Field(default_factory=list, description="Raw log entries observed during the incident")
    error_messages: List[str] = Field(default_factory=list, description="Extracted error messages or exceptions")


class IncidentCreate(IncidentBase):
    """Request schema for reporting or creating a new incident."""
    incident_id: Optional[str] = Field(
        default=None,
        description="Optional custom ID (e.g., 'INC-2025-101'). Generated automatically if omitted.",
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Time the incident occurred. Defaults to current UTC time.",
    )
    status: IncidentStatus = Field(
        default=IncidentStatus.OPEN,
        description="Initial incident status",
    )
    root_cause: Optional[str] = Field(default=None, description="Known root cause if already diagnosed")
    mitigation: Optional[str] = Field(default=None, description="Immediate mitigation or workaround")


class IncidentUpdate(BaseModel):
    """Request schema for updating an existing incident's properties."""
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=5)
    severity: Optional[Severity] = None
    affected_service: Optional[str] = Field(default=None, min_length=2, max_length=100)
    status: Optional[IncidentStatus] = None
    logs: Optional[List[str]] = None
    error_messages: Optional[List[str]] = None
    root_cause: Optional[str] = None
    mitigation: Optional[str] = None


class IncidentResolve(BaseModel):
    """Request schema for marking an incident as resolved with findings."""
    root_cause: str = Field(..., min_length=5, description="Confirmed root cause analysis")
    mitigation: str = Field(..., min_length=5, description="Remediation steps applied to resolve the outage")
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="Time of resolution. Defaults to current UTC time.",
    )


class Incident(IncidentBase):
    """Full domain and response model representing an incident."""
    incident_id: str = Field(..., description="Unique incident identifier, e.g., 'INC-2026-001'")
    timestamp: datetime = Field(..., description="Timestamp when the incident occurred")
    status: IncidentStatus = Field(default=IncidentStatus.OPEN, description="Current lifecycle state")
    root_cause: Optional[str] = Field(default=None, description="Confirmed root cause analysis")
    mitigation: Optional[str] = Field(default=None, description="Applied mitigation or remediation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Record creation time")
    resolved_at: Optional[datetime] = Field(default=None, description="Record resolution time")

    @classmethod
    def create_from_input(cls, input_data: IncidentCreate) -> "Incident":
        """Factory method to instantiate a domain Incident from an IncidentCreate payload."""
        now = datetime.now(timezone.utc)
        generated_id = input_data.incident_id or f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        return cls(
            incident_id=generated_id,
            title=input_data.title,
            description=input_data.description,
            severity=input_data.severity,
            affected_service=input_data.affected_service,
            timestamp=input_data.timestamp or now,
            logs=list(input_data.logs),
            error_messages=list(input_data.error_messages),
            status=input_data.status,
            root_cause=input_data.root_cause,
            mitigation=input_data.mitigation,
            created_at=now,
            resolved_at=now if input_data.status == IncidentStatus.RESOLVED else None,
        )


class IncidentListResponse(BaseModel):
    """Response envelope for listing incidents."""
    total: int
    items: List[Incident]

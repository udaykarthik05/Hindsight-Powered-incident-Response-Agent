from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentResolve,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)


def test_incident_create_valid() -> None:
    """Test valid incident creation schema."""
    payload = IncidentCreate(
        title="High CPU in billing worker",
        description="Billing worker CPU utilization hit 98% following batch invoice job.",
        severity=Severity.HIGH,
        affected_service="billing-worker",
        logs=["2026-01-01 10:00:00 WARN High CPU"],
        error_messages=["CPU threshold exceeded"],
    )
    assert payload.title == "High CPU in billing worker"
    assert payload.severity == Severity.HIGH
    assert payload.status == IncidentStatus.OPEN
    assert len(payload.logs) == 1


def test_incident_domain_factory() -> None:
    """Test factory method creating domain Incident from IncidentCreate."""
    payload = IncidentCreate(
        title="Database deadlock",
        description="Deadlock detected in order fulfillment transaction.",
        severity=Severity.CRITICAL,
        affected_service="order-service",
    )
    incident = Incident.create_from_input(payload)
    assert incident.incident_id.startswith("INC-")
    assert incident.title == payload.title
    assert incident.status == IncidentStatus.OPEN
    assert incident.created_at is not None
    assert incident.resolved_at is None


def test_incident_invalid_severity() -> None:
    """Test validation rejection for invalid severity string."""
    with pytest.raises(ValidationError):
        IncidentCreate(
            title="Invalid Severity",
            description="Testing invalid enum value.",
            severity="extreme",  # type: ignore
            affected_service="test",
        )


def test_incident_short_title_rejected() -> None:
    """Test title length constraint validation."""
    with pytest.raises(ValidationError):
        IncidentCreate(
            title="No",  # min_length is 3
            description="Short title test description.",
            affected_service="test-service",
        )


def test_incident_resolve_schema() -> None:
    """Test IncidentResolve requires root_cause and mitigation."""
    resolve_data = IncidentResolve(
        root_cause="Unindexed foreign key caused table scan.",
        mitigation="Added index on orders(customer_id).",
    )
    assert resolve_data.root_cause.startswith("Unindexed")
    assert resolve_data.mitigation.startswith("Added")

    with pytest.raises(ValidationError):
        IncidentResolve(root_cause="", mitigation="Short")  # min_length is 5

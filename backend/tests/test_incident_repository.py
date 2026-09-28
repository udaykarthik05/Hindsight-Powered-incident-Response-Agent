from datetime import datetime, timezone
import pytest

from app.repositories.incident_repository import InMemoryIncidentRepository
from app.schemas.incident import (
    Incident,
    IncidentCreate,
    IncidentResolve,
    IncidentStatus,
    IncidentUpdate,
    Severity,
)


@pytest.fixture
def repo() -> InMemoryIncidentRepository:
    """Fixture providing clean in-memory repository instance."""
    return InMemoryIncidentRepository()


def test_repo_create_and_get(repo: InMemoryIncidentRepository) -> None:
    """Test creating an incident and retrieving it by ID."""
    create_payload = IncidentCreate(
        incident_id="INC-TEST-001",
        title="Test Incident Title",
        description="Detailed test description of the problem.",
        severity=Severity.HIGH,
        affected_service="payment-service",
        logs=["log line 1", "log line 2"],
        error_messages=["Error: connection refused"],
    )
    incident = repo.create(create_payload)
    assert incident.incident_id == "INC-TEST-001"
    assert incident.affected_service == "payment-service"

    fetched = repo.get("INC-TEST-001")
    assert fetched is not None
    assert fetched.incident_id == "INC-TEST-001"
    assert fetched.title == "Test Incident Title"


def test_repo_get_nonexistent_returns_none(repo: InMemoryIncidentRepository) -> None:
    """Test retrieving nonexistent ID returns None."""
    assert repo.get("NONEXISTENT-ID") is None


def test_repo_list_and_filter(repo: InMemoryIncidentRepository) -> None:
    """Test listing incidents with various filters."""
    repo.create(
        IncidentCreate(
            incident_id="INC-1",
            title="Database error",
            description="DB timeout in auth",
            severity=Severity.CRITICAL,
            affected_service="auth-service",
            status=IncidentStatus.OPEN,
        )
    )
    repo.create(
        IncidentCreate(
            incident_id="INC-2",
            title="Redis error",
            description="Redis cluster latency",
            severity=Severity.HIGH,
            affected_service="cache-service",
            status=IncidentStatus.INVESTIGATING,
        )
    )
    repo.create(
        IncidentCreate(
            incident_id="INC-3",
            title="Auth worker crash",
            description="Worker restarted",
            severity=Severity.LOW,
            affected_service="auth-service",
            status=IncidentStatus.RESOLVED,
        )
    )

    assert repo.count() == 3

    # Filter by service
    auth_incidents = repo.list(service="auth-service")
    assert len(auth_incidents) == 2

    # Filter by status
    open_incidents = repo.list(status=IncidentStatus.OPEN)
    assert len(open_incidents) == 1
    assert open_incidents[0].incident_id == "INC-1"

    # Filter by severity
    critical_incidents = repo.list(severity=Severity.CRITICAL)
    assert len(critical_incidents) == 1
    assert critical_incidents[0].incident_id == "INC-1"


def test_repo_update(repo: InMemoryIncidentRepository) -> None:
    """Test partial update of incident fields."""
    incident = repo.create(
        IncidentCreate(
            incident_id="INC-UPDATE-1",
            title="Initial Title",
            description="Initial Description",
            severity=Severity.LOW,
            affected_service="gateway",
        )
    )

    updated = repo.update(
        "INC-UPDATE-1",
        IncidentUpdate(
            title="Escalated Title",
            severity=Severity.CRITICAL,
            status=IncidentStatus.INVESTIGATING,
        ),
    )
    assert updated is not None
    assert updated.title == "Escalated Title"
    assert updated.severity == Severity.CRITICAL
    assert updated.status == IncidentStatus.INVESTIGATING
    assert updated.description == "Initial Description"  # preserved


def test_repo_resolve(repo: InMemoryIncidentRepository) -> None:
    """Test resolving an incident."""
    incident = repo.create(
        IncidentCreate(
            incident_id="INC-RESOLVE-1",
            title="Outage to resolve",
            description="Description before resolution",
            severity=Severity.HIGH,
            affected_service="payment-service",
        )
    )
    assert incident.status == IncidentStatus.OPEN
    assert incident.resolved_at is None

    resolved = repo.resolve(
        "INC-RESOLVE-1",
        IncidentResolve(
            root_cause="Stripe webhook endpoint was responding with 500.",
            mitigation="Updated endpoint handler to acknowledge asynchronous events.",
        ),
    )
    assert resolved is not None
    assert resolved.status == IncidentStatus.RESOLVED
    assert resolved.root_cause.startswith("Stripe webhook")
    assert resolved.mitigation.startswith("Updated endpoint")
    assert resolved.resolved_at is not None


def test_repo_delete(repo: InMemoryIncidentRepository) -> None:
    """Test deleting an incident."""
    repo.create(
        IncidentCreate(
            incident_id="INC-DELETE-1",
            title="To be deleted",
            description="Description for deletion test",
            affected_service="test",
        )
    )
    assert repo.delete("INC-DELETE-1") is True
    assert repo.get("INC-DELETE-1") is None
    assert repo.delete("INC-DELETE-1") is False

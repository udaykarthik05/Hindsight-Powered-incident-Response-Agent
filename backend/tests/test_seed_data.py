from app.data.seed_incidents import get_seed_data, get_seed_incidents
from app.schemas.incident import Incident, IncidentStatus


def test_seed_incidents_count() -> None:
    """Ensure seed dataset has between 8 and 12 distinct incidents (Phase 2 requirement)."""
    data = get_seed_data()
    assert 8 <= len(data) <= 12
    assert len(data) == 10


def test_seed_incidents_unique_ids() -> None:
    """Ensure all seed incidents have distinct, unique identifiers."""
    data = get_seed_data()
    ids = [item.incident.incident_id for item in data]
    assert len(ids) == len(set(ids)), "Duplicate incident_id detected in seed dataset"


def test_seed_incidents_structure_and_completeness() -> None:
    """Verify each seed incident is fully populated with realistic details."""
    incidents = get_seed_incidents()
    for inc in incidents:
        assert isinstance(inc, Incident)
        assert len(inc.title) >= 10, f"Title too brief for {inc.incident_id}"
        assert len(inc.description) >= 20, f"Description too brief for {inc.incident_id}"
        assert inc.affected_service != "", f"Service empty for {inc.incident_id}"
        assert len(inc.logs) >= 2, f"Expected realistic logs for {inc.incident_id}"
        assert len(inc.error_messages) >= 1, f"Expected error messages for {inc.incident_id}"
        assert inc.root_cause is not None and len(inc.root_cause) >= 20, f"Missing root cause for {inc.incident_id}"
        assert inc.mitigation is not None and len(inc.mitigation) >= 20, f"Missing mitigation for {inc.incident_id}"
        assert inc.status == IncidentStatus.RESOLVED
        assert inc.resolved_at is not None


def test_seed_hindsight_formatting() -> None:
    """Verify that seed payloads convert cleanly to Hindsight memory format."""
    data = get_seed_data()
    for payload in data:
        formatted = payload.to_hindsight_format()
        assert "content" in formatted
        assert "metadata" in formatted
        assert "tags" in formatted
        assert "context" in formatted

        # Check content contains all key sections
        content = formatted["content"]
        assert payload.incident.incident_id in content
        assert "SYMPTOMS & IMPACT" in content
        assert "ROOT CAUSE" in content
        assert "MITIGATION" in content

        # Check metadata
        meta = formatted["metadata"]
        assert meta["incident_id"] == payload.incident.incident_id
        assert meta["service"] == payload.incident.affected_service
        assert meta["category"] == payload.category
        assert meta["severity"] == payload.incident.severity.value

        # Check tags
        assert len(formatted["tags"]) >= 3

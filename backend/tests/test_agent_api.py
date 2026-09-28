from starlette.testclient import TestClient


def test_investigate_api_success(client: TestClient) -> None:
    """Test POST /api/v1/incidents/{id}/investigate on seed incident returns 200 and InvestigationResult."""
    response = client.post("/api/v1/incidents/INC-2025-101/investigate")
    assert response.status_code == 200

    data = response.json()
    assert data["incident_id"] == "INC-2025-101"
    assert "summary" in data
    assert "observed_signals" in data
    assert "historical_context" in data
    assert "hypotheses" in data
    assert len(data["hypotheses"]) > 0
    assert "investigation_steps" in data
    assert len(data["investigation_steps"]) > 0
    assert "remediation_recommendations" in data
    assert "immediate_mitigation" in data["remediation_recommendations"]
    assert "long_term_fix" in data["remediation_recommendations"]
    assert 0.0 <= data["confidence"] <= 1.0


def test_investigate_api_not_found(client: TestClient) -> None:
    """Test POST /api/v1/incidents/{id}/investigate returns 404 for nonexistent incident."""
    response = client.post("/api/v1/incidents/INC-NONEXISTENT-999/investigate")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_investigate_api_newly_created_incident(client: TestClient) -> None:
    """Test end-to-end flow: create incident then trigger investigation."""
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Auth Service Redis Cache Connection Timeout",
            "description": "Session lookups failing due to Redis cluster unreachable.",
            "severity": "high",
            "affected_service": "auth-service",
            "logs": ["ERROR: redis.exceptions.ConnectionError: Connection refused to redis:6379"],
            "error_messages": ["Connection refused to redis:6379"],
        },
    )
    assert create_res.status_code == 201
    incident_id = create_res.json()["incident_id"]

    investigate_res = client.post(f"/api/v1/incidents/{incident_id}/investigate")
    assert investigate_res.status_code == 200

    data = investigate_res.json()
    assert data["incident_id"] == incident_id
    assert "redis" in str(data["observed_signals"]).lower()

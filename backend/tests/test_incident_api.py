from starlette.testclient import TestClient


def test_create_incident_api_success(client: TestClient) -> None:
    """Test POST /api/v1/incidents creates a new incident with 201 status."""
    payload = {
        "title": "API Gateway 502 Bad Gateway Spike",
        "description": "Upstream instances unhealthy due to connection timeout.",
        "severity": "critical",
        "affected_service": "api-gateway",
        "logs": ["2026-02-01 12:00:00 [error] 502 Bad Gateway"],
        "error_messages": ["502 Bad Gateway"],
    }
    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["incident_id"].startswith("INC-")
    assert data["title"] == payload["title"]
    assert data["severity"] == "critical"
    assert data["status"] == "open"
    assert len(data["logs"]) == 1


def test_create_incident_api_validation_error(client: TestClient) -> None:
    """Test POST /api/v1/incidents with missing required fields returns 422."""
    payload = {
        "title": "Missing service and description",
    }
    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 422


def test_get_incidents_list(client: TestClient) -> None:
    """Test GET /api/v1/incidents returns list of incidents."""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Seed incidents loaded on startup


def test_get_incidents_with_filters(client: TestClient) -> None:
    """Test GET /api/v1/incidents filtering by service and status."""
    # Filter by service
    response = client.get("/api/v1/incidents?service=auth-service")
    assert response.status_code == 200
    data = response.json()
    assert all(inc["affected_service"] == "auth-service" for inc in data)

    # Filter by severity
    response = client.get("/api/v1/incidents?severity=critical")
    assert response.status_code == 200
    data = response.json()
    assert all(inc["severity"] == "critical" for inc in data)


def test_get_incident_by_id_found(client: TestClient) -> None:
    """Test GET /api/v1/incidents/{id} returns 200 for seed incident."""
    response = client.get("/api/v1/incidents/INC-2025-101")
    assert response.status_code == 200

    data = response.json()
    assert data["incident_id"] == "INC-2025-101"
    assert "Auth Service" in data["title"]
    assert data["severity"] == "critical"


def test_get_incident_by_id_not_found(client: TestClient) -> None:
    """Test GET /api/v1/incidents/{id} returns 404 for unknown ID."""
    response = client.get("/api/v1/incidents/INC-999-DOESNOTEXIST")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_update_incident_api(client: TestClient) -> None:
    """Test PATCH /api/v1/incidents/{id} updates fields successfully."""
    # Create an incident to update
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Incident to update",
            "description": "Original description for update test.",
            "severity": "low",
            "affected_service": "test-service",
        },
    )
    incident_id = create_res.json()["incident_id"]

    # Patch incident
    patch_res = client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={
            "title": "Updated Title via PATCH",
            "severity": "high",
        },
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["title"] == "Updated Title via PATCH"
    assert patched_data["severity"] == "high"
    assert patched_data["affected_service"] == "test-service"


def test_update_nonexistent_incident_returns_404(client: TestClient) -> None:
    """Test PATCH /api/v1/incidents/{id} returns 404 for missing ID."""
    response = client.patch(
        "/api/v1/incidents/INC-MISSING-404",
        json={"title": "New Title"},
    )
    assert response.status_code == 404


def test_resolve_incident_api(client: TestClient) -> None:
    """Test POST /api/v1/incidents/{id}/resolve transitions incident to resolved."""
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "title": "Incident to resolve",
            "description": "Original description before resolution.",
            "severity": "medium",
            "affected_service": "test-service",
        },
    )
    incident_id = create_res.json()["incident_id"]

    resolve_payload = {
        "root_cause": "Race condition in cache invalidation worker.",
        "mitigation": "Added distributed Redis mutex around cache write.",
    }
    resolve_res = client.post(
        f"/api/v1/incidents/{incident_id}/resolve",
        json=resolve_payload,
    )
    assert resolve_res.status_code == 200

    data = resolve_res.json()
    assert data["status"] == "resolved"
    assert data["root_cause"] == resolve_payload["root_cause"]
    assert data["mitigation"] == resolve_payload["mitigation"]
    assert data["resolved_at"] is not None


def test_resolve_nonexistent_incident_returns_404(client: TestClient) -> None:
    """Test POST /api/v1/incidents/{id}/resolve returns 404 for unknown ID."""
    response = client.post(
        "/api/v1/incidents/INC-NOT-HERE/resolve",
        json={
            "root_cause": "Any root cause",
            "mitigation": "Any mitigation",
        },
    )
    assert response.status_code == 404

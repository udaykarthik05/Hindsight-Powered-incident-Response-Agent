from starlette.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test GET /health returns 200 OK and expected structure."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "environment" in data
    assert "timestamp" in data


def test_root_endpoint(client: TestClient) -> None:
    """Test GET / returns root metadata and endpoints dictionary."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "endpoints" in data
    assert data["endpoints"]["health"] == "/health"
    assert data["endpoints"]["docs"] == "/docs"
    assert data["endpoints"]["hindsight_status"] == "/api/v1/hindsight/status"

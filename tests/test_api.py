from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health_endpoint_is_lightweight():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "local"}


def test_soundtrack_endpoint_validates_memory_length_before_service_startup():
    response = client.post("/api/soundtracks", json={"memory": "short"})
    assert response.status_code == 422

import pytest
from fastapi.testclient import TestClient
from control_service.main import app

@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as client:
        yield client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
    "service": "laser-control-service",
    "status": "ok"
}

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from control_service.api.routes.health import router as health_router
from fastapi.testclient import TestClient
from control_service.api.dependencies import get_laser_driver


class FakeLaserDriver:
    def __init__(self, is_connected: bool) -> None:
        self.is_connected = is_connected

@pytest.fixture
def api_app() -> FastAPI:
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.fixture
def client(api_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(api_app) as client:
        yield client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
    "service": "laser-control-service",
    "status": "ok"
}

def test_ready_returns_200_when_driver_is_connected(
    client: TestClient,
    api_app: FastAPI,
) -> None:
    fake_driver = FakeLaserDriver(is_connected=True)
    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {
        "service": "laser-control-service",
        "status": "ok",
        "device_connected": True,
    }


def test_ready_returns_503_when_driver_is_not_connected(
    client: TestClient,
    api_app: FastAPI,
) -> None:
    fake_driver = FakeLaserDriver(is_connected=False)
    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Could not connect to laser driver",
    }

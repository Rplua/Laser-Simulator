from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from control_service.api.routes.health import router as health_router
from control_service.api.routes.laser import router as laser_router
from fastapi.testclient import TestClient




@pytest.fixture
def api_app() -> FastAPI:
    app = FastAPI()
    app.include_router(health_router)
    app.include_router(laser_router)
    return app


@pytest.fixture
def client(api_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(api_app) as client:
        yield client

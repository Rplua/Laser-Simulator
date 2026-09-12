from fastapi import FastAPI
from contextlib import asynccontextmanager
from control_service.api.routes.health import router as health_router
from device_driver.laser_driver import LaserDriver



@asynccontextmanager
async def lifespan(app: FastAPI):
    laser_driver: LaserDriver = LaserDriver(
        host="127.0.0.1",
        port=9000,
        connect_timeout_seconds=3.0,
        response_timeout_seconds=3.0
    )

    app.state.laser_driver = laser_driver
    try:
        await app.state.laser_driver.connect()
        yield
    finally:
        await laser_driver.disconnect()


app = FastAPI(title="Laser Control Service", lifespan=lifespan)

app.include_router(health_router, )
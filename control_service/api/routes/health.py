from fastapi import APIRouter, HTTPException, Depends

from control_service.api.dependencies import get_laser_driver
from device_driver.laser_driver import LaserDriver

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "service": "laser-control-service",
        "status": "ok",
    }

@router.get("/ready")
def ready(driver: LaserDriver = Depends(get_laser_driver)) -> dict[str, object]:
    if not driver.is_connected:
        raise HTTPException(status_code=503, detail="Could not connect to laser driver")


    return {
            "service": "laser-control-service",
            "status": "ok",
            "device_connected": True,
    }
from fastapi import APIRouter, Depends

from control_service.api.dependencies import get_laser_driver
from control_service.mappers.laser_snapshot import (
    map_laser_snapshot_to_response,
)
from control_service.schemas.responses import LaserSnapshotResponse
from device_driver.laser_driver import LaserDriver
from simulated_device.laser.model.laser_snapshot import LaserSnapshot

router = APIRouter(
    prefix="/laser",
    tags=["laser"],
)


@router.get(
    "/snapshot",
    response_model=LaserSnapshotResponse,
)
async def get_laser_snapshot(
    driver: LaserDriver = Depends(get_laser_driver),
) -> LaserSnapshotResponse:
    snapshot: LaserSnapshot = await driver.get_snapshot()
    return map_laser_snapshot_to_response(snapshot)

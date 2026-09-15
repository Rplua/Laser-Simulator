from fastapi import APIRouter, Depends

from control_service.api.dependencies import get_laser_driver
from control_service.mappers.laser_snapshot import (
    map_laser_snapshot_to_response,
)
from control_service.schemas.requests import SetTargetPowerRequest
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


@router.put(
    "/target-power",
    response_model=LaserSnapshotResponse,
)
async def set_target_power(
    command: SetTargetPowerRequest,
    driver: LaserDriver = Depends(get_laser_driver),
) -> LaserSnapshotResponse:
    laser_snapshot: LaserSnapshot = await driver.set_target_power(
        command.target_power_mw,
    )
    return map_laser_snapshot_to_response(laser_snapshot)


@router.post(
    "/commands/arm",
    response_model=LaserSnapshotResponse,
)
async def arm_laser(
    driver: LaserDriver = Depends(get_laser_driver),
) -> LaserSnapshotResponse:
    snapshot: LaserSnapshot = await driver.arm()
    return map_laser_snapshot_to_response(snapshot)


@router.post(
    "/commands/start",
    response_model=LaserSnapshotResponse)

async def start_laser(
        driver: LaserDriver = Depends(get_laser_driver),
)->LaserSnapshotResponse:
    laser_snapshot: LaserSnapshot = await driver.start()
    return map_laser_snapshot_to_response(laser_snapshot)


@router.post(
    "/commands/stop",
    response_model=LaserSnapshotResponse)

async def start_laser(
        driver: LaserDriver = Depends(get_laser_driver),
)->LaserSnapshotResponse:
    laser_snapshot: LaserSnapshot = await driver.stop()
    return map_laser_snapshot_to_response(laser_snapshot)


@router.post(
    "/commands/disarm",
    response_model=LaserSnapshotResponse)

async def start_laser(
        driver: LaserDriver = Depends(get_laser_driver),
)->LaserSnapshotResponse:
    laser_snapshot: LaserSnapshot = await driver.disarm()
    return map_laser_snapshot_to_response(laser_snapshot)


@router.post(
    "/commands/emergency-stop",
    response_model=LaserSnapshotResponse)

async def start_laser(
        driver: LaserDriver = Depends(get_laser_driver),
)->LaserSnapshotResponse:
    laser_snapshot: LaserSnapshot = await driver.emergency_stop()
    return map_laser_snapshot_to_response(laser_snapshot)

@router.post(
    "/commands/recover",
    response_model=LaserSnapshotResponse)

async def start_laser(
        driver: LaserDriver = Depends(get_laser_driver),
)->LaserSnapshotResponse:
    laser_snapshot: LaserSnapshot = await driver.recover()
    return map_laser_snapshot_to_response(laser_snapshot)
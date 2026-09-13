from control_service.schemas.responses import LaserSnapshotResponse
from simulated_device.laser.model.laser_snapshot import LaserSnapshot


def map_laser_snapshot_to_response(
    snapshot: LaserSnapshot,
) -> LaserSnapshotResponse:
    return LaserSnapshotResponse(
        state=snapshot.state.value,
        actual_power_mw=snapshot.actual_power_mw,
        target_power_mw=snapshot.target_power_mw,
        temperature_c=snapshot.temperature_c,
        current_ma=snapshot.current_ma,
        fault_reason=(
            snapshot.fault_reason.value
            if snapshot.fault_reason is not None
            else None
        ),
    )

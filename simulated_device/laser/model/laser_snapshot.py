from pydantic import BaseModel

from simulated_device.laser.enums.fault_reason import FaultReason
from simulated_device.laser.enums.laser_states import LaserState


class LaserSnapshot(BaseModel):
    state: LaserState
    actual_power_mw: float
    target_power_mw: float|None
    temperature_c: float
    current_ma: float
    fault_reason: FaultReason |None

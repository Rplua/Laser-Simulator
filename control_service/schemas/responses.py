from pydantic import BaseModel


class LaserSnapshotResponse(BaseModel):
    state: str
    actual_power_mw: float
    target_power_mw: float | None
    temperature_c: float
    current_ma: float
    fault_reason: str | None

from pydantic import BaseModel, ConfigDict


class SetTargetPowerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_power_mw: float
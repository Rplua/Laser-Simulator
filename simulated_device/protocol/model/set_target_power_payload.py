from pydantic import BaseModel, ConfigDict


class SetTargetPowerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    target_power_mw: float

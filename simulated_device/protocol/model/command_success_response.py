from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from simulated_device.laser.model.laser_snapshot import LaserSnapshot


class CommandSuccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal[1]
    message_type: Literal["response"]
    request_id: UUID
    status: Literal["ok"]
    result: LaserSnapshot
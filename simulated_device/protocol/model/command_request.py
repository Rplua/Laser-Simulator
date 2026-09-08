from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from simulated_device.protocol.enums.command_name import CommandName

class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal[1]
    message_type: Literal["command"]
    request_id: UUID
    command: CommandName
    payload: dict[str, object]

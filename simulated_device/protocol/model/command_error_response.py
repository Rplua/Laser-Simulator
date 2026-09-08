from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from simulated_device.protocol.model.error_detail import ErrorDetail


class CommandErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal[1]
    message_type: Literal["response"]
    request_id: UUID | None
    status: Literal["error"]
    error: ErrorDetail

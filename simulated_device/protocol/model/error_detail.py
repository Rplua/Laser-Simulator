from pydantic import BaseModel, ConfigDict

from simulated_device.protocol.enums.error_code import ErrorCode


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str

from pydantic import ValidationError

from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidMessageError,
)
from simulated_device.protocol.model.command_request import CommandRequest


def decode_command(payload: bytes) -> CommandRequest:
    try:
        return CommandRequest.model_validate_json(payload)
    except ValidationError as error:
        raise InvalidMessageError("Invalid command message") from error
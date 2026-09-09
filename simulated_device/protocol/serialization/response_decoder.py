from pydantic import TypeAdapter, ValidationError

from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidResponseError,
)
from simulated_device.protocol.model.command_error_response import (
    CommandErrorResponse,
)
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)


CommandResponse = CommandSuccessResponse | CommandErrorResponse

_RESPONSE_ADAPTER = TypeAdapter(CommandResponse)


def decode_response(payload: bytes) -> CommandResponse:
    try:
        return _RESPONSE_ADAPTER.validate_json(payload)
    except ValidationError as error:
        raise InvalidResponseError("Invalid command response") from error

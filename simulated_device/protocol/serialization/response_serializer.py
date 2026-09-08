from simulated_device.protocol.model.command_error_response import (
    CommandErrorResponse,
)
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)


def serialize_response(
    response: CommandSuccessResponse | CommandErrorResponse,
) -> bytes:
    return response.model_dump_json().encode("utf-8")

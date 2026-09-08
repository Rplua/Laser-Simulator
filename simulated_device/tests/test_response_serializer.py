from uuid import uuid4

from simulated_device.application.response_factory import (
    build_error_response,
    build_success_response,
)
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidRequestError,
)
from simulated_device.protocol.model.command_error_response import (
    CommandErrorResponse,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)
from simulated_device.protocol.serialization.response_serializer import (
    serialize_response,
)


def test_serialize_success_response_returns_valid_json_bytes() -> None:
    command = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.GET_SNAPSHOT,
        payload={},
    )
    response = build_success_response(command, Laser().snapshot())

    serialized = serialize_response(response)
    decoded = CommandSuccessResponse.model_validate_json(serialized)

    assert isinstance(serialized, bytes)
    assert decoded == response


def test_serialize_error_response_returns_valid_json_bytes() -> None:
    response = build_error_response(uuid4(), InvalidRequestError())

    serialized = serialize_response(response)
    decoded = CommandErrorResponse.model_validate_json(serialized)

    assert isinstance(serialized, bytes)
    assert decoded == response

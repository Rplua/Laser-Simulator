from uuid import uuid4

import pytest

from simulated_device.application.response_factory import build_success_response
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidResponseError,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)
from simulated_device.protocol.serialization.command_decoder import decode_command
from simulated_device.protocol.serialization.command_serializer import (
    serialize_command,
)
from simulated_device.protocol.serialization.response_decoder import (
    decode_response,
)
from simulated_device.protocol.serialization.response_serializer import (
    serialize_response,
)


def test_command_serialization_round_trip() -> None:
    command = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.ARM,
        payload={},
    )

    decoded = decode_command(serialize_command(command))

    assert decoded == command


def test_success_response_serialization_round_trip() -> None:
    command = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.GET_SNAPSHOT,
        payload={},
    )
    response = build_success_response(command, Laser().snapshot())

    decoded = decode_response(serialize_response(response))

    assert isinstance(decoded, CommandSuccessResponse)
    assert decoded == response


def test_response_decoder_rejects_invalid_response() -> None:
    with pytest.raises(InvalidResponseError):
        decode_response(b'{"status":"unknown"}')

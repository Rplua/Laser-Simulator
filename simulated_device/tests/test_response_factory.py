from uuid import uuid4

import pytest

from simulated_device.application.response_factory import (
    build_error_response,
    build_success_response,
)
from simulated_device.laser.exceptions.laser_exceptions import (
    InvalidStateTransitionError,
    InvalidTargetPowerError,
    TargetPowerNotConfiguredError,
    UnsafeRecoveryError,
)
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.enums.error_code import ErrorCode
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidEncodingError,
    InvalidFrameLengthError,
    InvalidJsonError,
    InvalidRequestError,
    UnsupportedCommandError,
    UnsupportedProtocolVersionError,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)


def test_build_success_response_preserves_request_id_and_snapshot() -> None:
    command_request = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.GET_SNAPSHOT,
        payload={},
    )
    laser_snapshot = Laser().snapshot()

    response = build_success_response(command_request, laser_snapshot)

    assert isinstance(response, CommandSuccessResponse)
    assert response.protocol_version == 1
    assert response.message_type == "response"
    assert response.request_id == command_request.request_id
    assert response.status == "ok"
    assert response.result == laser_snapshot


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (InvalidFrameLengthError(), ErrorCode.INVALID_FRAME_LENGTH),
        (InvalidEncodingError(), ErrorCode.INVALID_ENCODING),
        (InvalidJsonError(), ErrorCode.INVALID_JSON),
        (InvalidRequestError(), ErrorCode.INVALID_REQUEST),
        (
            UnsupportedProtocolVersionError(),
            ErrorCode.UNSUPPORTED_PROTOCOL_VERSION,
        ),
        (UnsupportedCommandError(), ErrorCode.UNSUPPORTED_COMMAND),
        (
            InvalidStateTransitionError(),
            ErrorCode.INVALID_STATE_TRANSITION,
        ),
        (
            TargetPowerNotConfiguredError(),
            ErrorCode.TARGET_POWER_NOT_CONFIGURED,
        ),
        (InvalidTargetPowerError(), ErrorCode.INVALID_TARGET_POWER),
        (UnsafeRecoveryError(), ErrorCode.UNSAFE_RECOVERY),
    ],
)
def test_build_error_response_maps_known_errors(
    error: Exception,
    expected_code: ErrorCode,
) -> None:
    request_id = uuid4()

    response = build_error_response(request_id, error)

    assert response.request_id == request_id
    assert response.status == "error"
    assert response.error.code is expected_code
    assert response.error.message


def test_build_error_response_hides_unexpected_error_details() -> None:
    response = build_error_response(
        uuid4(),
        RuntimeError("sensitive implementation details"),
    )

    assert response.error.code is ErrorCode.INTERNAL_ERROR
    assert response.error.message == "Internal server error"

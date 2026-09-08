from uuid import UUID

from simulated_device.laser.exceptions.laser_exceptions import (
    InvalidStateTransitionError,
    InvalidTargetPowerError,
    TargetPowerNotConfiguredError,
    UnsafeRecoveryError,
)
from simulated_device.laser.model.laser_snapshot import LaserSnapshot
from simulated_device.protocol.enums.error_code import ErrorCode
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidEncodingError,
    InvalidFrameLengthError,
    InvalidJsonError,
    InvalidMessageError,
    InvalidRequestError,
    UnsupportedCommandError,
    UnsupportedProtocolVersionError,
)
from simulated_device.protocol.model.command_error_response import (
    CommandErrorResponse,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)
from simulated_device.protocol.model.error_detail import ErrorDetail


_ERROR_CODES: tuple[tuple[type[Exception], ErrorCode], ...] = (
    (InvalidFrameLengthError, ErrorCode.INVALID_FRAME_LENGTH),
    (InvalidEncodingError, ErrorCode.INVALID_ENCODING),
    (InvalidJsonError, ErrorCode.INVALID_JSON),
    (UnsupportedProtocolVersionError, ErrorCode.UNSUPPORTED_PROTOCOL_VERSION),
    (UnsupportedCommandError, ErrorCode.UNSUPPORTED_COMMAND),
    (InvalidRequestError, ErrorCode.INVALID_REQUEST),
    (InvalidMessageError, ErrorCode.INVALID_REQUEST),
    (InvalidStateTransitionError, ErrorCode.INVALID_STATE_TRANSITION),
    (TargetPowerNotConfiguredError, ErrorCode.TARGET_POWER_NOT_CONFIGURED),
    (InvalidTargetPowerError, ErrorCode.INVALID_TARGET_POWER),
    (UnsafeRecoveryError, ErrorCode.UNSAFE_RECOVERY),
)

_DEFAULT_ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.INVALID_FRAME_LENGTH: "Invalid frame length",
    ErrorCode.INVALID_ENCODING: "Message payload is not valid UTF-8",
    ErrorCode.INVALID_JSON: "Message payload is not valid JSON",
    ErrorCode.INVALID_REQUEST: "Message does not satisfy the request contract",
    ErrorCode.UNSUPPORTED_PROTOCOL_VERSION: "Protocol version is not supported",
    ErrorCode.UNSUPPORTED_COMMAND: "Command is not supported",
    ErrorCode.INVALID_STATE_TRANSITION: "Invalid laser state transition",
    ErrorCode.TARGET_POWER_NOT_CONFIGURED: "Target power is not configured",
    ErrorCode.INVALID_TARGET_POWER: "Target power is outside the valid range",
    ErrorCode.UNSAFE_RECOVERY: "Laser measurements are not safe for recovery",
    ErrorCode.INTERNAL_ERROR: "Internal server error",
}


def build_success_response(
    command_request: CommandRequest,
    laser_snapshot: LaserSnapshot,
) -> CommandSuccessResponse:
    return CommandSuccessResponse(
        protocol_version=1,
        message_type="response",
        request_id=command_request.request_id,
        status="ok",
        result=laser_snapshot,
    )


def build_error_response(
    request_id: UUID | None,
    error: Exception,
) -> CommandErrorResponse:
    error_code = _error_code_for(error)
    message = str(error) or _DEFAULT_ERROR_MESSAGES[error_code]

    if error_code is ErrorCode.INTERNAL_ERROR:
        message = _DEFAULT_ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR]

    return CommandErrorResponse(
        protocol_version=1,
        message_type="response",
        request_id=request_id,
        status="error",
        error=ErrorDetail(
            code=error_code,
            message=message,
        ),
    )


def _error_code_for(error: Exception) -> ErrorCode:
    for error_type, error_code in _ERROR_CODES:
        if isinstance(error, error_type):
            return error_code

    return ErrorCode.INTERNAL_ERROR

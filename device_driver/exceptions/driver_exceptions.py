from uuid import UUID

from simulated_device.protocol.enums.error_code import ErrorCode


class LaserDriverError(Exception):
    """Base error raised by the high-level laser driver."""


class DriverNotConnectedError(LaserDriverError):
    """A command was requested without an active TCP connection."""


class DriverConnectionError(LaserDriverError):
    """The TCP connection could not be opened or was interrupted."""


class DriverTimeoutError(DriverConnectionError):
    """A connection or response exceeded its configured timeout."""


class DriverProtocolError(LaserDriverError):
    """The device returned a malformed or unrelated response."""


class DeviceCommandError(LaserDriverError):
    """The device understood a command but rejected it."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        request_id: UUID | None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.request_id = request_id

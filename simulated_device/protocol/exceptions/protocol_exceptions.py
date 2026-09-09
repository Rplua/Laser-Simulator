class ProtocolError(Exception):
    """Base error for the TCP application protocol."""


class InvalidFrameLengthError(ProtocolError):
    """The frame declares an invalid payload length."""


class InvalidMessageError(ProtocolError):
    """Base error for an invalid protocol message."""


class InvalidEncodingError(InvalidMessageError):
    """The payload is not valid UTF-8."""


class InvalidJsonError(InvalidMessageError):
    """The UTF-8 payload is not a valid JSON document."""


class InvalidRequestError(InvalidMessageError):
    """The JSON document does not satisfy the request contract."""


class InvalidResponseError(InvalidMessageError):
    """The JSON document does not satisfy the response contract."""


class UnsupportedProtocolVersionError(InvalidMessageError):
    """The request uses a protocol version that is not supported."""


class UnsupportedCommandError(InvalidMessageError):
    """The request names a command that is not supported."""

class ProtocolError(Exception):
    """Base error for the TCP application protocol."""


class InvalidFrameLengthError(ProtocolError):
    """The frame declares an invalid payload length."""

class InvalidMessageError(ProtocolError):
    """The message payload is not valid JSON or violates the protocol contract."""
class ProtocolError(Exception):
    """Base error for the TCP application protocol."""


class InvalidFrameLengthError(ProtocolError):
    """The frame declares an invalid payload length."""

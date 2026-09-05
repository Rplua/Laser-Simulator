from simulated_device.protocol.constants.protocol_constants import (
    BYTE_ORDER,
    HEADER_SIZE_BYTES,
    MAX_PAYLOAD_SIZE_BYTES,
)
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidFrameLengthError,
)


def encode_frame(payload: bytes) -> bytes:
    payload_size = len(payload)
    if payload_size == 0 or payload_size > MAX_PAYLOAD_SIZE_BYTES:
        raise InvalidFrameLengthError(
            f"Payload size must be between 1 and {MAX_PAYLOAD_SIZE_BYTES} bytes; "
            f"got {payload_size}"
        )

    header = payload_size.to_bytes(
        length=HEADER_SIZE_BYTES,
        byteorder=BYTE_ORDER,
        signed=False,
    )

    return header + payload

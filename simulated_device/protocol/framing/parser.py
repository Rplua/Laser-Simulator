from simulated_device.protocol.constants.protocol_constants import (
    BYTE_ORDER,
    HEADER_SIZE_BYTES,
    MAX_PAYLOAD_SIZE_BYTES,
)
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidFrameLengthError,
)


class FrameParser:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self._buffer.extend(data)
        payloads: list[bytes] = []

        while True:
            if len(self._buffer) < HEADER_SIZE_BYTES:
                break

            header = bytes(self._buffer[:HEADER_SIZE_BYTES])
            payload_size = int.from_bytes(
                header,
                byteorder=BYTE_ORDER,
                signed=False,
            )

            if payload_size == 0 or payload_size > MAX_PAYLOAD_SIZE_BYTES:
                raise InvalidFrameLengthError

            frame_size = HEADER_SIZE_BYTES + payload_size

            if len(self._buffer) < frame_size:
                break

            payload = bytes(self._buffer[HEADER_SIZE_BYTES:frame_size])
            del self._buffer[:frame_size]
            payloads.append(payload)

        return payloads

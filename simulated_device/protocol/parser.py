from simulated_device.protocol.constants import HEADER_SIZE_BYTES, BYTE_ORDER


class FrameParser:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self._buffer.extend(data)

        if len(self._buffer) < HEADER_SIZE_BYTES:
            return []

        header: bytes = bytes(self._buffer[:HEADER_SIZE_BYTES])


        payload_size: int = int.from_bytes(
            header,
            byteorder=BYTE_ORDER,
            signed=False,
        )
        frame_size: int = HEADER_SIZE_BYTES + payload_size

        if len(self._buffer) < frame_size:
            return []

        payload: bytes = bytes(self._buffer[HEADER_SIZE_BYTES:frame_size])
        del self._buffer[:frame_size]
        return [payload]





import pytest

from simulated_device.protocol.constants.protocol_constants import (
    BYTE_ORDER,
    HEADER_SIZE_BYTES,
    MAX_PAYLOAD_SIZE_BYTES,
)
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidFrameLengthError,
)
from simulated_device.protocol.framing.encoder import encode_frame
from simulated_device.protocol.framing.parser import FrameParser


def test_encode_frame_prefixes_payload_with_length() -> None:
    frame = encode_frame(b"hello")

    assert len(frame) == 9
    assert frame[:4] == b"\x00\x00\x00\x05"
    assert frame[4:] == b"hello"


def test_encode_frame_throws_if_length_is_zero() -> None:
    with pytest.raises(InvalidFrameLengthError):
        encode_frame(b"")


def test_encode_frame_rejects_payload_larger_than_maximum() -> None:
    payload = b"x" * (MAX_PAYLOAD_SIZE_BYTES + 1)

    with pytest.raises(InvalidFrameLengthError):
        encode_frame(payload)


def test_encode_frame_accepts_maximum_payload_size() -> None:
    payload = b"x" * MAX_PAYLOAD_SIZE_BYTES

    frame = encode_frame(payload)

    assert len(frame) == HEADER_SIZE_BYTES + MAX_PAYLOAD_SIZE_BYTES
    assert frame[:HEADER_SIZE_BYTES] == b"\x00\x01\x00\x00"
    assert frame[HEADER_SIZE_BYTES:] == payload


def test_frame_parser_extracts_one_complete_payload() -> None:
    frame_parser = FrameParser()
    frame = encode_frame(b"hello")
    parsed = frame_parser.feed(frame)
    assert parsed == [b"hello"]


def test_frame_parser_waits_for_complete_header() -> None:
    frame_parser = FrameParser()
    frame = encode_frame(b"hello")
    first_result = frame_parser.feed(frame[:2])
    assert first_result == []

    second_result = frame_parser.feed(frame[2:])
    assert second_result == [b"hello"]

def test_frame_parser_waits_for_complete_payload() -> None:
    frame_parser = FrameParser()
    frame = encode_frame(b"hello")
    first_result = frame_parser.feed(frame[:6])
    assert first_result == []
    second_result = frame_parser.feed(frame[6:])
    assert second_result == [b"hello"]

def test_frame_parser_extracts_multiple_frames_from_one_chunk() -> None:
    frist_frame = encode_frame(b"first")
    second_frame = encode_frame(b"second")
    frame_parser = FrameParser()
    total = frist_frame + second_frame
    result = frame_parser.feed(total)
    assert result == [b"first", b"second"]

def test_frame_parser_extracts_complete_frames_and_keeps_partial_frame() -> None:
    first_frame = encode_frame(b"first")
    second_frame = encode_frame(b"second")
    third_frame = encode_frame(b"third")
    frame_parser = FrameParser()

    first_result = frame_parser.feed(
        first_frame + second_frame + third_frame[:6]
    )
    assert first_result == [b"first", b"second"]

    second_result = frame_parser.feed(third_frame[6:])
    assert second_result == [b"third"]


@pytest.mark.parametrize(
    "payload_size",
    [0, MAX_PAYLOAD_SIZE_BYTES + 1],
)
def test_frame_parser_rejects_invalid_payload_size(payload_size: int) -> None:
    frame_parser = FrameParser()
    invalid_header = payload_size.to_bytes(
        length=HEADER_SIZE_BYTES,
        byteorder=BYTE_ORDER,
        signed=False,
    )

    with pytest.raises(InvalidFrameLengthError):
        frame_parser.feed(invalid_header)

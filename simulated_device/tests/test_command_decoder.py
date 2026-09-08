import json
from uuid import UUID

import pytest

from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidEncodingError,
    InvalidJsonError,
    InvalidRequestError,
    UnsupportedCommandError,
    UnsupportedProtocolVersionError,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.serialization.command_decoder import (
    decode_command,
    extract_request_id,
)


VALID_REQUEST_ID = "123e4567-e89b-12d3-a456-426614174000"


def test_decode_command_returns_valid_command_request() -> None:
    payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{VALID_REQUEST_ID}",
        "command": "set_target_power",
        "payload": {{
            "target_power_mw": 52.0
        }}
    }}
    """.encode("utf-8")

    result = decode_command(payload)

    assert isinstance(result, CommandRequest)
    assert result.protocol_version == 1
    assert result.request_id == UUID(VALID_REQUEST_ID)
    assert result.command is CommandName.SET_TARGET_POWER
    assert result.payload == {"target_power_mw": 52.0}


def test_decode_command_rejects_invalid_utf8() -> None:
    with pytest.raises(InvalidEncodingError):
        decode_command(b"\xff")


def test_decode_command_rejects_malformed_json() -> None:
    with pytest.raises(InvalidJsonError):
        decode_command(b'{"protocol_version":')


def test_decode_command_rejects_unknown_fields() -> None:
    payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{VALID_REQUEST_ID}",
        "command": "set_target_power",
        "payload": {{
            "target_power_mw": 52.0
        }},
        "unexpected_field": "something"
    }}
    """.encode("utf-8")

    with pytest.raises(InvalidRequestError):
        decode_command(payload)


def test_decode_command_rejects_missing_required_fields() -> None:
    payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{VALID_REQUEST_ID}",
        "command": "arm"
    }}
    """.encode("utf-8")

    with pytest.raises(InvalidRequestError):
        decode_command(payload)


def test_decode_command_rejects_unsupported_protocol_version() -> None:
    payload = f"""
    {{
        "protocol_version": 2,
        "message_type": "command",
        "request_id": "{VALID_REQUEST_ID}",
        "command": "arm",
        "payload": {{}}
    }}
    """.encode("utf-8")

    with pytest.raises(UnsupportedProtocolVersionError):
        decode_command(payload)


@pytest.mark.parametrize("version", ["1", 1.0, True])
def test_decode_command_rejects_non_integer_protocol_version(
    version: object,
) -> None:
    payload = json.dumps(
        {
            "protocol_version": version,
            "message_type": "command",
            "request_id": VALID_REQUEST_ID,
            "command": "arm",
            "payload": {},
        }
    ).encode("utf-8")

    with pytest.raises(InvalidRequestError):
        decode_command(payload)


def test_decode_command_rejects_non_string_request_id() -> None:
    payload = b"""
    {
        "protocol_version": 1,
        "message_type": "command",
        "request_id": 123,
        "command": "arm",
        "payload": {}
    }
    """

    with pytest.raises(InvalidRequestError):
        decode_command(payload)


def test_decode_command_rejects_unsupported_command() -> None:
    payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{VALID_REQUEST_ID}",
        "command": "calibrate_flux_capacitor",
        "payload": {{}}
    }}
    """.encode("utf-8")

    with pytest.raises(UnsupportedCommandError):
        decode_command(payload)


def test_extract_request_id_recovers_valid_identifier() -> None:
    payload = f'{{"request_id": "{VALID_REQUEST_ID}"}}'.encode("utf-8")

    assert extract_request_id(payload) == UUID(VALID_REQUEST_ID)


@pytest.mark.parametrize(
    "payload",
    [
        b"\xff",
        b"not-json",
        b'{"request_id": "not-a-uuid"}',
        b'{"request_id": 123}',
    ],
)
def test_extract_request_id_returns_none_when_not_recoverable(
    payload: bytes,
) -> None:
    assert extract_request_id(payload) is None

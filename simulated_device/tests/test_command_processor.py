from uuid import UUID

from simulated_device.application.command_dispatcher import CommandDispatcher
from simulated_device.application.command_processor import CommandProcessor
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.error_code import ErrorCode
from simulated_device.protocol.framing.parser import FrameParser
from simulated_device.protocol.model.command_error_response import (
    CommandErrorResponse,
)
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)


REQUEST_ID = "123e4567-e89b-12d3-a456-426614174000"


def build_processor() -> CommandProcessor:
    return CommandProcessor(CommandDispatcher(Laser()))


def extract_response_payload(response_frame: bytes) -> bytes:
    payloads = FrameParser().feed(response_frame)
    assert len(payloads) == 1
    return payloads[0]


def test_process_payload_returns_framed_success_response() -> None:
    request_payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{REQUEST_ID}",
        "command": "set_target_power",
        "payload": {{"target_power_mw": 52.0}}
    }}
    """.encode("utf-8")

    response_frame = build_processor().process_payload(request_payload)
    response_payload = extract_response_payload(response_frame)
    response = CommandSuccessResponse.model_validate_json(response_payload)

    assert response.request_id == UUID(REQUEST_ID)
    assert response.status == "ok"
    assert response.result.target_power_mw == 52.0


def test_process_payload_maps_domain_error_and_preserves_request_id() -> None:
    request_payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{REQUEST_ID}",
        "command": "start",
        "payload": {{}}
    }}
    """.encode("utf-8")

    response_frame = build_processor().process_payload(request_payload)
    response_payload = extract_response_payload(response_frame)
    response = CommandErrorResponse.model_validate_json(response_payload)

    assert response.request_id == UUID(REQUEST_ID)
    assert response.status == "error"
    assert response.error.code is ErrorCode.INVALID_STATE_TRANSITION


def test_process_payload_returns_error_without_id_for_malformed_json() -> None:
    response_frame = build_processor().process_payload(b"not-json")
    response_payload = extract_response_payload(response_frame)
    response = CommandErrorResponse.model_validate_json(response_payload)

    assert response.request_id is None
    assert response.error.code is ErrorCode.INVALID_JSON


def test_process_payload_recovers_id_from_invalid_request() -> None:
    request_payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{REQUEST_ID}",
        "command": "arm"
    }}
    """.encode("utf-8")

    response_frame = build_processor().process_payload(request_payload)
    response_payload = extract_response_payload(response_frame)
    response = CommandErrorResponse.model_validate_json(response_payload)

    assert response.request_id == UUID(REQUEST_ID)
    assert response.error.code is ErrorCode.INVALID_REQUEST


def test_processor_handles_valid_request_after_invalid_request() -> None:
    processor = build_processor()
    first_frame = processor.process_payload(b"not-json")
    first_payload = extract_response_payload(first_frame)
    first_response = CommandErrorResponse.model_validate_json(first_payload)

    valid_payload = f"""
    {{
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "{REQUEST_ID}",
        "command": "get_snapshot",
        "payload": {{}}
    }}
    """.encode("utf-8")
    second_frame = processor.process_payload(valid_payload)
    second_payload = extract_response_payload(second_frame)
    second_response = CommandSuccessResponse.model_validate_json(second_payload)

    assert first_response.error.code is ErrorCode.INVALID_JSON
    assert second_response.status == "ok"
    assert second_response.request_id == UUID(REQUEST_ID)

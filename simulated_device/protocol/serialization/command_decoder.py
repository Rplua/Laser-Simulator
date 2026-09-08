import json
from json import JSONDecodeError
from uuid import UUID

from pydantic import ValidationError

from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidEncodingError,
    InvalidJsonError,
    InvalidRequestError,
    UnsupportedCommandError,
    UnsupportedProtocolVersionError,
)
from simulated_device.protocol.model.command_request import CommandRequest


def decode_command(payload: bytes) -> CommandRequest:
    document = _decode_json_document(payload)

    if not isinstance(document, dict):
        raise InvalidRequestError("Command message must be a JSON object")

    _check_protocol_version(document)
    _check_command_name(document)
    _check_request_id_type(document)

    try:
        return CommandRequest.model_validate(document)
    except ValidationError as error:
        raise InvalidRequestError("Invalid command request") from error


def extract_request_id(payload: bytes) -> UUID | None:
    """Recover a valid request ID for an error response when possible."""
    try:
        document = _decode_json_document(payload)
    except (InvalidEncodingError, InvalidJsonError):
        return None

    if not isinstance(document, dict):
        return None

    request_id = document.get("request_id")
    if not isinstance(request_id, str):
        return None

    try:
        return UUID(request_id)
    except ValueError:
        return None


def _decode_json_document(payload: bytes) -> object:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidEncodingError("Command payload is not valid UTF-8") from error

    try:
        return json.loads(text)
    except JSONDecodeError as error:
        raise InvalidJsonError("Command payload is not valid JSON") from error


def _check_protocol_version(document: dict[object, object]) -> None:
    version = document.get("protocol_version")
    if "protocol_version" not in document:
        return

    if type(version) is not int:
        raise InvalidRequestError("protocol_version must be an integer")

    if version != 1:
        raise UnsupportedProtocolVersionError(
            f"Protocol version '{version}' is not supported"
        )


def _check_command_name(document: dict[object, object]) -> None:
    command = document.get("command")
    if not isinstance(command, str):
        return

    try:
        CommandName(command)
    except ValueError as error:
        raise UnsupportedCommandError(
            f"Command '{command}' is not supported"
        ) from error


def _check_request_id_type(document: dict[object, object]) -> None:
    if "request_id" not in document:
        return

    if not isinstance(document.get("request_id"), str):
        raise InvalidRequestError("request_id must be a UUID string")

from simulated_device.application.command_dispatcher import CommandDispatcher
from simulated_device.application.response_factory import (
    build_error_response,
    build_success_response,
)
from simulated_device.protocol.framing.encoder import encode_frame
from simulated_device.protocol.serialization.command_decoder import (
    decode_command,
    extract_request_id,
)
from simulated_device.protocol.serialization.response_serializer import (
    serialize_response,
)


class CommandProcessor:
    def __init__(self, dispatcher: CommandDispatcher) -> None:
        self._dispatcher = dispatcher

    def process_payload(self, payload: bytes) -> bytes:
        request_id = extract_request_id(payload)

        try:
            command = decode_command(payload)
            result = self._dispatcher.dispatch(command)
            response = build_success_response(command, result)
        except Exception as error:
            response = build_error_response(request_id, error)

        return encode_frame(serialize_response(response))

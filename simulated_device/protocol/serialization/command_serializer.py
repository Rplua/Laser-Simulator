from simulated_device.protocol.model.command_request import CommandRequest


def serialize_command(command: CommandRequest) -> bytes:
    return command.model_dump_json().encode("utf-8")

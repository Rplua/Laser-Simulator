from uuid import UUID
from uuid import uuid4
import pytest
from pydantic import ValidationError

from simulated_device.aplication.command_dispacher import CommandDispatcher
from simulated_device.laser.enums.laser_states import LaserState
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import InvalidMessageError
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.set_target_power_payload import SetTargetPowerPayload
from simulated_device.protocol.serialization.command_decoder import decode_command


def test_decode_command_returns_valid_command_request() -> None:
    payload = b"""
    {
        "protocol_version": 1,
        "message_type": "command",
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "command": "set_target_power",
        "payload": {
            "target_power_mw": 52.0
        }
    }
    """

    result = decode_command(payload)

    assert isinstance(result, CommandRequest)
    assert result.protocol_version == 1
    assert result.request_id == UUID("123e4567-e89b-12d3-a456-426614174000")
    assert result.command is CommandName.SET_TARGET_POWER
    assert result.payload == {"target_power_mw": 52.0}

def test_decode_command_rejects_malformed_json() -> None:

    with pytest.raises(InvalidMessageError):
        decode_command(b'{"protocol_version":')


def test_decode_command_rejects_unknown_fields() -> None:
    payload = b"""
      {
          "protocol_version": 1,
          "message_type": "command",
          "request_id": "123e4567-e89b-12d3-a456-426614174000",
          "command": "set_target_power",
          "payload": {
              "target_power_mw": 52.0, 
          }
          "unexpected_field": "something"
          
      }
      """
    with pytest.raises(InvalidMessageError):
         decode_command(payload)

def test_set_target_power_payload_rejects_unknown_fields() -> None:
    payload = {
        "target_power_mw": 52.0,
        "unexpected_field": True,
    }

    with pytest.raises(ValidationError):
        SetTargetPowerPayload.model_validate(payload)

def test_dispatch_set_target_power_updates_laser() -> None:
    laser = Laser()
    dispatcher = CommandDispatcher(laser)

    command_request = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.SET_TARGET_POWER,
        payload={"target_power_mw": 52.0},
    )

    result = dispatcher.dispatch(command_request)

    assert result.target_power_mw == 52.0
    assert result.state is LaserState.IDLE
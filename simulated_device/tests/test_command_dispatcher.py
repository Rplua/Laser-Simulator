from uuid import uuid4

import pytest

from simulated_device.application.command_dispatcher import CommandDispatcher
from simulated_device.laser.enums.fault_reason import FaultReason
from simulated_device.laser.enums.laser_states import LaserState
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidMessageError,
)
from simulated_device.protocol.model.command_request import CommandRequest


def build_command_request(
    command: CommandName,
    payload: dict[str, object] | None = None,
) -> CommandRequest:
    return CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=command,
        payload={} if payload is None else payload,
    )


def test_dispatch_set_target_power_updates_laser() -> None:
    laser = Laser()
    dispatcher = CommandDispatcher(laser)
    command = build_command_request(
        CommandName.SET_TARGET_POWER,
        {"target_power_mw": 52.0},
    )

    result = dispatcher.dispatch(command)

    assert result.target_power_mw == 52.0
    assert result.state is LaserState.IDLE


def test_dispatch_arm_changes_laser_state_to_armed() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(build_command_request(CommandName.ARM))

    assert result.state is LaserState.ARMED
    assert result.target_power_mw == 52.0


def test_dispatch_start_changes_laser_state_to_running() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    laser.arm()
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(build_command_request(CommandName.START))

    assert result.state is LaserState.RUNNING
    assert result.target_power_mw == 52.0


def test_dispatch_stop_changes_laser_state_to_idle() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    laser.arm()
    laser.start()
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(build_command_request(CommandName.STOP))

    assert result.state is LaserState.IDLE
    assert result.target_power_mw is None
    assert result.actual_power_mw == 0


def test_dispatch_disarm_changes_laser_state_to_idle() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    laser.arm()
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(build_command_request(CommandName.DISARM))

    assert result.state is LaserState.IDLE
    assert result.target_power_mw == 52.0


def test_dispatch_emergency_stop_enters_fault_state() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    laser.arm()
    laser.start()
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(
        build_command_request(CommandName.EMERGENCY_STOP)
    )

    assert result.state is LaserState.FAULT
    assert result.fault_reason is FaultReason.EMERGENCY_STOP
    assert result.actual_power_mw == 0
    assert result.current_ma == 0


def test_dispatch_recover_returns_laser_to_idle() -> None:
    laser = Laser()
    laser.emergency_stop()
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(build_command_request(CommandName.RECOVER))

    assert result.state is LaserState.IDLE
    assert result.fault_reason is None


def test_dispatch_get_snapshot_returns_current_laser_state() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    dispatcher = CommandDispatcher(laser)

    result = dispatcher.dispatch(build_command_request(CommandName.GET_SNAPSHOT))

    assert result == laser.snapshot()
    assert result.target_power_mw == 52.0


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"target_power_mw": "not-a-number"},
        {"target_power_mw": 52.0, "unexpected_field": True},
    ],
)
def test_dispatch_set_target_power_rejects_invalid_payload(
    payload: dict[str, object],
) -> None:
    dispatcher = CommandDispatcher(Laser())
    command = build_command_request(CommandName.SET_TARGET_POWER, payload)

    with pytest.raises(InvalidMessageError):
        dispatcher.dispatch(command)


def test_dispatch_command_without_arguments_rejects_non_empty_payload() -> None:
    laser = Laser()
    laser.set_target_power(52.0)
    dispatcher = CommandDispatcher(laser)
    command = build_command_request(
        CommandName.ARM,
        {"unexpected_field": True},
    )

    with pytest.raises(InvalidMessageError):
        dispatcher.dispatch(command)

    assert laser.snapshot().state is LaserState.IDLE

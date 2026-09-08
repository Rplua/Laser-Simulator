from collections.abc import Callable

from pydantic import ValidationError

from simulated_device.laser.laser.laser import Laser
from simulated_device.laser.model.laser_snapshot import LaserSnapshot
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidRequestError,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.empty_payload import EmptyPayload
from simulated_device.protocol.model.set_target_power_payload import (
    SetTargetPowerPayload,
)


class CommandDispatcher:
    def __init__(self, laser: Laser) -> None:
        self._laser = laser
        self._handlers: dict[
            CommandName,
            Callable[[dict[str, object]], None],
        ] = {
            CommandName.SET_TARGET_POWER: self._handle_set_target_power,
            CommandName.ARM: self._handle_arm,
            CommandName.START: self._handle_start,
            CommandName.STOP: self._handle_stop,
            CommandName.DISARM: self._handle_disarm,
            CommandName.EMERGENCY_STOP: self._handle_emergency_stop,
            CommandName.RECOVER: self._handle_recover,
            CommandName.GET_SNAPSHOT: self._handle_get_snapshot,
        }

    def dispatch(self, command: CommandRequest) -> LaserSnapshot:
        handler = self._handlers.get(command.command)
        if handler is None:
            raise NotImplementedError(
                f"Command '{command.command.value}' is not implemented"
            )

        try:
            handler(command.payload)
        except ValidationError as error:
            raise InvalidRequestError(
                f"Invalid payload for command '{command.command.value}'"
            ) from error

        return self._laser.snapshot()

    def _handle_set_target_power(self, payload: dict[str, object]) -> None:
        validated_payload = SetTargetPowerPayload.model_validate(payload)
        self._laser.set_target_power(validated_payload.target_power_mw)

    def _handle_arm(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)
        self._laser.arm()

    def _handle_start(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)
        self._laser.start()

    def _handle_stop(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)
        self._laser.stop()

    def _handle_disarm(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)
        self._laser.disarm()

    def _handle_emergency_stop(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)
        self._laser.emergency_stop()

    def _handle_recover(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)
        self._laser.recover()

    def _handle_get_snapshot(self, payload: dict[str, object]) -> None:
        EmptyPayload.model_validate(payload)

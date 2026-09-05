from simulated_device.laser.laser.laser import Laser
from simulated_device.laser.model.laser_snapshot import LaserSnapshot
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.set_target_power_payload import SetTargetPowerPayload


class CommandDispatcher:
    def __init__(self, laser: Laser) -> None:
        self._laser = laser

    def dispatch(self, command: CommandRequest) -> LaserSnapshot:
        if command.command is CommandName.SET_TARGET_POWER:
            payload = SetTargetPowerPayload.model_validate(command.payload)
            self._laser.set_target_power(payload.target_power_mw)
            return self._laser.snapshot()

        raise NotImplementedError(
            f"Command '{command.command.value}' is not implemented"
        )
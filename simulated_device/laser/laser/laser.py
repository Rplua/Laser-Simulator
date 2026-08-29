from simulated_device.laser.constants.constants import POWER_RAMP_RATE_MW_PER_SECOND, CURRENT_MA_PER_MW, \
    HEATING_RATE_C_PER_MW_SECOND, COOLING_RATE_C_PER_SECOND, AMBIENT_TEMPERATURE_C
from simulated_device.laser.enums.fault_reason import FaultReason
from simulated_device.laser.laser.exceptions import (
    InvalidTargetPowerError,
    InvalidStateTransitionError,
    TargetPowerNotConfiguredError, UnsafeRecoveryError,
)
from simulated_device.laser.model.laser_snapshot import LaserSnapshot
from simulated_device.laser.enums.laser_states import LaserState


class Laser:
    def __init__(self,) -> None:
        self._state: LaserState = LaserState.IDLE
        self._actual_power_mw: float = 0
        self._target_power_mw: float| None = None
        self._temperature_c: float = 25
        self._current_ma: float = 0
        self._fault_reason: FaultReason | None = None

    def arm(self) -> None:
        if self._state is not LaserState.IDLE:
            raise InvalidStateTransitionError(
                f"Cannot arm laser from state '{self._state.value}'; expected 'idle'"
            )

        if self._target_power_mw is None:
            raise TargetPowerNotConfiguredError(
                "Cannot arm laser without a configured target power"
            )

        self._state = LaserState.ARMED

    def start(self) -> None:
        if self._state is not LaserState.ARMED:
            raise InvalidStateTransitionError(
                f"Cannot start laser from state '{self._state.value}'; expected 'armed'"
            )
        self._state = LaserState.RUNNING

    def disarm(self) -> None:
        if self._state is not LaserState.ARMED:
            raise InvalidStateTransitionError(
                f"Cannot disarm laser from state '{self._state.value}'; expected 'armed'"
            )
        self._state = LaserState.IDLE


    def stop(self) -> None:
        if self._state is not LaserState.RUNNING:
            raise InvalidStateTransitionError(
                f"Cannot stop laser from state '{self._state.value}'; expected 'running'"
            )
        self._state = LaserState.IDLE
        self._target_power_mw = None
        self._actual_power_mw = 0
        self._current_ma = 0

    def set_target_power(self, target_mw: float) -> None:
        if self._state is not LaserState.IDLE:
            raise InvalidStateTransitionError(
                f"Cannot set target power to state '{self._state.value}'; expected 'idle'"
            )
        if not 1 <= target_mw <= 100:
            raise InvalidTargetPowerError(
                f"Cannot set target power to {target_mw} mW; "
                "expected a value between 1 and 100 mW"
            )
        self._target_power_mw = target_mw

    def emergency_stop(self) -> None:
        self._enter_fault(FaultReason.EMERGENCY_STOP)


    def recover(self) -> None:
        if self._state is not LaserState.FAULT:
            raise InvalidStateTransitionError(
                f"Cannot recover laser from state '{self._state.value}'; expected 'fault'"
            )
        if self._temperature_c > 45 or self._current_ma > 400:
            raise UnsafeRecoveryError(
                f"Cannot recover laser current  '{self._current_ma}' is higher than 400 or the temperature '{self._temperature_c} is bigger than 45'"
            )
        self._state = LaserState.IDLE
        self._target_power_mw = None
        self._actual_power_mw = 0
        self._fault_reason = None
        self._current_ma = 0

    def _enter_fault(self, reason: FaultReason) -> None:
        self._state = LaserState.FAULT
        self._actual_power_mw = 0
        self._fault_reason = reason
        self._current_ma = 0

    def update_measurements(self, temperature_c: float, current_ma: float, actual_power_mw: float) -> None:
        self._temperature_c = temperature_c
        self._current_ma = current_ma
        self._actual_power_mw = actual_power_mw

        if temperature_c >= 60:
            self._enter_fault(FaultReason.OVER_TEMPERATURE)
        elif current_ma >= 450:
            self._enter_fault(FaultReason.OVER_CURRENT)

    def tick(self, delta_seconds: float) -> None:
        if delta_seconds <= 0:
            raise ValueError("delta_seconds must be positive")

        if self._state is not LaserState.RUNNING:
            self._actual_power_mw = 0
            self._current_ma = 0
            cooled_temperature = (
                    self._temperature_c
                    - COOLING_RATE_C_PER_SECOND * delta_seconds
            )

            if cooled_temperature < AMBIENT_TEMPERATURE_C:
                self._temperature_c = AMBIENT_TEMPERATURE_C
            else:
                self._temperature_c = cooled_temperature
            return

        if self._target_power_mw is None:
            raise RuntimeError(
                "RUNNING laser has no configured target power"
            )
        power_increase = POWER_RAMP_RATE_MW_PER_SECOND * delta_seconds
        calculated_power = self._actual_power_mw + power_increase
        self._actual_power_mw = min(
            calculated_power,
            self._target_power_mw,
        )
        self._current_ma = self._actual_power_mw * CURRENT_MA_PER_MW
        temperature_increase= self._actual_power_mw * HEATING_RATE_C_PER_MW_SECOND * delta_seconds
        self._temperature_c = self._temperature_c + temperature_increase


    def snapshot(self) -> LaserSnapshot:
        return LaserSnapshot(
            state = self._state,
            actual_power_mw = self._actual_power_mw,
            target_power_mw=  self._target_power_mw,
            temperature_c= self._temperature_c,
            current_ma= self._current_ma,
            fault_reason = self._fault_reason
        )
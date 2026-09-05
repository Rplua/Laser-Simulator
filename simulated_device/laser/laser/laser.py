from simulated_device.laser.constants.laser_constants import (
    AMBIENT_TEMPERATURE_C,
    COOLING_RATE_C_PER_SECOND,
    CURRENT_MA_PER_MW,
    FAULT_CURRENT_MA,
    FAULT_TEMPERATURE_C,
    HEATING_RATE_C_PER_MW_SECOND,
    MAX_SAFE_RECOVERY_CURRENT_MA,
    MAX_SAFE_RECOVERY_TEMPERATURE_C,
    MAX_TARGET_POWER_MW,
    MIN_TARGET_POWER_MW,
    POWER_RAMP_RATE_MW_PER_SECOND,
)
from simulated_device.laser.enums.fault_reason import FaultReason
from simulated_device.laser.enums.laser_states import LaserState
from simulated_device.laser.exceptions.laser_exceptions import (
    InvalidStateTransitionError,
    InvalidTargetPowerError,
    TargetPowerNotConfiguredError,
    UnsafeRecoveryError,
)
from simulated_device.laser.model.laser_snapshot import LaserSnapshot


class Laser:
    def __init__(self) -> None:
        self._state: LaserState = LaserState.IDLE
        self._actual_power_mw: float = 0.0
        self._target_power_mw: float | None = None
        self._temperature_c: float = AMBIENT_TEMPERATURE_C
        self._current_ma: float = 0.0
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
        self._reset_output()

    def set_target_power(self, target_mw: float) -> None:
        if self._state is not LaserState.IDLE:
            raise InvalidStateTransitionError(
                f"Cannot set target power to state '{self._state.value}'; expected 'idle'"
            )
        if not MIN_TARGET_POWER_MW <= target_mw <= MAX_TARGET_POWER_MW:
            raise InvalidTargetPowerError(
                f"Cannot set target power to {target_mw} mW; "
                f"expected a value between {MIN_TARGET_POWER_MW:g} "
                f"and {MAX_TARGET_POWER_MW:g} mW"
            )
        self._target_power_mw = target_mw

    def emergency_stop(self) -> None:
        self._enter_fault(FaultReason.EMERGENCY_STOP)

    def recover(self) -> None:
        if self._state is not LaserState.FAULT:
            raise InvalidStateTransitionError(
                f"Cannot recover laser from state '{self._state.value}'; expected 'fault'"
            )
        if (
            self._temperature_c > MAX_SAFE_RECOVERY_TEMPERATURE_C
            or self._current_ma > MAX_SAFE_RECOVERY_CURRENT_MA
        ):
            raise UnsafeRecoveryError(
                "Cannot recover laser while measurements are unsafe: "
                f"temperature={self._temperature_c:g} °C "
                f"(maximum {MAX_SAFE_RECOVERY_TEMPERATURE_C:g} °C), "
                f"current={self._current_ma:g} mA "
                f"(maximum {MAX_SAFE_RECOVERY_CURRENT_MA:g} mA)"
            )
        self._state = LaserState.IDLE
        self._target_power_mw = None
        self._fault_reason = None
        self._reset_output()

    def update_measurements(
        self,
        temperature_c: float,
        current_ma: float,
        actual_power_mw: float,
    ) -> None:
        self._temperature_c = temperature_c
        self._current_ma = current_ma
        self._actual_power_mw = actual_power_mw

        self._check_safety_limits()

    def tick(self, delta_seconds: float) -> None:
        if delta_seconds <= 0:
            raise ValueError("delta_seconds must be positive")

        if self._state is not LaserState.RUNNING:
            self._reset_output()
            self._cool_down(delta_seconds)
            return

        self._ramp_power(delta_seconds)
        self._update_current()
        self._heat_up(delta_seconds)
        self._check_safety_limits()

    def snapshot(self) -> LaserSnapshot:
        return LaserSnapshot(
            state=self._state,
            actual_power_mw=self._actual_power_mw,
            target_power_mw=self._target_power_mw,
            temperature_c=self._temperature_c,
            current_ma=self._current_ma,
            fault_reason=self._fault_reason,
        )

    def _ramp_power(self, delta_seconds: float) -> None:
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

    def _update_current(self) -> None:
        self._current_ma = self._actual_power_mw * CURRENT_MA_PER_MW

    def _heat_up(self, delta_seconds: float) -> None:
        temperature_increase = (
            self._actual_power_mw
            * HEATING_RATE_C_PER_MW_SECOND
            * delta_seconds
        )
        self._temperature_c = self._temperature_c + temperature_increase

    def _reset_output(self) -> None:
        self._actual_power_mw = 0
        self._current_ma = 0

    def _cool_down(self, delta_seconds: float) -> None:
        cooled_temperature = (
            self._temperature_c - COOLING_RATE_C_PER_SECOND * delta_seconds
        )

        if cooled_temperature < AMBIENT_TEMPERATURE_C:
            self._temperature_c = AMBIENT_TEMPERATURE_C
        else:
            self._temperature_c = cooled_temperature

    def _check_safety_limits(self) -> None:
        if self._temperature_c >= FAULT_TEMPERATURE_C:
            self._enter_fault(FaultReason.OVER_TEMPERATURE)
        elif self._current_ma >= FAULT_CURRENT_MA:
            self._enter_fault(FaultReason.OVER_CURRENT)

    def _enter_fault(self, reason: FaultReason) -> None:
        self._state = LaserState.FAULT
        self._fault_reason = reason
        self._reset_output()

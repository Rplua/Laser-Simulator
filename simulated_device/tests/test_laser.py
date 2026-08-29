import pytest

from simulated_device.laser.enums.fault_reason import FaultReason
from simulated_device.laser.laser.exceptions import (
    InvalidStateTransitionError,
    InvalidTargetPowerError,
    TargetPowerNotConfiguredError,
    UnsafeRecoveryError,
)
from simulated_device.laser.laser.laser import Laser
from simulated_device.laser.enums.laser_states import LaserState


def test_new_laser_has_expected_initial_snapshot() -> None:
    laser = Laser()
    laser_snapshot = laser.snapshot()

    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.temperature_c == 25
    assert laser_snapshot.current_ma == 0
    assert laser_snapshot.fault_reason is None

def test_laser_cannot_arm_without_target_power()-> None:
    laser = Laser()
    with pytest.raises(TargetPowerNotConfiguredError):
        laser.arm()
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None


def test_setting_valid_target_power_updates_only_target() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.target_power_mw == 50
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.state is LaserState.IDLE


@pytest.mark.parametrize("value", [-10, 0, 101, 150])
def test_invalid_target_power_is_rejected(value: float) -> None:
    laser = Laser()

    with pytest.raises(InvalidTargetPowerError):
        laser.set_target_power(value)

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0


@pytest.mark.parametrize("value", [10, 1, 100, 50])
def test_target_power_accepts_valid_boundaries(value: float) -> None:
    laser = Laser()
    laser.set_target_power(value)

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw == value
    assert laser_snapshot.actual_power_mw == 0


def test_arm_changes_state_to_armed() -> None:
    laser = Laser()
    laser.set_target_power(10)

    laser.arm()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.ARMED
    assert laser_snapshot.target_power_mw == 10
    assert laser_snapshot.actual_power_mw == 0


def test_start_changes_state_to_running() -> None:
    laser = Laser()
    laser.set_target_power(10)

    laser.arm()
    laser.start()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.RUNNING
    assert laser_snapshot.target_power_mw == 10
    assert laser_snapshot.actual_power_mw == 0


def test_start_from_idle_is_rejected() -> None:
    laser = Laser()
    with pytest.raises(InvalidStateTransitionError):
        laser.start()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0

def test_disarm_transitions_from_armed_to_idle() -> None:
    laser = Laser()
    laser.set_target_power(10)
    laser.arm()
    laser.disarm()
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw == 10
    assert laser_snapshot.actual_power_mw == 0

def test_stop_from_running_resets_laser_to_idle() -> None:
    laser = Laser()
    laser.set_target_power(10)

    laser.arm()
    laser.start()
    laser.tick(1)
    laser.stop()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == pytest.approx(25.05)
    assert laser_snapshot.current_ma == 0

def test_cannot_change_target_power_while_armed() -> None:
    laser = Laser()
    laser.set_target_power(10)
    laser.arm()
    with pytest.raises(InvalidStateTransitionError):
        laser.set_target_power(20)
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.ARMED
    assert laser_snapshot.target_power_mw == 10
    assert laser_snapshot.actual_power_mw == 0


def test_disarm_from_idle_is_rejected() -> None:
    laser = Laser()

    with pytest.raises(InvalidStateTransitionError):
        laser.disarm()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0


def test_stop_from_idle_is_rejected() -> None:
    laser = Laser()

    with pytest.raises(InvalidStateTransitionError):
        laser.stop()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0


def test_arm_from_armed_is_rejected() -> None:
    laser = Laser()
    laser.set_target_power(10)
    laser.arm()

    with pytest.raises(InvalidStateTransitionError):
        laser.arm()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.ARMED
    assert laser_snapshot.target_power_mw == 10
    assert laser_snapshot.actual_power_mw == 0

def test_emergency_stop_from_running_enters_fault() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()
    laser.emergency_stop()
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.FAULT
    assert laser_snapshot.fault_reason is FaultReason.EMERGENCY_STOP
    assert laser_snapshot.target_power_mw == 50
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == 25
    assert laser_snapshot.current_ma == 0

def test_safe_recovery_from_fault_returns_laser_to_idle() -> None:
    laser = Laser()
    laser.set_target_power(10)
    laser.arm()
    laser.start()
    laser.emergency_stop()
    laser.recover()
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == 25
    assert laser_snapshot.current_ma == 0
    assert laser_snapshot.fault_reason is None

def test_recover_from_idle_is_rejected() -> None:
    laser = Laser()
    with pytest.raises(InvalidStateTransitionError):
        laser.recover()
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == 25
    assert laser_snapshot.current_ma == 0
    assert laser_snapshot.fault_reason is None

def test_temperature_at_fault_threshold_enters_fault() -> None:
    laser = Laser()
    laser.set_target_power(80)
    laser.update_measurements(60,20,20)
    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.FAULT
    assert laser_snapshot.fault_reason is FaultReason.OVER_TEMPERATURE
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.current_ma == 0
    assert laser_snapshot.target_power_mw == 80
    assert laser_snapshot.temperature_c == 60

def test_temperature_below_fault_threshold_keeps_laser_running() -> None:
    laser = Laser()
    laser.set_target_power(50)

    laser.arm()
    laser.start()
    laser.update_measurements(
        temperature_c=59.9,
        current_ma=20,
        actual_power_mw=20,
    )

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.RUNNING
    assert laser_snapshot.target_power_mw == 50
    assert laser_snapshot.actual_power_mw == 20
    assert laser_snapshot.temperature_c == 59.9
    assert laser_snapshot.current_ma == 20
    assert laser_snapshot.fault_reason is None


def test_current_at_fault_threshold_enters_fault() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()

    laser.update_measurements(
        temperature_c=25,
        current_ma=450,
        actual_power_mw=30,
    )

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.FAULT
    assert laser_snapshot.fault_reason is FaultReason.OVER_CURRENT
    assert laser_snapshot.target_power_mw == 50
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == 25
    assert laser_snapshot.current_ma == 0


def test_current_below_fault_threshold_keeps_laser_running() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()

    laser.update_measurements(
        temperature_c=25,
        current_ma=449.9,
        actual_power_mw=30,
    )

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.RUNNING
    assert laser_snapshot.fault_reason is None
    assert laser_snapshot.target_power_mw == 50
    assert laser_snapshot.actual_power_mw == 30
    assert laser_snapshot.temperature_c == 25
    assert laser_snapshot.current_ma == 449.9


def test_recovery_is_rejected_while_temperature_is_unsafe() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()
    laser.update_measurements(
        temperature_c=60,
        current_ma=20,
        actual_power_mw=30,
    )

    with pytest.raises(UnsafeRecoveryError):
        laser.recover()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.FAULT
    assert laser_snapshot.fault_reason is FaultReason.OVER_TEMPERATURE
    assert laser_snapshot.target_power_mw == 50
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == 60
    assert laser_snapshot.current_ma == 0


def test_recovery_succeeds_after_temperature_reaches_safe_limit() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()
    laser.update_measurements(
        temperature_c=60,
        current_ma=20,
        actual_power_mw=30,
    )
    laser.update_measurements(
        temperature_c=45,
        current_ma=0,
        actual_power_mw=0,
    )

    laser.recover()

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.fault_reason is None
    assert laser_snapshot.target_power_mw is None
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.temperature_c == 45
    assert laser_snapshot.current_ma == 0

def test_tick_ramps_power_to_target_without_overshooting() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()

    expected_measurements = [
        (20, 80),
        (40, 160),
        (50, 200),
        (50, 200),
    ]

    for expected_power, expected_current in expected_measurements:
        laser.tick(1)
        laser_snapshot = laser.snapshot()

        assert laser_snapshot.actual_power_mw == expected_power
        assert laser_snapshot.current_ma == expected_current
        assert laser_snapshot.state is LaserState.RUNNING
        assert laser_snapshot.fault_reason is None
        assert laser_snapshot.target_power_mw == 50
        assert laser_snapshot.actual_power_mw <= 50


def test_tick_increases_temperature_while_running() -> None:
    laser = Laser()
    laser.set_target_power(50)
    laser.arm()
    laser.start()

    laser.tick(1)

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.actual_power_mw == 20
    assert laser_snapshot.current_ma == 80
    assert laser_snapshot.temperature_c == pytest.approx(25.1)

def test_tick_cools_non_running_laser_toward_ambient_temperature() -> None:
    laser = Laser()
    laser.update_measurements(
        temperature_c=30,
        current_ma=0,
        actual_power_mw=0,
    )

    laser.tick(2)

    laser_snapshot = laser.snapshot()
    assert laser_snapshot.state is LaserState.IDLE
    assert laser_snapshot.temperature_c == pytest.approx(28)
    assert laser_snapshot.actual_power_mw == 0
    assert laser_snapshot.current_ma == 0
from fastapi import FastAPI
from fastapi.testclient import TestClient

from control_service.tests.fakes.fake_laser_driver import FakeLaserDriver
from simulated_device.laser.enums.fault_reason import FaultReason
from simulated_device.laser.enums.laser_states import LaserState
from simulated_device.laser.model.laser_snapshot import LaserSnapshot
from control_service.api.dependencies import get_laser_driver


def test_get_laser_snapshot_returns_current_device_state(
    client: TestClient,
    api_app: FastAPI,
) -> None:
    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.IDLE,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason=None
    )
    fake_driver: FakeLaserDriver = FakeLaserDriver(is_connected=True, snapshot=laser_snapshot)

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.get("/laser/snapshot")

    assert response.status_code == 200
    assert response.json() == {
        "state": "idle",
        "actual_power_mw": 0.0,
        "target_power_mw": 50.0,
        "temperature_c": 25.0,
        "current_ma": 0.0,
        "fault_reason": None,
    }

def test_put_on_target_power_mw(
    client: TestClient,
    api_app: FastAPI,
)->None:
    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.IDLE,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason=None
    )
    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.put("/laser/target-power", json={"target_power_mw": 50})

    assert fake_driver.received_target_power_mw == 50
    assert response.status_code == 200
    assert response.json()["target_power_mw"] == 50

def test_arm_laser_forwards_command_and_returns_armed_snapshot(
    client: TestClient,
    api_app: FastAPI,
) -> None:

    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.ARMED,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason=None
    )

    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.post("/laser/commands/arm")

    assert response.status_code == 200
    assert fake_driver.commands_called == ["arm"]
    assert response.json()["state"] == "armed"

def test_start_laser_forwards_command_and_returns_running_snapshot(
    client: TestClient,
    api_app: FastAPI,
) -> None:

    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.RUNNING,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason=None
    )

    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.post("/laser/commands/start")

    assert response.status_code == 200
    assert fake_driver.commands_called == ["start"]
    assert response.json()["state"] == "running"


def test_stop_laser_forwards_command_and_returns_idle_snapshot(
    client: TestClient,
    api_app: FastAPI,
) -> None:

    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.IDLE,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason=None
    )

    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.post("/laser/commands/stop")

    assert response.status_code == 200
    assert fake_driver.commands_called == ["stop"]
    assert response.json()["state"] == "idle"


def test_disarm_laser_forwards_command_and_returns_idle_snapshot(
    client: TestClient,
    api_app: FastAPI,
) -> None:

    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.IDLE,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason=None
    )

    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.post("/laser/commands/disarm")

    assert response.status_code == 200
    assert fake_driver.commands_called == ["disarm"]
    assert response.json()["state"] == "idle"


def test_emergency_stop_laser_forwards_command_and_returns_idle_snapshot(
    client: TestClient,
    api_app: FastAPI,
) -> None:

    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.IDLE,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason= FaultReason.EMERGENCY_STOP
    )

    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.post("/laser/commands/emergency-stop")

    assert response.status_code == 200
    assert fake_driver.commands_called == ["emergency_stop"]
    assert response.json()["state"] == "idle"


def test_recover_laser_forwards_command_and_returns_idle_snapshot(
    client: TestClient,
    api_app: FastAPI,
) -> None:

    laser_snapshot: LaserSnapshot = LaserSnapshot(
        state=LaserState.IDLE,
        actual_power_mw=0,
        target_power_mw=50,
        temperature_c=25,
        current_ma=0,
        fault_reason= None
    )

    fake_driver: FakeLaserDriver = FakeLaserDriver(
        is_connected=True,
        snapshot=laser_snapshot,
    )

    api_app.dependency_overrides[get_laser_driver] = lambda: fake_driver
    response = client.post("/laser/commands/recover")

    assert response.status_code == 200
    assert fake_driver.commands_called == ["recover"]
    assert response.json()["state"] == "idle"
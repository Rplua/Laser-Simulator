import asyncio

import pytest

from device_driver.exceptions.driver_exceptions import (
    DeviceCommandError,
    DriverConnectionError,
    DriverNotConnectedError,
    DriverTimeoutError,
)
from device_driver.laser_driver import LaserDriver
from simulated_device.application.command_dispatcher import CommandDispatcher
from simulated_device.application.command_processor import CommandProcessor
from simulated_device.laser.enums.laser_states import LaserState
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.enums.error_code import ErrorCode
from simulated_device.transport.tcp.tcp_server import LaserTCPServer


def build_server() -> LaserTCPServer:
    laser = Laser()
    dispatcher = CommandDispatcher(laser)
    processor = CommandProcessor(dispatcher)
    return LaserTCPServer("127.0.0.1", 0, processor)


@pytest.mark.asyncio
async def test_driver_executes_high_level_command_sequence() -> None:
    server = build_server()
    await server.start()
    driver = LaserDriver("127.0.0.1", server.bound_port)

    try:
        await driver.connect()

        configured = await driver.set_target_power(52.0)
        armed = await driver.arm()
        running = await driver.start()
        faulted = await driver.emergency_stop()

        assert configured.target_power_mw == 52.0
        assert armed.state is LaserState.ARMED
        assert running.state is LaserState.RUNNING
        assert faulted.state is LaserState.FAULT
        assert driver.is_connected is True
    finally:
        await driver.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_driver_translates_device_error() -> None:
    server = build_server()
    await server.start()
    driver = LaserDriver("127.0.0.1", server.bound_port)

    try:
        await driver.connect()

        with pytest.raises(DeviceCommandError) as captured_error:
            await driver.start()

        assert (
            captured_error.value.code
            is ErrorCode.INVALID_STATE_TRANSITION
        )
        assert captured_error.value.request_id is not None
        assert driver.is_connected is True
    finally:
        await driver.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_driver_rejects_command_when_not_connected() -> None:
    driver = LaserDriver("127.0.0.1", 9000)

    with pytest.raises(DriverNotConnectedError):
        await driver.get_snapshot()


@pytest.mark.asyncio
async def test_driver_can_reconnect_explicitly() -> None:
    server = build_server()
    await server.start()
    driver = LaserDriver("127.0.0.1", server.bound_port)

    try:
        await driver.connect()
        await driver.reconnect(max_attempts=1, delay_seconds=0)

        snapshot = await driver.get_snapshot()

        assert driver.is_connected is True
        assert snapshot.state is LaserState.IDLE
    finally:
        await driver.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_driver_serializes_concurrent_commands() -> None:
    server = build_server()
    await server.start()
    driver = LaserDriver("127.0.0.1", server.bound_port)

    try:
        await driver.connect()

        first_snapshot, second_snapshot = await asyncio.gather(
            driver.get_snapshot(),
            driver.get_snapshot(),
        )

        assert first_snapshot.state is LaserState.IDLE
        assert second_snapshot.state is LaserState.IDLE
    finally:
        await driver.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_driver_reports_connection_failure(
    unused_tcp_port: int,
) -> None:
    driver = LaserDriver(
        "127.0.0.1",
        unused_tcp_port,
        connect_timeout_seconds=0.1,
    )

    with pytest.raises(DriverConnectionError):
        await driver.connect()

    assert driver.is_connected is False


@pytest.mark.asyncio
async def test_reconnect_stops_after_configured_attempts(
    unused_tcp_port: int,
) -> None:
    driver = LaserDriver(
        "127.0.0.1",
        unused_tcp_port,
        connect_timeout_seconds=0.1,
    )

    with pytest.raises(
        DriverConnectionError,
        match="Could not reconnect after 2 attempts",
    ):
        await driver.reconnect(max_attempts=2, delay_seconds=0)


@pytest.mark.asyncio
async def test_response_timeout_drops_connection() -> None:
    handler_finished = asyncio.Event()

    async def accept_without_responding(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            await reader.read()
        finally:
            writer.close()
            await writer.wait_closed()
            handler_finished.set()

    silent_server = await asyncio.start_server(
        accept_without_responding,
        "127.0.0.1",
        0,
    )
    sockets = silent_server.sockets
    assert sockets
    port = int(sockets[0].getsockname()[1])
    driver = LaserDriver(
        "127.0.0.1",
        port,
        response_timeout_seconds=0.05,
    )

    try:
        await driver.connect()

        with pytest.raises(DriverTimeoutError):
            await driver.get_snapshot()

        assert driver.is_connected is False
        await asyncio.wait_for(handler_finished.wait(), timeout=1)
    finally:
        await driver.disconnect()
        silent_server.close()
        await silent_server.wait_closed()

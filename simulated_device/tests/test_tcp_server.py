import asyncio
from uuid import uuid4

import pytest

from simulated_device.application.command_dispatcher import CommandDispatcher
from simulated_device.application.command_processor import CommandProcessor
from simulated_device.laser.enums.laser_states import LaserState
from simulated_device.laser.laser.laser import Laser
from simulated_device.protocol.constants.protocol_constants import (
    BYTE_ORDER,
    HEADER_SIZE_BYTES,
)
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.framing.encoder import encode_frame
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.model.command_success_response import (
    CommandSuccessResponse,
)
from simulated_device.protocol.serialization.command_serializer import (
    serialize_command,
)
from simulated_device.protocol.serialization.response_decoder import (
    decode_response,
)
from simulated_device.transport.tcp.tcp_server import LaserTCPServer


def build_server() -> LaserTCPServer:
    laser = Laser()
    dispatcher = CommandDispatcher(laser)
    processor = CommandProcessor(dispatcher)
    return LaserTCPServer("127.0.0.1", 0, processor)


async def read_response_payload(reader: asyncio.StreamReader) -> bytes:
    header = await reader.readexactly(HEADER_SIZE_BYTES)
    payload_size = int.from_bytes(
        header,
        byteorder=BYTE_ORDER,
        signed=False,
    )
    return await reader.readexactly(payload_size)


async def close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_serve_forever_requires_started_server() -> None:
    server = build_server()

    with pytest.raises(RuntimeError):
        await server.serve_forever()


@pytest.mark.asyncio
async def test_start_rejects_second_start() -> None:
    server = build_server()
    await server.start()

    try:
        with pytest.raises(RuntimeError):
            await server.start()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_server_processes_real_tcp_command() -> None:
    server = build_server()
    await server.start()
    reader, writer = await asyncio.open_connection(
        "127.0.0.1",
        server.bound_port,
    )

    request = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.GET_SNAPSHOT,
        payload={},
    )

    try:
        writer.write(encode_frame(serialize_command(request)))
        await writer.drain()

        response_payload = await read_response_payload(reader)
        response = decode_response(response_payload)

        assert isinstance(response, CommandSuccessResponse)
        assert response.request_id == request.request_id
        assert response.result.state is LaserState.IDLE
    finally:
        await close_writer(writer)
        await server.stop()


@pytest.mark.asyncio
async def test_invalid_frame_closes_only_responsible_connection() -> None:
    server = build_server()
    await server.start()
    first_reader, first_writer = await asyncio.open_connection(
        "127.0.0.1",
        server.bound_port,
    )

    try:
        first_writer.write(b"\x00\x00\x00\x00")
        await first_writer.drain()

        assert await first_reader.read() == b""

        second_reader, second_writer = await asyncio.open_connection(
            "127.0.0.1",
            server.bound_port,
        )
        request = CommandRequest(
            protocol_version=1,
            message_type="command",
            request_id=uuid4(),
            command=CommandName.GET_SNAPSHOT,
            payload={},
        )

        try:
            second_writer.write(encode_frame(serialize_command(request)))
            await second_writer.drain()
            response = decode_response(
                await read_response_payload(second_reader)
            )
            assert isinstance(response, CommandSuccessResponse)
        finally:
            await close_writer(second_writer)
    finally:
        await close_writer(first_writer)
        await server.stop()


@pytest.mark.asyncio
async def test_stop_closes_active_client_connections() -> None:
    server = build_server()
    await server.start()
    reader, writer = await asyncio.open_connection(
        "127.0.0.1",
        server.bound_port,
    )
    request = CommandRequest(
        protocol_version=1,
        message_type="command",
        request_id=uuid4(),
        command=CommandName.GET_SNAPSHOT,
        payload={},
    )
    writer.write(encode_frame(serialize_command(request)))
    await writer.drain()
    await read_response_payload(reader)

    await server.stop()

    assert await asyncio.wait_for(reader.read(), timeout=1) == b""
    await close_writer(writer)

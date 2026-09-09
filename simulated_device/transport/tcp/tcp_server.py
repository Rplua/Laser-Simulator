import asyncio
from contextlib import suppress

from simulated_device.application.command_processor import CommandProcessor
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidFrameLengthError,
)
from simulated_device.protocol.framing.parser import FrameParser


READ_CHUNK_SIZE_BYTES = 4096


class LaserTCPServer:
    def __init__(
        self,
        host: str,
        port: int,
        command_processor: CommandProcessor,
    ) -> None:
        self._host = host
        self._port = port
        self._command_processor = command_processor
        self._server: asyncio.Server | None = None
        self._client_writers: set[asyncio.StreamWriter] = set()
        self._client_tasks: set[asyncio.Task[None]] = set()
        self._bound_port: int | None = None

    @property
    def bound_port(self) -> int:
        if self._bound_port is None:
            raise RuntimeError("TCP server has not been started")
        return self._bound_port

    async def start(self) -> None:
        if self._server is not None:
            raise RuntimeError("TCP server is already started")

        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
        )

        sockets = self._server.sockets
        if not sockets:
            await self.stop()
            raise RuntimeError("TCP server did not create a listening socket")

        self._bound_port = int(sockets[0].getsockname()[1])

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        frame_parser = FrameParser()
        client_task = asyncio.current_task()

        self._client_writers.add(writer)
        if client_task is not None:
            self._client_tasks.add(client_task)

        try:
            while True:
                data = await reader.read(READ_CHUNK_SIZE_BYTES)

                if not data:
                    break

                payloads = frame_parser.feed(data)

                for payload in payloads:
                    response_frame = self._command_processor.process_payload(
                        payload
                    )

                    writer.write(response_frame)
                    await writer.drain()
        except (InvalidFrameLengthError, ConnectionError, OSError):
            pass
        finally:
            self._client_writers.discard(writer)
            if client_task is not None:
                self._client_tasks.discard(client_task)
            await self._close_writer(writer)

    async def serve_forever(self) -> None:
        if self._server is None:
            raise RuntimeError("TCP server has not been started")

        await self._server.serve_forever()

    async def stop(self) -> None:
        server = self._server
        if server is None:
            return

        self._server = None
        self._bound_port = None

        server.close()

        client_writers = tuple(self._client_writers)
        for writer in client_writers:
            writer.close()

        current_task = asyncio.current_task()
        client_tasks = tuple(
            task
            for task in self._client_tasks
            if task is not current_task
        )

        for task in client_tasks:
            task.cancel()

        if client_tasks:
            await asyncio.gather(*client_tasks, return_exceptions=True)

        await server.wait_closed()

        self._client_writers.clear()
        self._client_tasks.clear()

    @staticmethod
    async def _close_writer(writer: asyncio.StreamWriter) -> None:
        writer.close()
        with suppress(ConnectionError, OSError):
            await writer.wait_closed()

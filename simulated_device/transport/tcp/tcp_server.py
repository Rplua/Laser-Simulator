import asyncio

from simulated_device.application.command_processor import CommandProcessor
from simulated_device.protocol.framing.parser import FrameParser


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

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
        )

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        frame_parser = FrameParser()

        try:
            while True:
                data = await reader.read(4096)

                if not data:
                    break

                payloads = frame_parser.feed(data)

                for payload in payloads:
                    response_frame = self._command_processor.process_payload(
                        payload
                    )

                    writer.write(response_frame)
                    await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def serve_forever(self) -> None:
        if self._server is None:
            raise RuntimeError("TCP server has not been started")

        await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server is None:
            return

        self._server.close()
        await self._server.wait_closed()
        self._server = None
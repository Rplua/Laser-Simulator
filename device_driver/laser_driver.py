import asyncio
from contextlib import suppress
from uuid import uuid4

from device_driver.exceptions.driver_exceptions import (
    DeviceCommandError,
    DriverConnectionError,
    DriverNotConnectedError,
    DriverProtocolError,
    DriverTimeoutError,
)
from simulated_device.laser.model.laser_snapshot import LaserSnapshot
from simulated_device.protocol.constants.protocol_constants import (
    BYTE_ORDER,
    HEADER_SIZE_BYTES,
    MAX_PAYLOAD_SIZE_BYTES,
)
from simulated_device.protocol.enums.command_name import CommandName
from simulated_device.protocol.exceptions.protocol_exceptions import (
    InvalidResponseError,
)
from simulated_device.protocol.framing.encoder import encode_frame
from simulated_device.protocol.model.command_error_response import (
    CommandErrorResponse,
)
from simulated_device.protocol.model.command_request import CommandRequest
from simulated_device.protocol.serialization.command_serializer import (
    serialize_command,
)
from simulated_device.protocol.serialization.response_decoder import (
    decode_response,
)


class LaserDriver:
    def __init__(
        self,
        host: str,
        port: int,
        connect_timeout_seconds: float = 3.0,
        response_timeout_seconds: float = 3.0,
    ) -> None:
        if connect_timeout_seconds <= 0:
            raise ValueError("connect_timeout_seconds must be positive")
        if response_timeout_seconds <= 0:
            raise ValueError("response_timeout_seconds must be positive")

        self._host = host
        self._port = port
        self._connect_timeout_seconds = connect_timeout_seconds
        self._response_timeout_seconds = response_timeout_seconds
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._request_lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        if self.is_connected:
            return

        await self._drop_connection()

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout_seconds,
            )
        except TimeoutError as error:
            raise DriverTimeoutError(
                f"Timed out connecting to {self._host}:{self._port}"
            ) from error
        except OSError as error:
            raise DriverConnectionError(
                f"Could not connect to {self._host}:{self._port}"
            ) from error

    async def disconnect(self) -> None:
        await self._drop_connection()

    async def reconnect(
        self,
        max_attempts: int = 3,
        delay_seconds: float = 0.5,
    ) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")

        await self._drop_connection()
        last_error: DriverConnectionError | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                await self.connect()
                return
            except DriverConnectionError as error:
                last_error = error
                if attempt < max_attempts:
                    await asyncio.sleep(delay_seconds)

        raise DriverConnectionError(
            f"Could not reconnect after {max_attempts} attempts"
        ) from last_error

    async def set_target_power(
        self,
        target_power_mw: float,
    ) -> LaserSnapshot:
        return await self._execute_command(
            CommandName.SET_TARGET_POWER,
            {"target_power_mw": target_power_mw},
        )

    async def arm(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.ARM)

    async def start(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.START)

    async def stop(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.STOP)

    async def disarm(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.DISARM)

    async def emergency_stop(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.EMERGENCY_STOP)

    async def recover(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.RECOVER)

    async def get_snapshot(self) -> LaserSnapshot:
        return await self._execute_command(CommandName.GET_SNAPSHOT)

    async def _execute_command(
        self,
        command_name: CommandName,
        payload: dict[str, object] | None = None,
    ) -> LaserSnapshot:
        async with self._request_lock:
            reader, writer = self._require_connection()
            request = CommandRequest(
                protocol_version=1,
                message_type="command",
                request_id=uuid4(),
                command=command_name,
                payload=payload or {},
            )
            request_frame = encode_frame(serialize_command(request))

            try:
                writer.write(request_frame)
                await asyncio.wait_for(
                    writer.drain(),
                    timeout=self._response_timeout_seconds,
                )
                response_payload = await asyncio.wait_for(
                    self._read_response_payload(reader),
                    timeout=self._response_timeout_seconds,
                )
            except TimeoutError as error:
                await self._drop_connection()
                raise DriverTimeoutError(
                    f"Timed out waiting for '{command_name.value}' response"
                ) from error
            except (
                asyncio.IncompleteReadError,
                ConnectionError,
                OSError,
            ) as error:
                await self._drop_connection()
                raise DriverConnectionError(
                    f"Connection lost while executing '{command_name.value}'"
                ) from error
            except DriverProtocolError:
                await self._drop_connection()
                raise

            try:
                response = decode_response(response_payload)
            except InvalidResponseError as error:
                await self._drop_connection()
                raise DriverProtocolError(
                    "Device returned an invalid response"
                ) from error

            if response.request_id != request.request_id:
                await self._drop_connection()
                raise DriverProtocolError(
                    "Response request_id does not match the command request"
                )

            if isinstance(response, CommandErrorResponse):
                raise DeviceCommandError(
                    code=response.error.code,
                    message=response.error.message,
                    request_id=response.request_id,
                )

            return response.result

    def _require_connection(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if (
            self._reader is None
            or self._writer is None
            or self._writer.is_closing()
        ):
            raise DriverNotConnectedError("Laser driver is not connected")

        return self._reader, self._writer

    @staticmethod
    async def _read_response_payload(
        reader: asyncio.StreamReader,
    ) -> bytes:
        header = await reader.readexactly(HEADER_SIZE_BYTES)
        payload_size = int.from_bytes(
            header,
            byteorder=BYTE_ORDER,
            signed=False,
        )

        if payload_size == 0 or payload_size > MAX_PAYLOAD_SIZE_BYTES:
            raise DriverProtocolError(
                f"Device declared invalid payload size {payload_size}"
            )

        return await reader.readexactly(payload_size)

    async def _drop_connection(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None

        if writer is None:
            return

        writer.close()
        with suppress(ConnectionError, OSError):
            await writer.wait_closed()

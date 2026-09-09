import asyncio
from contextlib import suppress

from simulated_device.application.command_dispatcher import CommandDispatcher
from simulated_device.application.command_processor import CommandProcessor
from simulated_device.application.simulation_runner import run_simulation
from simulated_device.laser.laser.laser import Laser
from simulated_device.transport.tcp.tcp_server import LaserTCPServer


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000


async def run_device() -> None:
    laser = Laser()
    dispatcher = CommandDispatcher(laser)
    processor = CommandProcessor(dispatcher)
    server = LaserTCPServer(DEFAULT_HOST, DEFAULT_PORT, processor)

    await server.start()
    simulation_task = asyncio.create_task(run_simulation(laser))

    print(f"Laser device simulator listening on {DEFAULT_HOST}:{server.bound_port}")

    try:
        await server.serve_forever()
    finally:
        simulation_task.cancel()
        with suppress(asyncio.CancelledError):
            await simulation_task
        await server.stop()


def main() -> None:
    try:
        asyncio.run(run_device())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

import asyncio

from simulated_device.laser.laser.laser import Laser


DEFAULT_TICK_INTERVAL_SECONDS = 0.1


async def run_simulation(
    laser: Laser,
    tick_interval_seconds: float = DEFAULT_TICK_INTERVAL_SECONDS,
) -> None:
    if tick_interval_seconds <= 0:
        raise ValueError("tick_interval_seconds must be positive")

    event_loop = asyncio.get_running_loop()
    previous_time = event_loop.time()

    while True:
        await asyncio.sleep(tick_interval_seconds)
        current_time = event_loop.time()
        laser.tick(current_time - previous_time)
        previous_time = current_time

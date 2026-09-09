import asyncio

from device_driver.laser_driver import LaserDriver


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000


async def run_demo() -> None:
    driver = LaserDriver(DEFAULT_HOST, DEFAULT_PORT)

    try:
        await driver.connect()
        snapshot = await driver.get_snapshot()
        print(snapshot.model_dump_json(indent=2))
    finally:
        await driver.disconnect()


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()

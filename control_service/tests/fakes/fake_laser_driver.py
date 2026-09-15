from simulated_device.laser.model.laser_snapshot import LaserSnapshot


class FakeLaserDriver:
    def __init__(
        self,
        is_connected: bool,
        snapshot: LaserSnapshot | None = None,
    ) -> None:
        self.is_connected = is_connected
        self._snapshot = snapshot
        self.received_target_power_mw: float | None = None
        self.commands_called: list[str] = []

    async def get_snapshot(self) -> LaserSnapshot:
        if self._snapshot is None:
            raise RuntimeError("No snapshot configured in fake driver")

        return self._snapshot

    async def set_target_power(
        self,
        target_power_mw: float,
    ) -> LaserSnapshot:
        self.received_target_power_mw = target_power_mw
        return await self.get_snapshot()

    async def arm(self) -> LaserSnapshot:
        self.commands_called.append("arm")
        return await self.get_snapshot()

    async def start(self) -> LaserSnapshot:
        self.commands_called.append("start")
        return await self.get_snapshot()

    async def stop(self) -> LaserSnapshot:
        self.commands_called.append("stop")
        return await self.get_snapshot()

    async def disarm(self) -> LaserSnapshot:
        self.commands_called.append("disarm")
        return await self.get_snapshot()

    async def emergency_stop(self) -> LaserSnapshot:
        self.commands_called.append("emergency_stop")
        return await self.get_snapshot()

    async def recover(self) -> LaserSnapshot:
        self.commands_called.append("recover")
        return await self.get_snapshot()
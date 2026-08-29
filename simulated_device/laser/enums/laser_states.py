from enum import Enum



class LaserState(Enum):
    IDLE = "idle"
    ARMED = "armed"
    RUNNING = "running"
    FAULT = "fault"

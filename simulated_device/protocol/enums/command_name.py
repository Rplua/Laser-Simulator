from enum import StrEnum


class CommandName(StrEnum):
    SET_TARGET_POWER = "set_target_power"
    ARM = "arm"
    START = "start"
    STOP = "stop"
    DISARM = "disarm"
    EMERGENCY_STOP = "emergency_stop"
    RECOVER = "recover"
    GET_SNAPSHOT = "get_snapshot"

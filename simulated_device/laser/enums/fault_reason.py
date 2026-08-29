from enum import Enum



class FaultReason(Enum):
    EMERGENCY_STOP = "emergency_stop"
    OVER_TEMPERATURE = "over_temperature"
    OVER_CURRENT = "over_current"

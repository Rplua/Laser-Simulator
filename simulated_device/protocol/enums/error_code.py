from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_FRAME_LENGTH = "invalid_frame_length"
    INVALID_ENCODING = "invalid_encoding"
    INVALID_JSON = "invalid_json"
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_PROTOCOL_VERSION = "unsupported_protocol_version"
    UNSUPPORTED_COMMAND = "unsupported_command"
    INVALID_STATE_TRANSITION = "invalid_state_transition"
    TARGET_POWER_NOT_CONFIGURED = "target_power_not_configured"
    INVALID_TARGET_POWER = "invalid_target_power"
    UNSAFE_RECOVERY = "unsafe_recovery"
    INTERNAL_ERROR = "internal_error"

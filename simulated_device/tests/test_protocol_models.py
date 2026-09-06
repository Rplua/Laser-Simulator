import pytest
from pydantic import ValidationError

from simulated_device.protocol.model.set_target_power_payload import (
    SetTargetPowerPayload,
)


def test_set_target_power_payload_rejects_unknown_fields() -> None:
    payload = {
        "target_power_mw": 52.0,
        "unexpected_field": True,
    }

    with pytest.raises(ValidationError):
        SetTargetPowerPayload.model_validate(payload)

from pydantic import BaseModel, ConfigDict


class EmptyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

from typing import Literal
from pydantic import BaseModel, field_validator

VALID_EVENTS = {
    "browsing.completed",
    "browsing.failed",
    "research.completed",
    "research.failed",
    "scout.updated",
    "scout.paused",
    "scout.resumed",
    "scout.completed",
}

WebhookFormat = Literal["sentinel", "slack", "zapier"]


class WebhookEndpointCreate(BaseModel):
    name: str
    url: str
    events: list[str] = list(VALID_EVENTS)
    webhook_format: WebhookFormat = "sentinel"

    @field_validator("events")
    @classmethod
    def validate_events(cls, v):
        invalid = set(v) - VALID_EVENTS
        if invalid:
            raise ValueError(f"Unknown event types: {invalid}")
        return v


class WebhookEndpointUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None
    webhook_format: WebhookFormat | None = None

    @field_validator("events")
    @classmethod
    def validate_events(cls, v):
        if v is not None:
            invalid = set(v) - VALID_EVENTS
            if invalid:
                raise ValueError(f"Unknown event types: {invalid}")
        return v


class WebhookEndpointResponse(BaseModel):
    id: str
    name: str
    url: str
    secret: str
    events: list[str]
    is_active: bool
    webhook_format: str
    created_at: str

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: str
    endpoint_id: str
    event_type: str
    status: str
    attempts: int
    last_attempt_at: str | None
    response_status: int | None
    created_at: str

    model_config = {"from_attributes": True}

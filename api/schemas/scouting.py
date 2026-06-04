from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class ScoutCreate(BaseModel):
    query: str
    display_name: str | None = None
    output_interval: int = Field(default=86400, ge=1800)
    start_timestamp: int = 0
    user_timezone: str = "America/Los_Angeles"
    user_location: str = "San Francisco, CA, US"
    skip_email: bool = True
    is_public: bool = False
    webhook_url: str | None = None
    webhook_format: str = "sentinel"
    output_schema: dict | None = None


class ScoutPatch(BaseModel):
    display_name: str | None = None
    output_interval: int | None = None
    webhook_url: str | None = None
    webhook_format: str | None = None
    output_schema: dict | None = None
    skip_email: bool | None = None
    is_public: bool | None = None


class ScoutResponse(BaseModel):
    id: str
    query: str
    display_name: str | None = None
    status: str
    output_interval: int
    next_run_at: datetime | None = None
    created_at: datetime
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    view_url: str | None = None
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes = True)


class ScoutUpdateItem(BaseModel):
    id: str
    timestamp: int
    content: str
    citations: list | None = None
    structured_result: Any | None = None
    structured_output_status: str = "not_requested"
    stats: dict | None = None
    header_image_url: str | None = None


class ScoutUpdatesResponse(BaseModel):
    updates: list[ScoutUpdateItem]
    prev_cursor: str | None = None
    next_cursor: str | None = None


class EmailSettingsUpdate(BaseModel):
    emails: list[str]

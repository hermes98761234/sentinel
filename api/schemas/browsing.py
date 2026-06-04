from typing import Any
from pydantic import BaseModel, Field


class BrowsingTaskCreate(BaseModel):
    task: str
    start_url: str
    max_steps: int = Field(default=20, ge=2, le=100)
    agent: str | None = None
    require_auth: bool = False
    browser: str = "cloud"
    output_schema: dict | None = None
    webhook_url: str | None = None
    webhook_format: str = "sentinel"


class BrowsingTaskResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None
    structured_result: Any | None = None
    structured_output_status: str = "not_requested"
    rejection_reason: str | None = None

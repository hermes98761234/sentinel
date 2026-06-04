from pydantic import BaseModel


class ResearchTaskCreate(BaseModel):
    query: str
    mode: str = "deep"
    user_timezone: str = "America/Los_Angeles"
    user_location: str = "San Francisco, CA, US"
    output_schema: dict | None = None
    webhook_url: str | None = None
    webhook_format: str = "sentinel"
    skip_email: bool = True


class ResearchTaskResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None
    structured_result: dict | None = None
    structured_output_status: str = "not_requested"
    view_url: str | None = None
    mode: str = "deep"

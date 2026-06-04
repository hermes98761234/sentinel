import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from api.core.db import Base


class ResearchTask(Base):
    __tablename__ = "research_tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str] = mapped_column(String(10), default="deep")
    status: Mapped[str] = mapped_column(String(20), default="queued")
    result: Mapped[str | None] = mapped_column(String, nullable=True)
    structured_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured_output_status: Mapped[str] = mapped_column(String(20), default="not_requested")
    output_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    webhook_format: Mapped[str] = mapped_column(String(20), default="sentinel")
    skip_email: Mapped[bool] = mapped_column(Boolean, default=True)
    user_timezone: Mapped[str] = mapped_column(String(64), default="America/Los_Angeles")
    user_location: Mapped[str] = mapped_column(String(255), default="San Francisco, CA, US")
    view_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

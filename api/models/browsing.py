import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from api.core.db import Base


class BrowsingTask(Base):
    __tablename__ = "browsing_tasks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id: Mapped[str] = mapped_column(String, nullable=False)
    task: Mapped[str] = mapped_column(String, nullable=False)
    start_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    result: Mapped[str | None] = mapped_column(String, nullable=True)
    structured_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured_output_status: Mapped[str] = mapped_column(String(20), default="not_requested")
    trajectory: Mapped[list | None] = mapped_column(JSON, nullable=True)
    agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_steps: Mapped[int] = mapped_column(Integer, default=20)
    require_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    output_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    webhook_format: Mapped[str] = mapped_column(String(20), default="sentinel")
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

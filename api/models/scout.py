import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from api.core.db import Base


class Scout(Base):
    __tablename__ = "scouts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    output_interval: Mapped[int] = mapped_column(Integer, default=86400)
    status: Mapped[str] = mapped_column(String(20), default="active")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    output_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String, nullable=True)
    webhook_format: Mapped[str] = mapped_column(String(20), default="sentinel")
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_timezone: Mapped[str] = mapped_column(String(64), default="America/Los_Angeles")
    user_location: Mapped[str] = mapped_column(String(255), default="San Francisco, CA, US")
    skip_email: Mapped[bool] = mapped_column(Boolean, default=True)


class ScoutUpdate(Base):
    __tablename__ = "scout_updates"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scout_id: Mapped[str] = mapped_column(String, ForeignKey("scouts.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    structured_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured_output_status: Mapped[str] = mapped_column(String(20), default="not_requested")
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    header_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScoutSubscription(Base):
    __tablename__ = "scout_subscriptions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scout_id: Mapped[str] = mapped_column(String, ForeignKey("scouts.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

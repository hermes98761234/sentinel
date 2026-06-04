import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from api.models.scout import Scout, ScoutUpdate, ScoutSubscription
from api.schemas.scouting import ScoutCreate, ScoutPatch


async def create_scout(db: AsyncSession, data: ScoutCreate, api_key_id: str) -> Scout:
    scout = Scout(
        id=str(uuid.uuid4()), api_key_id=api_key_id, query=data.query,
        display_name=data.display_name or data.query[:64],
        output_interval=data.output_interval, user_timezone=data.user_timezone,
        user_location=data.user_location, skip_email=data.skip_email,
        is_public=data.is_public, webhook_url=data.webhook_url,
        webhook_format=data.webhook_format, output_schema=data.output_schema, status="active",
    )
    db.add(scout)
    await db.commit()
    await db.refresh(scout)
    return scout


async def get_scout(db: AsyncSession, scout_id: str) -> Scout | None:
    result = await db.execute(select(Scout).where(Scout.id == scout_id))
    return result.scalar_one_or_none()


async def list_scouts(db: AsyncSession, api_key_id: str, status: str | None = None) -> list[Scout]:
    q = select(Scout).where(Scout.api_key_id == api_key_id)
    if status:
        q = q.where(Scout.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def patch_scout(db: AsyncSession, scout: Scout, data: ScoutPatch) -> Scout:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(scout, field, value)
    await db.commit()
    await db.refresh(scout)
    return scout


async def delete_scout(db: AsyncSession, scout: Scout) -> None:
    await db.delete(scout)
    await db.commit()


async def set_scout_status(db: AsyncSession, scout: Scout, status: str) -> Scout:
    scout.status = status
    if status == "paused":
        scout.paused_at = datetime.now(timezone.utc)
    elif status == "active":
        scout.paused_at = None
    elif status == "completed":
        scout.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(scout)
    return scout


async def get_scout_updates(db: AsyncSession, scout_id: str, page_size: int = 20, cursor: str | None = None):
    q = select(ScoutUpdate).where(ScoutUpdate.scout_id == scout_id).order_by(ScoutUpdate.created_at.desc())
    if cursor:
        q = q.where(ScoutUpdate.id < cursor)
    q = q.limit(page_size + 1)
    result = await db.execute(q)
    updates = list(result.scalars().all())
    next_cursor = None
    if len(updates) > page_size:
        updates = updates[:page_size]
        next_cursor = updates[-1].id
    return updates, None, next_cursor


async def update_email_settings(db: AsyncSession, scout_id: str, emails: list[str]) -> None:
    await db.execute(delete(ScoutSubscription).where(ScoutSubscription.scout_id == scout_id))
    for email in emails:
        db.add(ScoutSubscription(scout_id=scout_id, email=email))
    await db.commit()

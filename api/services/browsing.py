import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.models.browsing import BrowsingTask
from api.schemas.browsing import BrowsingTaskCreate
from api.core.config import settings


async def create_browsing_task(db: AsyncSession, data: BrowsingTaskCreate, api_key_id: int) -> BrowsingTask:
    task = BrowsingTask(
        id=str(uuid.uuid4()),
        api_key_id=str(api_key_id),
        task=data.task,
        start_url=data.start_url,
        max_steps=data.max_steps,
        agent=data.agent or settings.sentinel_vision_model,
        require_auth=data.require_auth,
        output_schema=data.output_schema,
        webhook_url=data.webhook_url,
        webhook_format=data.webhook_format,
        status="queued",
        trajectory=[],
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_browsing_task(db: AsyncSession, task_id: str) -> BrowsingTask | None:
    result = await db.execute(select(BrowsingTask).where(BrowsingTask.id == task_id))
    return result.scalar_one_or_none()

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.models.research import ResearchTask
from api.schemas.research import ResearchTaskCreate
from api.core.config import settings


async def create_research_task(db: AsyncSession, data: ResearchTaskCreate, api_key_id: str) -> ResearchTask:
    task_id = str(uuid.uuid4())
    task = ResearchTask(
        id=task_id,
        api_key_id=api_key_id,
        query=data.query,
        mode=data.mode,
        user_timezone=data.user_timezone,
        user_location=data.user_location,
        output_schema=data.output_schema,
        webhook_url=data.webhook_url,
        webhook_format=data.webhook_format,
        skip_email=data.skip_email,
        status="queued",
        view_url=f"{settings.sentinel_api_base_url}/v1/research/tasks/{task_id}",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_research_task(db: AsyncSession, task_id: str) -> ResearchTask | None:
    result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
    return result.scalar_one_or_none()

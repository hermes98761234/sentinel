import asyncio
from api.workers.celery_app import celery_app
from api.core.config import settings


@celery_app.task(name="research.run_research_task", bind=True, max_retries=1)
def run_research_task(self, task_id: str):
    asyncio.run(_run_research_async(task_id))


async def _run_research_async(task_id: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, update
    from api.models.research import ResearchTask
    from api.core.openrouter import openrouter_client
    from api.services.webhook import fire_webhook, dispatch_event

    engine = create_async_engine(settings.database_url)
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSession() as db:
        result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return
        await db.execute(update(ResearchTask).where(ResearchTask.id == task_id).values(status="running"))
        await db.commit()

    max_iterations = 10 if task.mode == "deep" else 3
    messages = [
        {"role": "system", "content": (
            f"You are a research assistant. Location: {task.user_location}. Timezone: {task.user_timezone}. "
            "Research the user's query thoroughly and provide a comprehensive, well-structured response."
        )},
        {"role": "user", "content": task.query},
    ]

    try:
        final_result = "Research completed."
        for _ in range(max_iterations):
            response = await openrouter_client.chat_completions({
                "model": settings.sentinel_default_model,
                "messages": messages,
                "max_completion_tokens": 2048,
                "temperature": 0.3,
            })
            choice = response["choices"][0]["message"]
            content = choice.get("content", "")
            if not choice.get("tool_calls"):
                final_result = content
                break
            messages.append({"role": "assistant", "content": content})

        async with AsyncSession() as db:
            task_row = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
            task = task_row.scalar_one()
            await db.execute(update(ResearchTask).where(ResearchTask.id == task_id).values(status="succeeded", result=final_result))
            await db.commit()
            event_type = "research.completed"
            event_payload = {
                "event": event_type,
                "task_id": task.id,
                "status": "succeeded",
                "result": final_result,
            }
            await dispatch_event(db, event_type, event_payload)
            if task.webhook_url:
                await fire_webhook(task.webhook_url, task.webhook_format, {"task_id": task_id, "status": "succeeded", "result": final_result})

    except Exception as e:
        async with AsyncSession() as db:
            await db.execute(update(ResearchTask).where(ResearchTask.id == task_id).values(status="failed", result=str(e)))
            await db.commit()
            event_type = "research.failed"
            event_payload = {
                "event": event_type,
                "task_id": task_id,
                "status": "failed",
                "result": str(e),
            }
            await dispatch_event(db, event_type, event_payload)
        raise
    finally:
        await engine.dispose()

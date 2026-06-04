import asyncio
import uuid
from datetime import datetime, timezone
from api.workers.celery_app import celery_app
from api.core.config import settings


def schedule_scout(scout_id: str, interval_seconds: int) -> None:
    celery_app.conf.beat_schedule[f"scout-{scout_id}"] = {
        "task": "scouting.run_scout_task",
        "schedule": interval_seconds,
        "args": [scout_id],
    }


def unschedule_scout(scout_id: str) -> None:
    celery_app.conf.beat_schedule.pop(f"scout-{scout_id}", None)


@celery_app.task(name="scouting.run_scout_task", bind=True, max_retries=1)
def run_scout_task(self, scout_id: str):
    asyncio.run(_run_scout_async(scout_id))


async def _run_scout_async(scout_id: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, update
    from api.models.scout import Scout, ScoutUpdate
    from api.core.openrouter import openrouter_client
    from api.services.webhook import fire_webhook, dispatch_event

    engine = create_async_engine(settings.database_url)
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSession() as db:
        result = await db.execute(select(Scout).where(Scout.id == scout_id))
        scout = result.scalar_one_or_none()
        if not scout or scout.status != "active":
            await engine.dispose()
            return

    try:
        response = await openrouter_client.chat_completions({
            "model": settings.sentinel_default_model,
            "messages": [
                {"role": "system", "content": f"You are a web monitoring assistant. Location: {scout.user_location}. Timezone: {scout.user_timezone}. Summarize relevant recent developments for the monitoring query."},
                {"role": "user", "content": scout.query},
            ],
            "max_completion_tokens": 1024,
            "temperature": 0.3,
        })
        content = response["choices"][0]["message"].get("content", "No results found.")

        async with AsyncSession() as db:
            last = await db.execute(select(ScoutUpdate).where(ScoutUpdate.scout_id == scout_id).order_by(ScoutUpdate.created_at.desc()).limit(1))
            last_update = last.scalar_one_or_none()
            if not last_update or last_update.content != content:
                new_update = ScoutUpdate(id=str(uuid.uuid4()), scout_id=scout_id, content=content, stats={"tool_calls": 1, "time_saved": 5})
                db.add(new_update)
                await db.execute(update(Scout).where(Scout.id == scout_id).values(next_run_at=datetime.now(timezone.utc)))
                await db.commit()
                event_payload = {
                    "event": "scout.updated",
                    "scout_id": scout.id,
                    "update_id": new_update.id,
                    "content": new_update.content[:500],
                }
                await dispatch_event(db, "scout.updated", event_payload)
                if scout.webhook_url:
                    await fire_webhook(scout.webhook_url, scout.webhook_format, {
                        "scout_id": scout_id, "query": scout.query, "content": content,
                        "timestamp": int(datetime.now(timezone.utc).timestamp()),
                    })
    except Exception:
        raise
    finally:
        await engine.dispose()

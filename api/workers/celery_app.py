from celery import Celery
from api.core.config import settings

celery_app = Celery(
    "sentinel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["api.workers.browsing", "api.workers.research", "api.workers.scouting"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={},
)

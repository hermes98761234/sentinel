from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.db import get_db
from api.core.auth import get_current_key
from api.models.api_key import ApiKey
from api.schemas.scouting import (
    ScoutCreate, ScoutPatch, ScoutResponse, ScoutUpdatesResponse,
    ScoutUpdateItem, EmailSettingsUpdate,
)
from api.services.scouting import (
    create_scout, get_scout, list_scouts, patch_scout, delete_scout,
    set_scout_status, get_scout_updates, update_email_settings,
)

router = APIRouter()


@router.post("/scouting/tasks", response_model=ScoutResponse)
async def create(data: ScoutCreate, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await create_scout(db, data, key.id)
    from api.workers.scouting import schedule_scout
    schedule_scout(scout.id, scout.output_interval)
    return scout


@router.get("/scouting/tasks", response_model=list[ScoutResponse])
async def list_all(status: str | None = Query(None), key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    return await list_scouts(db, key.id, status)


@router.get("/scouting/tasks/{scout_id}", response_model=ScoutResponse)
async def get_one(scout_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    return scout


@router.put("/scouting/tasks/{scout_id}", response_model=ScoutResponse)
async def full_update(scout_id: str, data: ScoutCreate, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    return await patch_scout(db, scout, ScoutPatch(**data.model_dump()))


@router.patch("/scouting/tasks/{scout_id}", response_model=ScoutResponse)
async def partial_update(scout_id: str, data: ScoutPatch, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    return await patch_scout(db, scout, data)


@router.delete("/scouting/tasks/{scout_id}")
async def remove(scout_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    from api.workers.scouting import unschedule_scout
    unschedule_scout(scout_id)
    await delete_scout(db, scout)
    return {"deleted": True}


@router.post("/scouting/tasks/{scout_id}/pause", response_model=ScoutResponse)
async def pause(scout_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    from api.workers.scouting import unschedule_scout
    unschedule_scout(scout_id)
    return await set_scout_status(db, scout, "paused")


@router.post("/scouting/tasks/{scout_id}/resume", response_model=ScoutResponse)
async def resume(scout_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    scout = await set_scout_status(db, scout, "active")
    from api.workers.scouting import schedule_scout
    schedule_scout(scout_id, scout.output_interval)
    return scout


@router.post("/scouting/tasks/{scout_id}/restart", response_model=ScoutResponse)
async def restart(scout_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    scout = await set_scout_status(db, scout, "active")
    from api.workers.scouting import schedule_scout, run_scout_task
    schedule_scout(scout_id, scout.output_interval)
    run_scout_task.delay(scout_id)
    return scout


@router.post("/scouting/tasks/{scout_id}/done", response_model=ScoutResponse)
async def done(scout_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    from api.workers.scouting import unschedule_scout
    unschedule_scout(scout_id)
    return await set_scout_status(db, scout, "completed")


@router.get("/scouting/tasks/{scout_id}/updates", response_model=ScoutUpdatesResponse)
async def get_updates(scout_id: str, page_size: int = Query(default=20, ge=1, le=100), cursor: str | None = Query(None), key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    updates, prev_cursor, next_cursor = await get_scout_updates(db, scout_id, page_size, cursor)
    return ScoutUpdatesResponse(
        updates=[ScoutUpdateItem(
            id=u.id, timestamp=int(u.created_at.timestamp()), content=u.content,
            citations=u.citations, structured_result=u.structured_result,
            structured_output_status=u.structured_output_status, stats=u.stats,
            header_image_url=u.header_image_url,
        ) for u in updates],
        prev_cursor=prev_cursor, next_cursor=next_cursor,
    )


@router.put("/scouting/tasks/{scout_id}/email-settings")
async def email_settings(scout_id: str, data: EmailSettingsUpdate, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    scout = await get_scout(db, scout_id)
    if not scout:
        raise HTTPException(404, "Scout not found")
    await update_email_settings(db, scout_id, data.emails)
    return {"updated": True}

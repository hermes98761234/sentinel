from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.db import get_db
from api.core.auth import get_current_key
from api.models.api_key import ApiKey
from api.schemas.browsing import BrowsingTaskCreate, BrowsingTaskResponse
from api.services.browsing import create_browsing_task, get_browsing_task

router = APIRouter()


@router.post("/browsing/tasks", response_model=BrowsingTaskResponse)
async def create_task(data: BrowsingTaskCreate, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    task = await create_browsing_task(db, data, key.id)
    from api.workers.browsing import run_browsing_task
    run_browsing_task.delay(task.id)
    return BrowsingTaskResponse(task_id=task.id, status=task.status)


@router.get("/browsing/tasks/{task_id}", response_model=BrowsingTaskResponse)
async def get_task(task_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    task = await get_browsing_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return BrowsingTaskResponse(
        task_id=task.id, status=task.status, result=task.result,
        structured_result=task.structured_result,
        structured_output_status=task.structured_output_status,
        rejection_reason=task.rejection_reason,
    )


@router.get("/browsing/tasks/{task_id}/trajectory")
async def get_trajectory(task_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    task = await get_browsing_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "steps": task.trajectory or []}

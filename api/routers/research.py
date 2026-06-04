from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.db import get_db
from api.core.auth import get_current_key
from api.models.api_key import ApiKey
from api.schemas.research import ResearchTaskCreate, ResearchTaskResponse
from api.services.research import create_research_task, get_research_task

router = APIRouter()


@router.post("/research/tasks", response_model=ResearchTaskResponse)
async def create_task(data: ResearchTaskCreate, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    task = await create_research_task(db, data, key.id)
    from api.workers.research import run_research_task
    run_research_task.delay(task.id)
    return ResearchTaskResponse(task_id=task.id, status=task.status, mode=task.mode, view_url=task.view_url)


@router.get("/research/tasks/{task_id}", response_model=ResearchTaskResponse)
async def get_task(task_id: str, key: ApiKey = Depends(get_current_key), db: AsyncSession = Depends(get_db)):
    task = await get_research_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ResearchTaskResponse(
        task_id=task.id, status=task.status, result=task.result,
        structured_result=task.structured_result,
        structured_output_status=task.structured_output_status,
        view_url=task.view_url, mode=task.mode,
    )

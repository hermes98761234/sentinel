from fastapi import APIRouter, Depends
from api.core.auth import get_current_key
from api.models.api_key import ApiKey

router = APIRouter()


@router.get("/usage")
async def get_usage(key: ApiKey = Depends(get_current_key)):
    return {
        "num_active_scouts": 0,
        "active_scout_ids": [],
        "rate_limits": {"status": "available"},
        "navigator_rate_limits": {"status": "available"},
        "activity": {"scout_runs": 0, "browsing_tasks": 0, "research_tasks": 0, "navigator_calls": 0},
    }

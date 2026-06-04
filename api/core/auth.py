from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.db import get_db
from api.services.auth import validate_api_key
from api.models.api_key import ApiKey

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_key(
    bearer=Security(bearer_scheme),
    x_api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    raw_key = None
    if bearer:
        raw_key = bearer.credentials
    elif x_api_key:
        raw_key = x_api_key
    if not raw_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    key = await validate_api_key(db, raw_key)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


async def bearer_only_key(
    bearer=Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    if not bearer:
        raise HTTPException(status_code=401, detail="Bearer token required")
    key = await validate_api_key(db, bearer.credentials)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key

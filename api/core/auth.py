import hashlib
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.core.db import get_db, AsyncSessionLocal
from api.models.api_key import ApiKey


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def get_current_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    token = None
    # Check X-API-Key header first, then Authorization: Bearer
    x_api_key = request.headers.get("X-API-Key")
    if x_api_key:
        token = x_api_key
    else:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    token_hash = _hash_key(token)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == token_hash))
    key = result.scalar_one_or_none()
    if not key or not key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )
    return key


async def bearer_only_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )
    token = auth.removeprefix("Bearer ").strip()
    token_hash = _hash_key(token)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == token_hash))
    key = result.scalar_one_or_none()
    if not key or not key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )
    return key

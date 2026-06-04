import hashlib
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from api.models.api_key import ApiKey


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(db: AsyncSession, owner: str) -> str:
    raw_key = "sk-" + secrets.token_urlsafe(32)
    key = ApiKey(key_hash=_hash_key(raw_key), owner=owner)
    db.add(key)
    await db.commit()
    return raw_key


async def validate_api_key(db: AsyncSession, raw_key: str) -> ApiKey | None:
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == _hash_key(raw_key), ApiKey.is_active == True)
    )
    key = result.scalar_one_or_none()
    if key:
        await db.execute(
            update(ApiKey).where(ApiKey.id == key.id).values(last_used_at=datetime.now(timezone.utc))
        )
        await db.commit()
    return key

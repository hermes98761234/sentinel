from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.core.db import engine, Base
from api.routers import health, navigator, browsing, research, scouting, usage, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Sentinel API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router, prefix="/v1")
app.include_router(navigator.router, prefix="/v1")
app.include_router(browsing.router, prefix="/v1")
app.include_router(research.router, prefix="/v1")
app.include_router(scouting.router, prefix="/v1")
app.include_router(usage.router, prefix="/v1")
app.include_router(webhooks.router, prefix="/v1")

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from main import app
from api.core.db import Base, get_db
from api.models.api_key import ApiKey

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_browsing.db"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncSessionLocal() as session:
        session.add(ApiKey(id="key-1", key="test-api-key-12345", name="test", is_active=True))
        await session.commit()

    yield

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_browsing_task():
    with patch("api.routers.browsing.run_browsing_task.delay"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/v1/browsing/tasks",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={"task": "Find the main heading", "start_url": "https://example.com"}
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert "task_id" in data


@pytest.mark.asyncio
async def test_get_browsing_task():
    with patch("api.routers.browsing.run_browsing_task.delay"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/v1/browsing/tasks",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={"task": "Find heading", "start_url": "https://example.com"}
            )
            task_id = create_resp.json()["task_id"]
            get_resp = await client.get(f"/v1/browsing/tasks/{task_id}", headers={"Authorization": "Bearer test-api-key-12345"})
    assert get_resp.status_code == 200
    assert get_resp.json()["task_id"] == task_id


@pytest.mark.asyncio
async def test_get_browsing_trajectory():
    with patch("api.routers.browsing.run_browsing_task.delay"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/v1/browsing/tasks",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={"task": "Find heading", "start_url": "https://example.com"}
            )
            task_id = create_resp.json()["task_id"]
            traj_resp = await client.get(f"/v1/browsing/tasks/{task_id}/trajectory", headers={"Authorization": "Bearer test-api-key-12345"})
    assert traj_resp.status_code == 200
    assert "steps" in traj_resp.json()

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_create_browsing_task(valid_api_key):
    with patch("api.workers.browsing.run_browsing_task.delay"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/v1/browsing/tasks",
                headers={"X-API-Key": valid_api_key},
                json={"task": "Find the main heading", "start_url": "https://example.com"}
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert "task_id" in data

@pytest.mark.asyncio
async def test_get_browsing_task(valid_api_key):
    with patch("api.workers.browsing.run_browsing_task.delay"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/v1/browsing/tasks",
                headers={"X-API-Key": valid_api_key},
                json={"task": "Find heading", "start_url": "https://example.com"}
            )
            task_id = create_resp.json()["task_id"]
            get_resp = await client.get(f"/v1/browsing/tasks/{task_id}", headers={"X-API-Key": valid_api_key})
    assert get_resp.status_code == 200
    assert get_resp.json()["task_id"] == task_id

@pytest.mark.asyncio
async def test_get_browsing_trajectory(valid_api_key):
    with patch("api.workers.browsing.run_browsing_task.delay"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/v1/browsing/tasks",
                headers={"X-API-Key": valid_api_key},
                json={"task": "Find heading", "start_url": "https://example.com"}
            )
            task_id = create_resp.json()["task_id"]
            traj_resp = await client.get(f"/v1/browsing/tasks/{task_id}/trajectory", headers={"X-API-Key": valid_api_key})
    assert traj_resp.status_code == 200
    assert "steps" in traj_resp.json()

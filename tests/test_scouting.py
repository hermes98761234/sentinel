import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_create_scout(valid_api_key):
    with patch("api.workers.scouting.schedule_scout"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/v1/scouting/tasks",
                headers={"X-API-Key": valid_api_key},
                json={"query": "Monitor AI news", "output_interval": 3600}
            )
    assert resp.status_code == 200
    assert "id" in resp.json()


@pytest.mark.asyncio
async def test_list_scouts(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/scouting/tasks", headers={"X-API-Key": valid_api_key})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_scout(valid_api_key):
    with patch("api.workers.scouting.schedule_scout"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            scout_id = (await client.post("/v1/scouting/tasks", headers={"X-API-Key": valid_api_key}, json={"query": "Monitor prices"})).json()["id"]
            resp = await client.get(f"/v1/scouting/tasks/{scout_id}", headers={"X-API-Key": valid_api_key})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_pause_resume_scout(valid_api_key):
    with patch("api.workers.scouting.schedule_scout"), patch("api.workers.scouting.unschedule_scout"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            scout_id = (await client.post("/v1/scouting/tasks", headers={"X-API-Key": valid_api_key}, json={"query": "test"})).json()["id"]
            assert (await client.post(f"/v1/scouting/tasks/{scout_id}/pause", headers={"X-API-Key": valid_api_key})).status_code == 200
            assert (await client.post(f"/v1/scouting/tasks/{scout_id}/resume", headers={"X-API-Key": valid_api_key})).status_code == 200


@pytest.mark.asyncio
async def test_get_scout_updates(valid_api_key):
    with patch("api.workers.scouting.schedule_scout"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            scout_id = (await client.post("/v1/scouting/tasks", headers={"X-API-Key": valid_api_key}, json={"query": "test"})).json()["id"]
            resp = await client.get(f"/v1/scouting/tasks/{scout_id}/updates", headers={"X-API-Key": valid_api_key})
    assert resp.status_code == 200
    assert "updates" in resp.json()

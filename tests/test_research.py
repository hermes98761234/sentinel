import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app
from api.core.auth import get_current_key


@pytest.mark.asyncio
async def test_create_research_task(valid_api_key):
    mock_key = MagicMock()
    mock_key.id = "test-key-id"

    async def override_get_current_key():
        return mock_key

    app.dependency_overrides[get_current_key] = override_get_current_key
    try:
        with patch("api.workers.research.run_research_task.delay"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/v1/research/tasks",
                    headers={"Authorization": f"Bearer {valid_api_key}"},
                    json={"query": "What is the latest news on AI?"}
                )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert "task_id" in data
    finally:
        del app.dependency_overrides[get_current_key]


@pytest.mark.asyncio
async def test_get_research_task(valid_api_key):
    mock_key = MagicMock()
    mock_key.id = "test-key-id"

    async def override_get_current_key():
        return mock_key

    app.dependency_overrides[get_current_key] = override_get_current_key
    try:
        with patch("api.workers.research.run_research_task.delay"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                create_resp = await client.post("/v1/research/tasks",
                    headers={"Authorization": f"Bearer {valid_api_key}"},
                    json={"query": "AI news"}
                )
                task_id = create_resp.json()["task_id"]
                get_resp = await client.get(f"/v1/research/tasks/{task_id}", headers={"Authorization": f"Bearer {valid_api_key}"})
        assert get_resp.status_code == 200
        assert get_resp.json()["task_id"] == task_id
    finally:
        del app.dependency_overrides[get_current_key]

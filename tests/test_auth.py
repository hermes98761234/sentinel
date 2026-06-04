import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_no_key():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_protected_requires_key():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/usage")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_bearer_token_accepted(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/usage", headers={"Authorization": f"Bearer {valid_api_key}"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_x_api_key_accepted(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/usage", headers={"X-API-Key": valid_api_key})
    assert resp.status_code == 200

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_create_webhook(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["browsing.completed", "research.completed"],
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "Test Webhook"
    assert data["url"] == "https://example.com/webhook"
    assert len(data["secret"]) > 0
    assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_list_webhooks(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create two webhooks
        resp1 = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Webhook A",
                "url": "https://example.com/a",
                "events": ["browsing.completed"],
            },
        )
        assert resp1.status_code == 201
        id1 = resp1.json()["id"]

        resp2 = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Webhook B",
                "url": "https://example.com/b",
                "events": ["research.completed"],
            },
        )
        assert resp2.status_code == 201
        id2 = resp2.json()["id"]

        # List and verify both are returned
        list_resp = await client.get("/v1/webhooks", headers={"X-API-Key": valid_api_key})
    assert list_resp.status_code == 200
    data = list_resp.json()
    ids = [w["id"] for w in data]
    assert id1 in ids
    assert id2 in ids


@pytest.mark.asyncio
async def test_get_webhook(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Get Test",
                "url": "https://example.com/get",
                "events": ["browsing.completed"],
            },
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        endpoint_id = created["id"]

        get_resp = await client.get(
            f"/v1/webhooks/{endpoint_id}", headers={"X-API-Key": valid_api_key}
        )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == endpoint_id
    assert data["name"] == "Get Test"
    assert data["url"] == "https://example.com/get"


@pytest.mark.asyncio
async def test_get_webhook_not_found(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/v1/webhooks/nonexistent", headers={"X-API-Key": valid_api_key}
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_webhook(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Update Test",
                "url": "https://example.com/update",
                "events": ["browsing.completed"],
            },
        )
        assert create_resp.status_code == 201
        endpoint_id = create_resp.json()["id"]

        patch_resp = await client.patch(
            f"/v1/webhooks/{endpoint_id}",
            headers={"X-API-Key": valid_api_key},
            json={"name": "Updated Name", "is_active": False},
        )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_webhook(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Delete Test",
                "url": "https://example.com/delete",
                "events": ["browsing.completed"],
            },
        )
        assert create_resp.status_code == 201
        endpoint_id = create_resp.json()["id"]

        delete_resp = await client.delete(
            f"/v1/webhooks/{endpoint_id}", headers={"X-API-Key": valid_api_key}
        )
        assert delete_resp.status_code == 204

        get_resp = await client.get(
            f"/v1/webhooks/{endpoint_id}", headers={"X-API-Key": valid_api_key}
        )
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_webhook_invalid_event(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Invalid Event",
                "url": "https://example.com/invalid",
                "events": ["invalid.event"],
            },
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delivery_history_empty(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/v1/webhooks",
            headers={"X-API-Key": valid_api_key},
            json={
                "name": "Delivery History Test",
                "url": "https://example.com/deliveries",
                "events": ["browsing.completed"],
            },
        )
        assert create_resp.status_code == 201
        endpoint_id = create_resp.json()["id"]

        del_resp = await client.get(
            f"/v1/webhooks/{endpoint_id}/deliveries",
            headers={"X-API-Key": valid_api_key},
        )
    assert del_resp.status_code == 200
    assert del_resp.json() == []


@pytest.mark.asyncio
async def test_retry_delivery_not_found(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/webhooks/deliveries/nonexistent/retry",
            headers={"X-API-Key": valid_api_key},
        )
    assert resp.status_code == 404

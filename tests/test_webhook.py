import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.webhook import fire_webhook, format_payload


def test_format_sentinel():
    payload = format_payload("sentinel", {"id": "abc", "status": "succeeded", "result": "done"})
    assert payload["id"] == "abc"
    assert payload["status"] == "succeeded"


def test_format_slack():
    payload = format_payload("slack", {"id": "abc", "status": "succeeded", "result": "done"})
    assert "text" in payload
    assert "succeeded" in payload["text"]


def test_format_zapier():
    payload = format_payload("zapier", {"id": "abc", "status": "succeeded", "result": "done"})
    assert payload["id"] == "abc"
    assert "status" in payload


@pytest.mark.asyncio
async def test_fire_webhook_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await fire_webhook("https://example.com/hook", "sentinel", {"id": "1", "status": "succeeded"})
        assert mock_post.called

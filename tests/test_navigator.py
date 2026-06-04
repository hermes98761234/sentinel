import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from main import app

MOCK_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "I'll click the button.",
            "tool_calls": [{
                "id": "tool-1",
                "type": "function",
                "function": {"name": "left_click", "arguments": "{\"coordinates\": [500, 300]}"}
            }]
        },
        "finish_reason": "tool_calls"
    }],
    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
}


@pytest.mark.asyncio
async def test_navigator_requires_bearer(valid_api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/v1/chat/completions",
            headers={"X-API-Key": valid_api_key},
            json={"model": "n1.5-latest", "messages": [{"role": "user", "content": "click"}]}
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_navigator_chat_completion(valid_api_key):
    with patch("api.core.openrouter.OpenRouterClient.chat_completions", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = MOCK_RESPONSE
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/v1/chat/completions",
                headers={"Authorization": f"Bearer {valid_api_key}"},
                json={"model": "n1.5-latest", "messages": [{"role": "user", "content": "click the button"}]}
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["choices"][0]["message"]["role"] == "assistant"

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


def format_payload(webhook_format: str, data: dict) -> dict:
    if webhook_format == "slack":
        status = data.get("status", "unknown")
        result = data.get("result", "") or data.get("content", "")
        return {
            "text": f"Sentinel task {status}: {result[:200] if result else '(no result)'}",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Status:* {status}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": result[:500] if result else "(no result)"}},
            ],
        }
    if webhook_format == "zapier":
        return {k: str(v) if v is not None else "" for k, v in data.items()}
    return data


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fire_webhook(url: str, webhook_format: str, data: dict) -> None:
    payload = format_payload(webhook_format, data)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()

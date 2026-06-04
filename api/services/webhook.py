import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from api.models.webhook import WebhookDelivery, WebhookEndpoint


def format_payload(webhook_format: str, data: dict) -> dict:
    if webhook_format == "slack":
        status = data.get("status", "unknown")
        result = data.get("result", "") or data.get("content", "")
        return {
            "text": f"Sentinel event {status}: {result[:200] if result else '(no result)'}",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Status:* {status}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": result[:500] if result else "(no result)"}},
            ],
        }
    if webhook_format == "zapier":
        return {k: str(v) if v is not None else "" for k, v in data.items()}
    return data


def sign_payload(secret: str, payload_bytes: bytes) -> str:
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fire_webhook(url: str, webhook_format: str, data: dict, secret: str | None = None) -> tuple[int, str]:
    payload = format_payload(webhook_format, data)
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Sentinel-Signature"] = f"sha256={sign_payload(secret, body)}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, content=body, headers=headers)
        resp.raise_for_status()
        return resp.status_code, resp.text[:2000]


async def dispatch_event(db: AsyncSession, event_type: str, payload: dict) -> None:
    """Fire event to all active registered endpoints subscribed to this event type."""
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.is_active == True,
            WebhookEndpoint.events.contains([event_type]),
        )
    )
    endpoints = result.scalars().all()
    for endpoint in endpoints:
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            endpoint_id=endpoint.id,
            event_type=event_type,
            payload=payload,
            status="pending",
        )
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        try:
            status_code, body = await fire_webhook(
                endpoint.url, endpoint.webhook_format, payload, endpoint.secret
            )
            delivery.status = "delivered"
            delivery.response_status = status_code
            delivery.response_body = body
        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)[:2000]
        delivery.attempts += 1
        delivery.last_attempt_at = datetime.now(timezone.utc)
        await db.commit()

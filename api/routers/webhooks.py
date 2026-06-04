import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.auth import get_current_key
from api.core.db import get_db
from api.models.api_key import ApiKey
from api.models.webhook import WebhookDelivery, WebhookEndpoint
from api.schemas.webhooks import (
    WebhookDeliveryResponse,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEndpointUpdate,
)
from api.services.webhook import fire_webhook

router = APIRouter()


def _serialize_endpoint(e: WebhookEndpoint) -> WebhookEndpointResponse:
    return WebhookEndpointResponse(
        id=e.id,
        name=e.name,
        url=e.url,
        secret=e.secret,
        events=e.events or [],
        is_active=e.is_active,
        webhook_format=e.webhook_format,
        created_at=e.created_at.isoformat() if e.created_at else "",
    )


def _serialize_delivery(d: WebhookDelivery) -> WebhookDeliveryResponse:
    return WebhookDeliveryResponse(
        id=d.id,
        endpoint_id=d.endpoint_id,
        event_type=d.event_type,
        status=d.status,
        attempts=d.attempts,
        last_attempt_at=d.last_attempt_at.isoformat() if d.last_attempt_at else None,
        response_status=d.response_status,
        created_at=d.created_at.isoformat() if d.created_at else "",
    )


@router.post("/webhooks", response_model=WebhookEndpointResponse, status_code=201)
async def create_webhook(
    data: WebhookEndpointCreate,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    endpoint = WebhookEndpoint(
        id=str(uuid.uuid4()),
        api_key_id=key.id,
        name=data.name,
        url=data.url,
        events=data.events,
        webhook_format=data.webhook_format,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return _serialize_endpoint(endpoint)


@router.get("/webhooks", response_model=list[WebhookEndpointResponse])
async def list_webhooks(
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.api_key_id == key.id)
    )
    return [_serialize_endpoint(e) for e in result.scalars().all()]


@router.get("/webhooks/{endpoint_id}", response_model=WebhookEndpointResponse)
async def get_webhook(
    endpoint_id: str,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.api_key_id == key.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return _serialize_endpoint(endpoint)


@router.patch("/webhooks/{endpoint_id}", response_model=WebhookEndpointResponse)
async def update_webhook(
    endpoint_id: str,
    data: WebhookEndpointUpdate,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.api_key_id == key.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(endpoint, field, value)
    endpoint.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(endpoint)
    return _serialize_endpoint(endpoint)


@router.delete("/webhooks/{endpoint_id}", status_code=204)
async def delete_webhook(
    endpoint_id: str,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.api_key_id == key.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(endpoint)
    await db.commit()


@router.post("/webhooks/{endpoint_id}/test", status_code=200)
async def test_webhook(
    endpoint_id: str,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.api_key_id == key.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    test_payload = {
        "event": "test",
        "endpoint_id": endpoint_id,
        "message": "This is a test delivery from Sentinel.",
    }
    try:
        status_code, body = await fire_webhook(
            endpoint.url, endpoint.webhook_format, test_payload, endpoint.secret
        )
        return {"success": True, "status_code": status_code}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Delivery failed: {e}")


@router.get("/webhooks/{endpoint_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_deliveries(
    endpoint_id: str,
    limit: int = 50,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    ep_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.api_key_id == key.id,
        )
    )
    if not ep_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Webhook not found")
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.endpoint_id == endpoint_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(limit)
    )
    return [_serialize_delivery(d) for d in result.scalars().all()]


@router.post("/webhooks/deliveries/{delivery_id}/retry", status_code=200)
async def retry_delivery(
    delivery_id: str,
    key: ApiKey = Depends(get_current_key),
    db: AsyncSession = Depends(get_db),
):
    d_result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = d_result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    ep_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == delivery.endpoint_id,
            WebhookEndpoint.api_key_id == key.id,
        )
    )
    endpoint = ep_result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    try:
        status_code, body = await fire_webhook(
            endpoint.url, endpoint.webhook_format, delivery.payload, endpoint.secret
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
    return {"success": delivery.status == "delivered", "status": delivery.status}

import httpx
from api.core.config import settings

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODEL_ALIASES = {
    "n1.5-latest": settings.sentinel_vision_model,
    "n1.5-20260428": settings.sentinel_vision_model,
    "n1-latest": settings.sentinel_vision_model,
}


class OpenRouterClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.sentinel_api_base_url,
        }

    def _resolve_model(self, model: str) -> str:
        return MODEL_ALIASES.get(model, model)

    async def chat_completions(self, payload: dict) -> dict:
        payload = dict(payload)
        payload["model"] = self._resolve_model(payload.get("model", settings.sentinel_vision_model))
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()


openrouter_client = OpenRouterClient()

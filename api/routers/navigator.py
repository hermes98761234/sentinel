from fastapi import APIRouter, Depends, HTTPException
from api.schemas.navigator import ChatCompletionRequest
from api.core.auth import bearer_only_key
from api.core.openrouter import openrouter_client
from api.models.api_key import ApiKey

router = APIRouter()


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    key: ApiKey = Depends(bearer_only_key),
):
    payload = request.model_dump(exclude_none=True)
    payload.pop("tool_set", None)
    payload.pop("disable_tools", None)
    payload.pop("json_schema", None)
    try:
        return await openrouter_client.chat_completions(payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenRouter error: {str(e)}")

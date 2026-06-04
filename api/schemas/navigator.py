from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str | list | None = None
    tool_calls: list | None = None
    tool_call_id: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str = "n1.5-latest"
    messages: list[Message]
    max_completion_tokens: int = 1572
    temperature: float = 0.3
    tools: list[dict] | None = None
    tool_choice: str | None = "auto"
    tool_set: str | None = None
    disable_tools: list[str] | None = None
    json_schema: dict | None = None
    stream: bool = False

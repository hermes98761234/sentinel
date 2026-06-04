from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    sentinel_vision_model: str = "openrouter/anthropic/claude-sonnet-4"
    sentinel_api_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite+aiosqlite:///./sentinel.db"

    class Config:
        env_prefix = ""
        env_file = ".env"


settings = Settings()

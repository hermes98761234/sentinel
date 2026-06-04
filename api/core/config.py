from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"
    redis_url: str = "redis://localhost:6379/0"
    openrouter_api_key: str = ""
    sentinel_vision_model: str = "meta-llama/llama-3.2-11b-vision-instruct:free"
    sentinel_default_model: str = "google/gemma-3-27b-it:free"
    sentinel_api_base_url: str = "http://localhost:8000"
    secret_key: str = "changeme"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Recruiting Agent"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/recruiting_agent"
    database_url_sync: str = "postgresql+psycopg://postgres:postgres@localhost:5432/recruiting_agent"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "models/gemini-embedding-2"

    # Tavily
    tavily_api_key: str = ""

    # Search provider (tavily | serpapi | duckduckgo)
    search_provider: str = "tavily"

    # Agent settings
    max_research_depth: int = 3
    max_tokens_per_call: int = 4096
    agent_timeout_seconds: int = 120

    # Vector search
    embedding_dimensions: int = 3072
    similarity_top_k: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

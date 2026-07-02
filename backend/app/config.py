from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Global Equity Council"
    database_url: str = "sqlite:///./global_equity_council.db"
    data_provider: str = "fixture"
    market_data_api_key: str | None = None
    twelvedata_api_key: str | None = None
    finnhub_api_key: str | None = None
    market_data_cache_ttl_seconds: int = 900
    llm_provider: str = "demo"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    sec_user_agent: str = "GlobalEquityCouncil/1.0 contact@example.com"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    frontend_dist: str = "/app/frontend-dist"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

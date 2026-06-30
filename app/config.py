"""Uygulama yapılandırması — .env'den pydantic Settings ile okunur."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_vision_model: str = "gpt-4o"
    openai_embed_model: str = "text-embedding-3-small"

    # Gemini (Ebced / ilm-i hurûf yorumu)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # RevenueCat
    revenuecat_webhook_secret: str = ""

    # App
    env: str = "dev"
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

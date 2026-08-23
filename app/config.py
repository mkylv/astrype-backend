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
    # gpt-5.6-luna: reasoning modeli — en derin/akıllı yorumlar. Uzun okumalar
    # ~60s (LyraProgress zamanlayıcısı gösterir), kısa sohbet ~2s. Client
    # temperature GÖNDERMEZ (yalnız default 1) + max_completion_tokens verir
    # (bkz. openai_client._model_kwargs). Vision (sembol çıkarımı) gpt-4o'da kalır.
    openai_chat_model: str = "gpt-5.6-luna"
    openai_vision_model: str = "gpt-4o"
    openai_embed_model: str = "text-embedding-3-small"

    # Gemini (Ebced / ilm-i hurûf yorumu)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # RevenueCat
    revenuecat_webhook_secret: str = ""

    # Coin ekonomisi ("Yıldız Tozu"). Kapalıyken erişim kapıları no-op'tur:
    # hiçbir okuma ücretlendirilmez (mevcut davranış korunur). Flutter mağazası +
    # RevenueCat dashboard ürünleri hazır olunca Render env'inde 'true' yapılır.
    coins_enabled: bool = False

    # App
    env: str = "dev"
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

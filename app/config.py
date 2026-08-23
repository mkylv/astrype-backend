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
    # gpt-4.1: gpt-4o'ya göre ~4× daha uzun/derin yorum üretir ve uzunluk
    # talimatlarını (natal 4-5 paragraf/bölüm) çok daha iyi izler; token başına
    # daha ucuz. Sohbet kısa kalır çünkü CHAT prompt'u kısalık ister ve gpt-4.1
    # talimata sadıktır.
    openai_chat_model: str = "gpt-4.1"
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

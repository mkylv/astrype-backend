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

    # AI zaman aşımı / retry bütçesi (saniye). Takılan bir istek dakikalarca
    # asılı kalmasın diye her katman sınırlıdır:
    #   - OpenAI SDK kendi retry'ı KAPALI (max_retries=0); retry tek yerde (tenacity).
    #   - Deneme başı okuma zaman aşımı: kısa çağrılar (sohbet/vision) AI_TIMEOUT,
    #     uzun JSON yorumları (natal ~80s Luna) AI_LONG_TIMEOUT.
    #   - Gemini fallback istek başı GEMINI_TIMEOUT.
    #   - Bir AI üretiminin TOPLAM tavanı (birincil + retry + fallback):
    #     AI_REQUEST_BUDGET (sohbet/vision) / AI_LONG_REQUEST_BUDGET (JSON yorum).
    #   - Tek HTTP isteğinin tüm AI çağrılarının toplam tavanı: AI_REQUEST_DEADLINE
    #     (ör. kahve falı: 3 vision + 1 yorum).
    ai_connect_timeout_seconds: float = 10.0
    ai_timeout_seconds: float = 60.0
    ai_long_timeout_seconds: float = 150.0
    gemini_timeout_seconds: float = 60.0
    ai_max_attempts: int = 2
    ai_request_budget_seconds: float = 120.0
    ai_long_request_budget_seconds: float = 270.0
    ai_request_deadline_seconds: float = 360.0

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

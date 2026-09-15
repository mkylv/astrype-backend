"""Astrype Backend — FastAPI app, router mount, CORS."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_chart,
    routes_chat,
    routes_coffee,
    routes_daily,
    routes_dream,
    routes_ebced,
    routes_face,
    routes_horoscope,
    routes_humandesign,
    routes_legal,
    routes_numerology,
    routes_palm,
    routes_planet,
    routes_profile,
    routes_readings,
    routes_relationship,
    routes_subconscious,
    routes_tarot,
    routes_wallet,
    routes_webhooks,
    routes_yildizname,
)
from app.config import get_settings
from app.services.ai.resilience import AIUnavailableError, request_deadline

settings = get_settings()

app = FastAPI(
    title="Astrype API",
    version="1.0.0",
    description="Astroloji + tarot + fal + Cosmic Memory AI asistanı backend'i.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AIRequestDeadlineMiddleware:
    """Her HTTP isteğine AI çağrıları için mutlak toplam tavan koyar
    (AI_REQUEST_DEADLINE). Birden çok AI çağrısı yapan uçlar (ör. kahve falı:
    3 vision + yorum) da bu süreyi paylaşır; AI dışı kodu etkilemez."""

    def __init__(self, app_):
        self.app = app_

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        with request_deadline(get_settings().ai_request_deadline_seconds):
            return await self.app(scope, receive, send)


app.add_middleware(AIRequestDeadlineMiddleware)


@app.exception_handler(AIUnavailableError)
async def _ai_unavailable_handler(_: Request, exc: AIUnavailableError):
    # Kısa, sızıntısız mesaj (sağlayıcı/URL/key detayı yok). Ücret düşülmez:
    # route'lar commit_charge'ı üretim BAŞARILI olduktan sonra çağırır.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.public_message}},
    )


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "env": settings.env}


for module in (
    routes_profile,
    routes_chart,
    routes_daily,
    routes_tarot,
    routes_coffee,
    routes_palm,
    routes_relationship,
    routes_chat,
    routes_horoscope,
    routes_numerology,
    routes_humandesign,
    routes_planet,
    routes_ebced,
    routes_face,
    routes_dream,
    routes_yildizname,
    routes_subconscious,
    routes_readings,
    routes_wallet,
    routes_legal,
    routes_webhooks,
):
    app.include_router(module.router)

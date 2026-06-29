"""Astrype Backend — FastAPI app, router mount, CORS."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_chart,
    routes_chat,
    routes_coffee,
    routes_daily,
    routes_humandesign,
    routes_numerology,
    routes_palm,
    routes_profile,
    routes_readings,
    routes_relationship,
    routes_tarot,
    routes_webhooks,
)
from app.config import get_settings

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
    routes_numerology,
    routes_humandesign,
    routes_readings,
    routes_webhooks,
):
    app.include_router(module.router)

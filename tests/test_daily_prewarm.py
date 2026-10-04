"""Günlük yorum: ön ısıtma + eşzamanlı istekler tek üretimi paylaşmalı.

Bugünün yorumu servis edilince yarınınki arka planda hazırlanır. Ön ısıtma
sürerken kullanıcı açarsa ikinci bir OpenAI üretimi başlamamalı.
"""
import asyncio
from datetime import date

from app.api import routes_daily


def test_prewarm_and_open_share_one_generation(monkeypatch):
    calls = []

    async def fake_generate(user_id, day):
        calls.append(day)
        await asyncio.sleep(0.05)
        return {"summary": "ok"}

    monkeypatch.setattr(routes_daily, "_generate_and_store", fake_generate)
    monkeypatch.setattr(routes_daily, "_cached", lambda sb, u, d: None)
    monkeypatch.setattr(routes_daily, "get_supabase", lambda: None)

    async def scenario():
        routes_daily._schedule_prewarm("u1", date(2026, 10, 4))
        await asyncio.sleep(0.01)  # ön ısıtma görevi başlasın
        r = await asyncio.shield(routes_daily._task("u1", "2026-10-05"))  # kullanıcı açtı
        await asyncio.sleep(0.01)
        return r

    assert asyncio.run(scenario()) == {"summary": "ok"}
    assert calls == ["2026-10-05"]
    assert not routes_daily._TASKS


def test_prewarm_skips_when_already_cached(monkeypatch):
    calls = []

    async def fake_generate(user_id, day):
        calls.append(day)
        return {}

    monkeypatch.setattr(routes_daily, "_generate_and_store", fake_generate)
    monkeypatch.setattr(routes_daily, "_cached", lambda sb, u, d: {"summary": "var"})
    monkeypatch.setattr(routes_daily, "get_supabase", lambda: None)

    asyncio.run(routes_daily._prewarm("u1", "2026-10-05"))
    assert calls == []


def test_prewarm_failure_is_silent(monkeypatch):
    async def boom(user_id, day):
        raise RuntimeError("openai down")

    monkeypatch.setattr(routes_daily, "_generate_and_store", boom)
    monkeypatch.setattr(routes_daily, "_cached", lambda sb, u, d: None)
    monkeypatch.setattr(routes_daily, "get_supabase", lambda: None)

    asyncio.run(routes_daily._prewarm("u1", "2026-10-05"))  # fırlatmamalı
    assert not routes_daily._TASKS

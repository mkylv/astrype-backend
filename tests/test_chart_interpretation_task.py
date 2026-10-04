"""Natal yorum üretimi harita başına TEK kez çalışmalı.

Kayıt anında arka planda başlayan üretim sürerken kullanıcı haritaya girerse
(/chart/interpret) ikinci bir ~80 sn'lik üretim başlamamalı; aynı işi beklemeli.
"""
import asyncio

from app.api import routes_chart


def test_concurrent_requests_share_one_generation(monkeypatch):
    calls = []

    async def fake_generate(user_id, chart_id, snap):
        calls.append(chart_id)
        await asyncio.sleep(0.05)
        return {"summary": "ok"}

    monkeypatch.setattr(routes_chart, "_generate_and_store_interpretation", fake_generate)

    async def scenario():
        t1 = routes_chart._interpretation_task("u1", "chart-1", {})  # kayıt anı (arka plan)
        t2 = routes_chart._interpretation_task("u1", "chart-1", {})  # kullanıcı haritaya girdi
        assert t1 is t2
        r1, r2 = await asyncio.gather(t1, asyncio.shield(t2))
        await asyncio.sleep(0)  # done callback çalışsın
        return r1, r2

    r1, r2 = asyncio.run(scenario())
    assert calls == ["chart-1"]
    assert r1 == r2 == {"summary": "ok"}
    assert "chart-1" not in routes_chart._INTERP_TASKS


def test_new_generation_after_previous_finished(monkeypatch):
    calls = []

    async def fake_generate(user_id, chart_id, snap):
        calls.append(chart_id)
        return None  # ör. AI hatası → tekrar denenebilmeli

    monkeypatch.setattr(routes_chart, "_generate_and_store_interpretation", fake_generate)

    async def scenario():
        await routes_chart._interpretation_task("u1", "chart-2", {})
        await asyncio.sleep(0)
        await routes_chart._interpretation_task("u1", "chart-2", {})

    asyncio.run(scenario())
    assert calls == ["chart-2", "chart-2"]

"""AI timeout / retry / fallback bütçesi — ağ gerektirmez."""
import asyncio
import time

import httpx
import pytest

from app.services.ai import resilience as r


def _run(coro):
    return asyncio.run(coro)


def test_success_path_untouched():
    async def primary():
        return {"ok": 1}

    async def fallback():  # pragma: no cover
        raise AssertionError("fallback çağrılmamalı")

    out = _run(r.with_fallback(primary, fallback, budget=5, fallback_reserve=1, label="t"))
    assert out == {"ok": 1}


def test_hanging_primary_falls_back_within_budget():
    async def primary():
        await asyncio.sleep(60)

    async def fallback():
        return "gemini"

    t0 = time.monotonic()
    out = _run(r.with_fallback(primary, fallback, budget=0.6, fallback_reserve=0.3, label="t"))
    assert out == "gemini"
    assert time.monotonic() - t0 < 1.0


def test_everything_hangs_hard_bound_504():
    async def hang():
        await asyncio.sleep(60)

    t0 = time.monotonic()
    with pytest.raises(r.AITimeoutError):
        _run(r.with_fallback(hang, hang, budget=0.5, fallback_reserve=0.2, label="t"))
    assert time.monotonic() - t0 < 1.0


def test_both_fail_fast_503():
    async def boom():
        raise r.ProviderHTTPError("X", 400)

    with pytest.raises(r.AIUnavailableError) as ei:
        _run(r.with_fallback(boom, boom, budget=5, fallback_reserve=1, label="t"))
    assert not isinstance(ei.value, r.AITimeoutError)
    assert ei.value.status_code == 503


def test_request_deadline_caps_budget():
    async def hang():
        await asyncio.sleep(60)

    async def main():
        with r.request_deadline(0.3):
            await r.with_fallback(hang, hang, budget=100, fallback_reserve=10, label="t")

    t0 = time.monotonic()
    with pytest.raises(r.AITimeoutError):
        _run(main())
    assert time.monotonic() - t0 < 0.8


def test_retry_only_on_transient():
    calls = {"n": 0}

    async def bad_request():
        calls["n"] += 1
        raise r.ProviderHTTPError("X", 401)

    with pytest.raises(r.ProviderHTTPError):
        _run(r.retry_transient(bad_request, attempts=3, max_delay=10))
    assert calls["n"] == 1  # 4xx asla tekrar denenmez

    calls["n"] = 0

    async def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("down")
        return "ok"

    assert _run(r.retry_transient(flaky, attempts=2, max_delay=10)) == "ok"
    assert calls["n"] == 2


def test_transient_classification():
    assert r.is_transient(r.ProviderHTTPError("X", 429))
    assert r.is_transient(r.ProviderHTTPError("X", 503))
    assert not r.is_transient(r.ProviderHTTPError("X", 400))
    assert r.is_transient(httpx.ReadTimeout("t"))
    assert not r.is_transient(ValueError("json"))


def test_gemini_key_not_in_url_or_errors(monkeypatch):
    from app.services.ai import gemini_client
    from app.config import get_settings

    secret = "SECRET-KEY-123"
    monkeypatch.setattr(get_settings(), "gemini_api_key", secret)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["header"] = request.headers.get("x-goog-api-key")
        return httpx.Response(500, json={"error": "x"})

    real = httpx.AsyncClient

    class _Client(real):
        def __init__(self, *a, **kw):
            kw["transport"] = httpx.MockTransport(handler)
            super().__init__(*a, **kw)

    monkeypatch.setattr(gemini_client.httpx, "AsyncClient", _Client)
    with pytest.raises(r.ProviderHTTPError) as ei:
        _run(gemini_client._generate({"contents": []}))
    assert secret not in seen["url"] and "key=" not in seen["url"]
    assert seen["header"] == secret
    assert secret not in str(ei.value)


def _mock_openai(monkeypatch, handler):
    from openai import AsyncOpenAI

    from app.services.ai import openai_client

    client = AsyncOpenAI(
        api_key="test", max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr(openai_client, "_get_client", lambda: client)
    return openai_client


def test_openai_json_success_and_no_retry_on_4xx(monkeypatch):
    calls = {"openai": 0, "gemini": 0}

    def ok(request):
        calls["openai"] += 1
        return httpx.Response(200, json={
            "id": "x", "object": "chat.completion", "created": 0, "model": "m",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": '{"summary": "hi"}'}}],
        })

    oc = _mock_openai(monkeypatch, ok)
    assert _run(oc.complete_json("sys", "ctx")) == {"summary": "hi"}
    assert calls["openai"] == 1

    def unauthorized(request):
        calls["openai"] += 1
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    async def fake_gemini(system, text):
        calls["gemini"] += 1
        return {"from": "gemini"}

    calls["openai"] = 0
    oc = _mock_openai(monkeypatch, unauthorized)
    monkeypatch.setattr(oc, "json_gemini_retrying", fake_gemini)
    assert _run(oc.complete_json("sys", "ctx")) == {"from": "gemini"}
    assert calls == {"openai": 1, "gemini": 1}


def test_exception_handler_maps_to_504():
    from fastapi.testclient import TestClient

    from app.main import app

    @app.get("/__test_ai_timeout")
    async def _boom():
        raise r.AITimeoutError()

    try:
        res = TestClient(app).get("/__test_ai_timeout")
        assert res.status_code == 504
        assert res.json()["detail"]["code"] == "AI_TIMEOUT"
    finally:
        app.router.routes = [x for x in app.router.routes
                             if getattr(x, "path", "") != "/__test_ai_timeout"]

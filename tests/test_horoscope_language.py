"""Genel burç yorumları dile göre üretilir ve dile göre cache'lenir."""
from fastapi.testclient import TestClient

from app.api import routes_horoscope as rh
from app.deps import CurrentUser, current_user
from app.main import app


def _setup(monkeypatch, langs):
    calls = []

    async def fake_complete(prompt, context):
        calls.append(context)
        return {"title": f"t{len(calls)}", "overview": "o"}

    monkeypatch.setattr(rh, "get_supabase", lambda: object())
    monkeypatch.setattr(rh, "get_profile", lambda sb, uid: {"language": langs[uid], "birth_date": "1995-03-11"})
    monkeypatch.setattr(rh, "complete_json", fake_complete)
    monkeypatch.setattr(rh.wallet, "check_access", lambda *a, **k: None)
    monkeypatch.setattr(rh.wallet, "commit_charge", lambda *a, **k: {"charged": False})
    rh._monthly_cache.clear()
    rh._daily_cache.clear()
    return calls


def _get(path, uid):
    app.dependency_overrides[current_user] = lambda: CurrentUser(id=uid)
    try:
        return TestClient(app).get(path)
    finally:
        app.dependency_overrides.pop(current_user, None)


def test_monthly_cached_per_language(monkeypatch):
    calls = _setup(monkeypatch, {"u-en": "en", "u-tr": "tr", "u-en2": "en"})
    a = _get("/horoscope/monthly?sign=pisces", "u-en").json()
    b = _get("/horoscope/monthly?sign=pisces", "u-tr").json()
    c = _get("/horoscope/monthly?sign=pisces", "u-en2").json()
    assert len(calls) == 2  # en + tr; ikinci İngilizce kullanıcı cache'ten
    assert "English" in calls[0] and "Türkçe" in calls[1]
    assert a["content"] == c["content"] != b["content"]


def test_daily_includes_language(monkeypatch):
    calls = _setup(monkeypatch, {"u-de": "de"})
    _get("/horoscope/daily?sign=leo", "u-de")
    assert "Deutsch" in calls[0]

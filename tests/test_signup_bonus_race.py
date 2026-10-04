"""Yeni kullanıcı cüzdanı açılmadan ücretli bir özelliğe istek atınca 402 almamalı.

Gerçek olay (2026-10-04, App Review videosu): yeni hesabın ana ekranı günlük
yorumu GET /wallet'tan önce istedi; kayıt hediyesi henüz verilmediği için bakiye
0 görüldü ve kullanıcı ilk ekranda hata gördü.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import wallet


@pytest.fixture
def paid_feature(monkeypatch):
    monkeypatch.setattr(wallet, "get_settings", lambda: SimpleNamespace(coins_enabled=True))
    monkeypatch.setattr(wallet, "feature_price", lambda sb, f: (8, "continuous"))
    monkeypatch.setattr(wallet, "_subscription_row", lambda sb, uid: None)
    monkeypatch.setattr(wallet, "_already_unlocked", lambda sb, key: False)
    monkeypatch.setattr(wallet, "get_balance", lambda sb, uid: 0)


def test_new_user_gets_signup_bonus_before_first_paid_request(paid_feature, monkeypatch):
    calls = []
    monkeypatch.setattr(wallet, "ensure_signup_bonus",
                        lambda sb, uid: calls.append(uid) or 200)
    access = wallet.check_access(object(), "new-user", "daily_map", unlock_key="k")
    assert calls == ["new-user"]
    assert access.balance == 200


def test_user_who_spent_bonus_still_gets_402(paid_feature, monkeypatch):
    # Hediye zaten verilmiş ve harcanmış: idempotent çağrı mevcut bakiyeyi döner.
    monkeypatch.setattr(wallet, "ensure_signup_bonus", lambda sb, uid: 3)
    with pytest.raises(HTTPException) as e:
        wallet.check_access(object(), "spent-user", "daily_map", unlock_key="k")
    assert e.value.status_code == 402
    assert e.value.detail["code"] == "INSUFFICIENT_COINS"


def test_sufficient_balance_does_not_touch_bonus(monkeypatch, paid_feature):
    monkeypatch.setattr(wallet, "get_balance", lambda sb, uid: 500)

    def boom(*_):
        raise AssertionError("mutlu yolda hediye sorgusu yapılmamalı")

    monkeypatch.setattr(wallet, "ensure_signup_bonus", boom)
    access = wallet.check_access(object(), "rich-user", "daily_map", unlock_key="k")
    assert access.balance == 500

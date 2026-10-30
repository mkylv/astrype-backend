"""Stripe web ödemeleri — ağ yok; imza gerçek HMAC ile, Supabase sahte."""
import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import routes_billing
from app.config import get_settings
from app.deps import CurrentUser, current_user
from app.main import app
from app.services import wallet
from app.services.subscription import stripe_billing as sbb

USER = "00000000-0000-0000-0000-0000000000aa"
WHSEC = "whsec_test_secret"


@pytest.fixture
def enabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "stripe_enabled", True)
    monkeypatch.setattr(s, "stripe_secret_key", "sk_test_dummy")
    monkeypatch.setattr(s, "stripe_webhook_secret", WHSEC)
    return s


def _sig(payload: bytes, secret=WHSEC) -> str:
    ts = int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


class FakeSB:
    def __init__(self, first_done=False):
        self.first_done = first_done
        self.upserts, self.updates = [], []

    def table(self, name):
        sb = self

        class Q:
            def select(self, *_):
                return self

            def eq(self, *_):
                return self

            def limit(self, *_):
                return self

            def update(self, row):
                sb.updates.append((name, row))
                return self

            def upsert(self, row, **_):
                sb.upserts.append((name, row))
                return self

            def execute(self):
                return MagicMock(data=[{"first_purchase_done": sb.first_done}] if name == "wallets" else [])

        return Q()


def test_session_params_pack_and_sub():
    p = sbb.build_session_params(USER, "a@b.c", "astrype_coins_650", "https://astrype.com/en/app/wallet?paid=1", "https://astrype.com/en/app/wallet")
    assert p["mode"] == "payment" and p["line_items"][0]["price_data"]["unit_amount"] == 999
    assert p["metadata"] == {"user_id": USER, "product_id": "astrype_coins_650"}
    s = sbb.build_session_params(USER, None, "astrype_sub_yearly", "https://astrype.com/x", "https://astrype.com/y")
    assert s["mode"] == "subscription"
    assert s["line_items"][0]["price_data"]["recurring"]["interval"] == "year"
    assert s["subscription_data"]["trial_period_days"] == 3


@pytest.mark.parametrize("bad", ["https://evil.example/x", "javascript:alert(1)", "//astrype.com.evil/x"])
def test_open_redirect_rejected(bad):
    with pytest.raises(sbb.BillingInputError):
        sbb.build_session_params(USER, None, "astrype_coins_100", bad, "https://astrype.com/y")


def test_unknown_product_rejected():
    with pytest.raises(sbb.BillingInputError):
        sbb.build_session_params(USER, None, "free_money", "https://astrype.com/x", "https://astrype.com/y")


def test_checkout_disabled_is_503(monkeypatch):
    monkeypatch.setattr(get_settings(), "stripe_enabled", False)
    app.dependency_overrides[current_user] = lambda: CurrentUser(id=USER)
    try:
        r = TestClient(app).post("/billing/checkout", json={"product_id": "astrype_coins_100", "success_url": "https://astrype.com/a", "cancel_url": "https://astrype.com/b"})
    finally:
        app.dependency_overrides.pop(current_user, None)
    assert r.status_code == 503


def test_checkout_creates_session(enabled, monkeypatch):
    fake = MagicMock()
    fake.checkout.Session.create.return_value = {"url": "https://checkout.stripe.com/c/pay/cs_test_1"}
    monkeypatch.setattr(sbb, "_stripe", lambda: fake)
    app.dependency_overrides[current_user] = lambda: CurrentUser(id=USER, email="a@b.c")
    try:
        r = TestClient(app).post("/billing/checkout", json={"product_id": "astrype_coins_300", "success_url": "http://localhost:3000/en/app/wallet?paid=1", "cancel_url": "http://localhost:3000/en/app/wallet"})
    finally:
        app.dependency_overrides.pop(current_user, None)
    assert r.status_code == 200 and r.json()["url"].startswith("https://checkout.stripe.com/")
    kwargs = fake.checkout.Session.create.call_args.kwargs
    assert kwargs["client_reference_id"] == USER and kwargs["customer_email"] == "a@b.c"


def test_webhook_rejects_bad_signature(enabled):
    body = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
    r = TestClient(app).post("/webhooks/stripe", content=body, headers={"Stripe-Signature": _sig(body, "whsec_wrong")})
    assert r.status_code == 400


def test_webhook_pack_grants_coins_with_first_bonus(enabled, monkeypatch):
    sb = FakeSB(first_done=False)
    grants = []
    monkeypatch.setattr(routes_billing, "get_supabase", lambda: sb)
    monkeypatch.setattr(wallet, "grant", lambda *a, **k: grants.append((a, k)) or 0)
    event = {
        "id": "evt_1", "object": "event", "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_1", "object": "checkout.session", "mode": "payment", "payment_status": "paid",
                            "metadata": {"user_id": USER, "product_id": "astrype_coins_650"}}},
    }
    body = json.dumps(event).encode()
    r = TestClient(app).post("/webhooks/stripe", content=body, headers={"Stripe-Signature": _sig(body)})
    assert r.status_code == 200
    (args, kw), = grants
    assert args[1] == USER and args[2] == 650 + 325 and args[3] == "purchase"
    assert kw["idempotency_key"] == "stripe_pack:cs_test_1"
    assert ("wallets", {"first_purchase_done": True}) in sb.updates


def test_invoice_paid_activates_sub_and_grants(monkeypatch):
    sb = FakeSB()
    grants = []
    monkeypatch.setattr(wallet, "grant", lambda *a, **k: grants.append((a, k)) or 0)
    sbb.handle_event(sb, {
        "type": "invoice.paid",
        "data": {"object": {"id": "in_1", "billing_reason": "subscription_create",
                            "parent": {"subscription_details": {"metadata": {"user_id": USER, "product_id": "astrype_sub_yearly"}}},
                            "lines": {"data": [{"period": {"end": 1893456000}}]}}},
    })
    name, row = sb.upserts[0]
    assert name == "subscriptions" and row["is_active"] and row["tier"] == "premium" and row["period"] == "yearly"
    amounts = sorted(a[2] for a, _ in grants)
    assert amounts == [700, 1500]


def test_subscription_deleted_deactivates():
    sb = FakeSB()
    sbb.handle_event(sb, {"type": "customer.subscription.deleted", "data": {"object": {
        "status": "canceled", "metadata": {"user_id": USER, "product_id": "astrype_sub_monthly"}, "current_period_end": 1893456000}}})
    assert sb.upserts[0][1]["is_active"] is False and sb.upserts[0][1]["tier"] == "free"

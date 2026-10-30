"""Stripe web ödemeleri: Checkout oturumu + webhook işleme.

Fiyatlar Stripe panelinde ürün gerektirmez: billing_catalog'daki USD fiyatı
`price_data` ile oturuma yazılır. Kullanıcı, oturum/abonelik metadata'sındaki
user_id ile eşlenir. Tüm coin yatırmaları idempotent (Stripe nesne id'si).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from supabase import Client

from app.config import get_settings
from app.services import billing_catalog as cat
from app.services import wallet

log = logging.getLogger("astrype.stripe")

_INTERVAL = {"weekly": ("week", 1), "monthly": ("month", 1), "yearly": ("year", 1)}


class BillingDisabled(Exception):
    pass


class BillingInputError(ValueError):
    pass


def _stripe():
    s = get_settings()
    if not s.stripe_enabled or not s.stripe_secret_key:
        raise BillingDisabled()
    import stripe  # yalnız etkinken yüklenir

    stripe.api_key = s.stripe_secret_key
    return stripe


def allowed_return_url(url: str) -> bool:
    """Açık yönlendirmeyi önle: yalnız izinli web kökenlerine dönüş."""
    try:
        p = urlparse(url)
    except ValueError:
        return False
    origin = f"{p.scheme}://{p.netloc}"
    return p.scheme in ("http", "https") and origin in get_settings().web_origin_list


def build_session_params(user_id: str, email: str | None, product_id: str, success_url: str, cancel_url: str) -> dict[str, Any]:
    """Checkout oturum parametreleri (saf fonksiyon — test edilebilir)."""
    if not (allowed_return_url(success_url) and allowed_return_url(cancel_url)):
        raise BillingInputError("return_url")
    meta = {"user_id": user_id, "product_id": product_id}
    pack = cat.coin_pack(product_id)
    sub = cat.subscription(product_id) if product_id.startswith("astrype_sub_") else None
    common: dict[str, Any] = {
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": user_id,
        "metadata": meta,
        "allow_promotion_codes": False,
    }
    if email:
        common["customer_email"] = email
    if pack:
        return {
            **common,
            "mode": "payment",
            "line_items": [{
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(round(pack["usd"] * 100)),
                    "product_data": {"name": f"Astrype Stardust · {pack['coins']}"},
                },
            }],
            "payment_intent_data": {"metadata": meta},
        }
    if sub:
        interval, count = _INTERVAL[sub["period"]]
        sub_data: dict[str, Any] = {"metadata": meta}
        if sub.get("trial_days"):
            sub_data["trial_period_days"] = int(sub["trial_days"])
        return {
            **common,
            "mode": "subscription",
            "line_items": [{
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(round(sub["usd"] * 100)),
                    "recurring": {"interval": interval, "interval_count": count},
                    "product_data": {"name": f"Astrype Premium · {sub['period']}"},
                },
            }],
            "subscription_data": sub_data,
        }
    raise BillingInputError("product_id")


def create_checkout(user_id: str, email: str | None, product_id: str, success_url: str, cancel_url: str) -> str:
    params = build_session_params(user_id, email, product_id, success_url, cancel_url)
    session = _stripe().checkout.Session.create(**params)
    return session["url"]


def verify_event(payload: bytes, signature: str) -> dict[str, Any]:
    s = get_settings()
    if not s.stripe_enabled or not s.stripe_webhook_secret:
        raise BillingDisabled()
    import stripe

    return stripe.Webhook.construct_event(payload, signature, s.stripe_webhook_secret)


# ---------------------------------------------------------------- işleme

def _g(obj: Any, *path: str) -> Any:
    for k in path:
        if obj is None:
            return None
        if isinstance(obj, list):
            obj = obj[int(k)] if k.isdigit() and int(k) < len(obj) else None
        elif isinstance(obj, dict):
            obj = obj.get(k)
        else:
            obj = getattr(obj, k, None)
    return obj


def grant_pack(sb: Client, user_id: str, product_id: str, idem: str) -> None:
    pack = cat.coin_pack(product_id)
    if not pack:
        log.warning("bilinmeyen paket %s (user=%s)", product_id, user_id)
        return
    base = int(pack["coins"])
    w = sb.table("wallets").select("first_purchase_done").eq("user_id", user_id).limit(1).execute()
    rows = getattr(w, "data", None) or []
    first_done = bool(rows and rows[0].get("first_purchase_done"))
    bonus = 0 if first_done else int(base * cat.FIRST_PURCHASE_BONUS_RATE)
    wallet.grant(
        sb, user_id, base + bonus, "purchase",
        idempotency_key=f"stripe_pack:{idem}",
        metadata={"product_id": product_id, "coins": base, "first_purchase_bonus": bonus, "store": "stripe"},
    )
    if not first_done:
        sb.table("wallets").update({"first_purchase_done": True}).eq("user_id", user_id).execute()


def _sub_meta(invoice: dict[str, Any]) -> dict[str, Any]:
    # API sürümüne göre abonelik metadata'sı farklı yerde olabilir.
    for path in (("subscription_details", "metadata"), ("parent", "subscription_details", "metadata")):
        m = _g(invoice, *path)
        if m and m.get("user_id"):
            return dict(m)
    lines = _g(invoice, "lines", "data") or []
    for line in lines:
        m = _g(line, "metadata")
        if m and m.get("user_id"):
            return dict(m)
    return {}


def _ts(v: Any) -> str | None:
    return datetime.fromtimestamp(int(v), tz=timezone.utc).isoformat() if v else None


def _upsert_sub(sb: Client, user_id: str, product_id: str, active: bool, period_end: Any) -> None:
    sub = cat.subscription(product_id) or {}
    sb.table("subscriptions").upsert(
        {
            "user_id": user_id,
            "tier": cat.ENTITLEMENT_TIER.get(sub.get("entitlement", ""), "premium") if active else "free",
            "is_active": active,
            "expires_at": _ts(period_end),
            "product_id": product_id if sub else None,
            "period": sub.get("period"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="user_id",
    ).execute()


def handle_event(sb: Client, event: dict[str, Any]) -> None:
    """Stripe olayını işle. Bilinmeyen tür / kullanıcı → loglanan no-op."""
    etype = _g(event, "type")
    obj = _g(event, "data", "object") or {}

    if etype == "checkout.session.completed":
        meta = _g(obj, "metadata") or {}
        user_id, product_id = meta.get("user_id"), meta.get("product_id")
        if not user_id or not product_id:
            log.warning("checkout oturumu metadata eksik (%s)", _g(obj, "id"))
            return
        if _g(obj, "mode") == "payment" and _g(obj, "payment_status") == "paid":
            grant_pack(sb, user_id, product_id, _g(obj, "id"))
        # Abonelik coinleri invoice.paid ile gelir.
        return

    if etype == "invoice.paid":
        meta = _sub_meta(obj)
        user_id, product_id = meta.get("user_id"), meta.get("product_id")
        sub = cat.subscription(product_id or "")
        if not user_id or not sub:
            return
        lines = _g(obj, "lines", "data") or []
        period_end = _g(lines[0], "period", "end") if lines else None
        _upsert_sub(sb, user_id, product_id, True, period_end)
        reason = _g(obj, "billing_reason")
        inv_id = _g(obj, "id")
        if int(sub.get("coin_grant", 0)) > 0 and reason in ("subscription_create", "subscription_cycle"):
            wallet.grant(sb, user_id, int(sub["coin_grant"]), "subscription_grant",
                         idempotency_key=f"stripe_sub:{inv_id}",
                         metadata={"product_id": product_id, "period": sub.get("period"), "store": "stripe"})
        if reason == "subscription_create" and int(sub.get("welcome_bonus", 0)) > 0:
            wallet.grant(sb, user_id, int(sub["welcome_bonus"]), "welcome_bonus",
                         idempotency_key=f"stripe_welcome:{inv_id}",
                         metadata={"product_id": product_id, "store": "stripe"})
        return

    if etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        meta = _g(obj, "metadata") or {}
        user_id, product_id = meta.get("user_id"), meta.get("product_id")
        if not user_id or not product_id:
            return
        status = _g(obj, "status")
        active = etype == "customer.subscription.updated" and status in ("active", "trialing", "past_due")
        period_end = _g(obj, "current_period_end") or _g(obj, "items", "data", "0", "current_period_end")
        _upsert_sub(sb, user_id, product_id, active, period_end)
        return

    log.info("Stripe olayı işlenmedi: %s", etype)

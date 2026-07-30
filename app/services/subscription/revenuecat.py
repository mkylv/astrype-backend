"""RevenueCat webhook senkronu — abonelik durumu + coin kazandırma.

Yetki kontrolü her zaman backend'de (subscriptions + wallets tabloları) yapılır;
Flutter'ın bildirdiği tier'a/coin'e güvenilmez. Coin kazandırmaları event id ile
idempotent'tir: RevenueCat aynı webhook'u tekrar gönderse bile çift yatmaz.
"""
import hmac
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.config import get_settings
from app.services import billing_catalog as cat
from app.services import wallet

_ACTIVE_TYPES = {
    "INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE",
    "UNCANCELLATION", "NON_RENEWING_PURCHASE",
}
_INACTIVE_TYPES = {"CANCELLATION", "EXPIRATION", "BILLING_ISSUE"}


def verify_signature(authorization_header: str) -> bool:
    """RevenueCat webhook Authorization header'ını sabit-zamanlı karşılaştır."""
    secret = get_settings().revenuecat_webhook_secret
    if not secret:
        return False
    provided = authorization_header.removeprefix("Bearer ").strip()
    return hmac.compare_digest(provided, secret)


def _tier_from_event(event: dict[str, Any]) -> tuple[str, bool]:
    ev_type = event.get("type", "")
    entitlements = event.get("entitlement_ids") or []
    tier = "free"
    for ent in entitlements:
        if ent in cat.ENTITLEMENT_TIER:
            tier = cat.ENTITLEMENT_TIER[ent]
            break
    if ev_type in _INACTIVE_TYPES:
        return "free", False
    if ev_type in _ACTIVE_TYPES:
        return tier, True
    return tier, bool(entitlements)


def _grant_coins_for_event(sb: Client, user_id: str, event: dict[str, Any]) -> None:
    """Event bir abonelik yenilemesi ya da coin paketi alımıysa coin yatır."""
    ev_type = event.get("type", "")
    ev_id = event.get("id") or f"{user_id}:{event.get('event_timestamp_ms','')}"
    product_id = event.get("product_id", "")

    # 1) Coin paketi (consumable) alımı.
    pack = cat.coin_pack(product_id)
    if pack and ev_type in ("NON_RENEWING_PURCHASE", "INITIAL_PURCHASE"):
        base = int(pack["coins"])
        w = sb.table("wallets").select("first_purchase_done").eq("user_id", user_id).limit(1).execute()
        rows = getattr(w, "data", None) or []
        first_done = bool(rows and rows[0].get("first_purchase_done"))
        bonus = 0 if first_done else int(base * cat.FIRST_PURCHASE_BONUS_RATE)
        wallet.grant(
            sb, user_id, base + bonus, "purchase",
            idempotency_key=f"rc_pack:{ev_id}",
            metadata={"product_id": product_id, "coins": base, "first_purchase_bonus": bonus},
        )
        if not first_done:
            sb.table("wallets").update({"first_purchase_done": True}).eq("user_id", user_id).execute()
        return

    # 2) Abonelik dönem coini + (ilk alımda) welcome bonusu.
    sub = cat.subscription(product_id)
    if sub and ev_type in ("INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION"):
        if int(sub.get("coin_grant", 0)) > 0:
            wallet.grant(
                sb, user_id, int(sub["coin_grant"]), "subscription_grant",
                idempotency_key=f"rc_sub:{ev_id}",
                metadata={"product_id": product_id, "period": sub.get("period")},
            )
        if ev_type == "INITIAL_PURCHASE" and int(sub.get("welcome_bonus", 0)) > 0:
            wallet.grant(
                sb, user_id, int(sub["welcome_bonus"]), "welcome_bonus",
                idempotency_key=f"rc_welcome:{ev_id}",
                metadata={"product_id": product_id},
            )


async def handle_event(sb: Client, payload: dict[str, Any]) -> None:
    """Webhook payload'ını subscriptions + wallets tablolarına işle."""
    event = payload.get("event", {})
    app_user_id = event.get("app_user_id")
    if not app_user_id:
        return

    tier, is_active = _tier_from_event(event)
    product_id = event.get("product_id")
    sub_meta = cat.subscription(product_id or "")

    expires_ms = event.get("expiration_at_ms")
    expires_at = None
    if expires_ms:
        expires_at = datetime.fromtimestamp(expires_ms / 1000, tz=timezone.utc).isoformat()

    sb.table("subscriptions").upsert(
        {
            "user_id": app_user_id,
            "rc_app_user_id": app_user_id,
            "tier": tier,
            "is_active": is_active,
            "expires_at": expires_at,
            "product_id": product_id if sub_meta else None,
            "period": sub_meta.get("period") if sub_meta else None,
            "updated_at": "now()",
        },
        on_conflict="user_id",
    ).execute()

    # Coin kazandırma (idempotent).
    try:
        _grant_coins_for_event(sb, app_user_id, event)
    except Exception:  # noqa: BLE001 — coin yatırma başarısızsa abonelik senkronu bozulmasın
        import logging

        logging.getLogger("astrype.revenuecat").exception("coin grant hatası")

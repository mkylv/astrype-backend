"""RevenueCat webhook senkronu.

Yetki kontrolü her zaman backend'de (subscriptions tablosu) yapılır;
Flutter'ın bildirdiği tier'a güvenilmez.
"""
import hmac
from typing import Any

from supabase import Client

from app.config import get_settings

# RevenueCat ürün/entitlement -> uygulama tier eşlemesi.
_ENTITLEMENT_TIER = {
    "premium": "premium",
    "elite": "elite",
}


def verify_signature(authorization_header: str) -> bool:
    """RevenueCat webhook Authorization header'ını sabit-zamanlı karşılaştır."""
    secret = get_settings().revenuecat_webhook_secret
    if not secret:
        return False
    provided = authorization_header.removeprefix("Bearer ").strip()
    return hmac.compare_digest(provided, secret)


def _tier_from_event(event: dict[str, Any]) -> tuple[str, bool]:
    """Event'ten (tier, is_active) çıkar."""
    ev_type = event.get("type", "")
    entitlements = event.get("entitlement_ids") or []
    active_types = {
        "INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE",
        "UNCANCELLATION", "NON_RENEWING_PURCHASE",
    }
    inactive_types = {"CANCELLATION", "EXPIRATION", "BILLING_ISSUE"}

    tier = "free"
    for ent in entitlements:
        if ent in _ENTITLEMENT_TIER:
            tier = _ENTITLEMENT_TIER[ent]
            break

    if ev_type in inactive_types:
        return "free", False
    if ev_type in active_types:
        return tier, True
    return tier, bool(entitlements)


async def handle_event(sb: Client, payload: dict[str, Any]) -> None:
    """Webhook payload'ını subscriptions tablosuna işle."""
    event = payload.get("event", {})
    app_user_id = event.get("app_user_id")
    if not app_user_id:
        return
    tier, is_active = _tier_from_event(event)
    expires_ms = event.get("expiration_at_ms")
    expires_at = None
    if expires_ms:
        # ms epoch -> ISO; DB tarafında timestamptz'e cast edilir.
        from datetime import datetime, timezone

        expires_at = datetime.fromtimestamp(
            expires_ms / 1000, tz=timezone.utc
        ).isoformat()

    sb.table("subscriptions").upsert(
        {
            "user_id": app_user_id,
            "rc_app_user_id": app_user_id,
            "tier": tier,
            "is_active": is_active,
            "expires_at": expires_at,
            "updated_at": "now()",
        },
        on_conflict="user_id",
    ).execute()

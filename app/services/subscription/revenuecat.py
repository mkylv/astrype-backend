"""RevenueCat webhook senkronu — abonelik durumu + coin kazandırma.

Yetki kontrolü her zaman backend'de (subscriptions + wallets tabloları) yapılır;
Flutter'ın bildirdiği tier'a/coin'e güvenilmez. Coin kazandırmaları event id ile
idempotent'tir: RevenueCat aynı webhook'u tekrar gönderse bile çift yatmaz.

Yaşam döngüsü (RevenueCat event semantiği):
- INITIAL_PURCHASE / RENEWAL / UNCANCELLATION / PRODUCT_CHANGE / SUBSCRIPTION_EXTENDED
  / TEMPORARY_ENTITLEMENT_GRANT / NON_RENEWING_PURCHASE (abonelik ürünü) → aktif,
  expires_at = expiration_at_ms.
- CANCELLATION → otomatik yenileme kapandı (veya iade). Erişim kesilMEZ;
  expires_at = expiration_at_ms'e kadar sürer (iadede bu zaten geçmiş zamandır).
- BILLING_ISSUE → ödeme alınamadı. Gelecekte bir grace_period_expiration_at_ms varsa
  erişim o ana kadar uzar; yoksa mevcut expires_at korunur (uzatılmaz).
- EXPIRATION → erişimi bitiren event (is_active=false).
- TRANSFER → abonelik satırı transferred_from → transferred_to kullanıcısına taşınır.

Erişim kontrolü zamana dayalıdır (supabase_client.subscription_is_current): kaçırılan
bir EXPIRATION kalıcı premium vermez.
"""
from __future__ import annotations

import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.config import get_settings
from app.db.supabase_client import _first_row, _parse_ts
from app.services import billing_catalog as cat
from app.services import wallet

log = logging.getLogger("astrype.revenuecat")

# Erişimi (yeniden) açan / süresini güncelleyen event'ler.
_ACTIVE_TYPES = {
    "INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE",
    "UNCANCELLATION", "NON_RENEWING_PURCHASE",
    "SUBSCRIPTION_EXTENDED", "TEMPORARY_ENTITLEMENT_GRANT",
}
# Yalnızca bu event erişimi bitirir.
_INACTIVE_TYPES = {"EXPIRATION"}
# Erişimi hemen kesmeyen, süreye göre yöneten event'ler.
_TIME_BOUND_TYPES = {"CANCELLATION", "BILLING_ISSUE"}


def verify_signature(authorization_header: str) -> bool:
    """RevenueCat webhook Authorization header'ını sabit-zamanlı karşılaştır."""
    secret = get_settings().revenuecat_webhook_secret
    if not secret:
        return False
    provided = authorization_header.removeprefix("Bearer ").strip()
    return hmac.compare_digest(provided, secret)


def _is_uuid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def resolve_user_id(event: dict[str, Any]) -> str | None:
    """Event'teki ilk Supabase UUID'sini bul.

    Uygulama her zaman Purchases.logIn(supabaseUid) çağırır; ama event anonim
    ($RCAnonymousID:...) id ile gelebilir. Sıra: app_user_id → original_app_user_id → aliases.
    """
    candidates: list[Any] = [event.get("app_user_id"), event.get("original_app_user_id")]
    candidates.extend(event.get("aliases") or [])
    for c in candidates:
        if _is_uuid(c):
            return str(c)
    return None


def _ms_to_dt(ms: Any) -> datetime | None:
    if ms in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _effective_product_id(event: dict[str, Any]) -> str:
    """PRODUCT_CHANGE'de yeni ürün new_product_id'dedir (katalogda varsa onu kullan)."""
    new_pid = event.get("new_product_id")
    if event.get("type") == "PRODUCT_CHANGE" and new_pid and cat.subscription(new_pid):
        return new_pid
    return event.get("product_id") or ""


def _tier_from_event(event: dict[str, Any]) -> tuple[str, bool]:
    """(tier, entitlement_bu_eventle_devam_ediyor_mu).

    CANCELLATION/BILLING_ISSUE erişimi hemen kesmez (True döner); gerçek aktiflik
    handle_event'te expiration/grace zamanına göre belirlenir.
    """
    ev_type = event.get("type", "")
    entitlements = event.get("entitlement_ids") or []
    if not entitlements and event.get("entitlement_id"):
        entitlements = [event["entitlement_id"]]
    tier = "free"
    for ent in entitlements:
        if ent in cat.ENTITLEMENT_TIER:
            tier = cat.ENTITLEMENT_TIER[ent]
            break
    if tier == "free":
        # Entitlement listesi boş/eksikse abonelik ürününün katalog entitlement'ına düş.
        sub = cat.subscription(_effective_product_id(event))
        if sub:
            tier = cat.ENTITLEMENT_TIER.get(sub.get("entitlement", ""), "free")
    if ev_type in _INACTIVE_TYPES:
        return "free", False
    if ev_type in _ACTIVE_TYPES or ev_type in _TIME_BOUND_TYPES:
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


def _existing_row(sb: Client, user_id: str) -> dict[str, Any] | None:
    try:
        res = (
            sb.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return _first_row(res)
    except Exception:  # noqa: BLE001
        log.warning("subscription okunamadı (user=%s)", user_id)
        return None


def _row_expiry(row: dict[str, Any] | None) -> datetime | None:
    if not row:
        return None
    try:
        return _parse_ts(row.get("expires_at"))
    except ValueError:
        return None


def build_subscription_update(
    event: dict[str, Any],
    existing: dict[str, Any] | None,
    user_id: str,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Event'ten yazılacak subscriptions satırını üret. None → satıra dokunma."""
    now = now or datetime.now(timezone.utc)
    ev_type = event.get("type", "")
    product_id = _effective_product_id(event)

    # Coin paketi (consumable) aboneliği etkilemez — mevcut premium satırını ezmesin.
    if cat.coin_pack(product_id) and not cat.subscription(product_id):
        return None

    tier, _ = _tier_from_event(event)
    sub_meta = cat.subscription(product_id)
    expiration = _ms_to_dt(event.get("expiration_at_ms"))
    base = {
        "user_id": user_id,
        "rc_app_user_id": event.get("app_user_id") or user_id,
        "updated_at": now.isoformat(),
    }
    product_fields = {
        "product_id": product_id if sub_meta else None,
        "period": sub_meta.get("period") if sub_meta else None,
    }
    existing_exp = _row_expiry(existing)

    if ev_type in _ACTIVE_TYPES:
        return {
            **base, **product_fields,
            "tier": tier,
            "is_active": expiration is None or expiration > now,
            "expires_at": expiration.isoformat() if expiration else None,
        }

    if ev_type == "CANCELLATION":
        # Yenileme kapandı; ödenen dönem sonuna kadar erişim sürer. İadede
        # expiration_at_ms iade anıdır (geçmiş) → erişim zaten biter.
        log.info(
            "CANCELLATION: yenilenmeyecek, erişim %s tarihine kadar (user=%s, reason=%s)",
            expiration, user_id, event.get("cancel_reason"),
        )
        if expiration is None:
            expiration = existing_exp
        if tier == "free" and existing:
            tier = existing.get("tier") or "free"
        return {
            **base, **product_fields,
            "tier": tier,
            "is_active": expiration is not None and expiration > now,
            "expires_at": expiration.isoformat() if expiration else None,
        }

    if ev_type == "BILLING_ISSUE":
        grace = _ms_to_dt(event.get("grace_period_expiration_at_ms"))
        if grace and grace > now:
            if tier == "free" and existing:
                tier = existing.get("tier") or "free"
            log.info("BILLING_ISSUE: grace period %s tarihine kadar (user=%s)", grace, user_id)
            return {
                **base, **product_fields,
                "tier": tier,
                "is_active": True,
                "expires_at": grace.isoformat(),
            }
        # Grace yok: mevcut expires_at korunur (uzatılmaz); süre dolunca erişim biter.
        log.info("BILLING_ISSUE: grace yok, mevcut expires_at korunuyor (user=%s)", user_id)
        return None

    if ev_type == "EXPIRATION":
        # Sıra dışı gelen eski EXPIRATION, sonradan yenilenmiş aboneliği kesmesin.
        if (
            existing
            and existing.get("is_active")
            and existing_exp is not None
            and existing_exp > now
            and (expiration is None or existing_exp > expiration)
        ):
            log.info("EXPIRATION eski/sıra dışı, yok sayıldı (user=%s)", user_id)
            return None
        return {
            **base,
            "tier": "free",
            "is_active": False,
            "expires_at": expiration.isoformat() if expiration else now.isoformat(),
        }

    # SUBSCRIPTION_PAUSED, SUBSCRIBER_ALIAS, INVOICE_ISSUANCE vb.: erişimi değiştirmez.
    log.info("RevenueCat event erişimi değiştirmiyor, atlandı (type=%s)", ev_type)
    return None


def _handle_transfer(sb: Client, event: dict[str, Any]) -> None:
    to_ids = [i for i in (event.get("transferred_to") or []) if _is_uuid(i)]
    from_ids = [i for i in (event.get("transferred_from") or []) if _is_uuid(i)]
    skipped = [
        i for i in (event.get("transferred_to") or []) + (event.get("transferred_from") or [])
        if not _is_uuid(i)
    ]
    if skipped:
        log.info("TRANSFER: UUID olmayan id'ler atlandı: %s", skipped)
    if not to_ids or not from_ids:
        log.warning("TRANSFER: geçerli kaynak/hedef UUID yok, atlandı")
        return
    to_id = to_ids[0]

    rows = [r for r in (_existing_row(sb, f) for f in from_ids if f != to_id) if r]
    if not rows:
        log.info("TRANSFER: kaynak kullanıcıda abonelik satırı yok (to=%s)", to_id)
        return
    # En uzun süreli aktif satırı taşı (expires_at None = lifetime en üstte).
    far = datetime.max.replace(tzinfo=timezone.utc)
    rows.sort(key=lambda r: (bool(r.get("is_active")), _row_expiry(r) or far), reverse=True)
    src = rows[0]
    now_iso = datetime.now(timezone.utc).isoformat()
    moved = {
        "user_id": to_id,
        "rc_app_user_id": to_id,
        "tier": src.get("tier") or "free",
        "is_active": bool(src.get("is_active")),
        "expires_at": src.get("expires_at"),
        "product_id": src.get("product_id"),
        "period": src.get("period"),
        "updated_at": now_iso,
    }
    try:
        sb.table("subscriptions").upsert(moved, on_conflict="user_id").execute()
        for f in from_ids:
            if f == to_id:
                continue
            sb.table("subscriptions").update(
                {"tier": "free", "is_active": False, "updated_at": now_iso}
            ).eq("user_id", f).execute()
        log.info("TRANSFER: abonelik %s -> %s taşındı", from_ids, to_id)
    except Exception:  # noqa: BLE001
        log.warning("TRANSFER: taşıma başarısız (to=%s)", to_id)


async def handle_event(sb: Client, payload: dict[str, Any]) -> None:
    """Webhook payload'ını subscriptions + wallets tablolarına işle.

    Dayanıklı: RevenueCat TEST event'i, UUID çözülemeyen (anonim) kullanıcı ve
    profilde olmayan (sahte/silinmiş) kullanıcı 500 değil, loglanan no-op olur —
    webhook her zaman 2xx döner (RevenueCat sonsuz retry yapmaz).
    """
    event = payload.get("event", {}) or {}
    ev_type = event.get("type", "")

    # RevenueCat panel "Send test event" — doğrulama için, işlenmez.
    if ev_type == "TEST":
        return

    if ev_type == "TRANSFER":
        _handle_transfer(sb, event)
        return

    user_id = resolve_user_id(event)
    if not user_id:
        log.warning(
            "RevenueCat event atlandı: UUID bulunamadı (type=%s, app_user_id=%s, event_id=%s)",
            ev_type, event.get("app_user_id"), event.get("id"),
        )
        return

    # Abonelik senkronu — bilinmeyen user_id (FK) 500'e yol açmasın.
    try:
        existing = _existing_row(sb, user_id)
        row = build_subscription_update(event, existing, user_id)
        if row is not None:
            sb.table("subscriptions").upsert(row, on_conflict="user_id").execute()
    except Exception:  # noqa: BLE001 — bilinmeyen kullanıcı / geçici hata
        log.warning("subscription upsert atlandı (user=%s)", user_id)

    # Coin kazandırma (idempotent).
    try:
        _grant_coins_for_event(sb, user_id, event)
    except Exception:  # noqa: BLE001 — coin yatırma başarısızsa abonelik senkronu bozulmasın
        log.warning("coin grant atlandı (user=%s)", user_id)

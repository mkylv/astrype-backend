"""Coin cüzdanı servisi — bakiye, erişim kontrolü, harcama, kazandırma.

Tüm coin hareketleri atomik Postgres RPC'leri (spend_coins/grant_coins) üzerinden
yapılır; bakiye SUNUCU tarafında tutulur. Harcama idempotent'tir: aynı
idempotency_key ile ikinci istek çift düşmez (timeout/retry güvenliği).

Erişim modeli (coinekonomisi §4-5):
- free        → hiç ücret yok (Günlük Burç).
- continuous  → aktif abone için ücretsiz (sınırsız); değilse coin düşer.
- one_time    → her zaman coin düşer (abone dahil; abone zaten aylık coin alır).
- chat        → abone günlük mesaj hakkı, sonrası indirimli coin; abone değilse coin.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timezone
from datetime import datetime as _dt
from typing import Any

from fastapi import HTTPException, status
from supabase import Client

from app.config import get_settings
from app.db.supabase_client import _first_row, get_user_tier
from app.services import billing_catalog as cat

# Fiyat kataloğu, DB'de değişebildiği için kısa süreli önbelleklenir.
_PRICE_CACHE: dict[str, tuple[int, str]] = {}


def _load_prices(sb: Client) -> dict[str, tuple[int, str]]:
    global _PRICE_CACHE
    if _PRICE_CACHE:
        return _PRICE_CACHE
    res = sb.table("feature_prices").select("feature,coin_price,category").execute()
    rows = getattr(res, "data", None) or []
    _PRICE_CACHE = {r["feature"]: (int(r["coin_price"]), r["category"]) for r in rows}
    return _PRICE_CACHE


def feature_price(sb: Client, feature: str) -> tuple[int, str]:
    """(coin_price, category) döner; bilinmeyen feature güvenli varsayılan (0, free)."""
    return _load_prices(sb).get(feature, (0, "free"))


def new_idempotency_key() -> str:
    return uuid.uuid4().hex


def get_balance(sb: Client, user_id: str) -> int:
    res = sb.table("wallets").select("balance").eq("user_id", user_id).limit(1).execute()
    row = _first_row(res)
    return int(row["balance"]) if row else 0


def _subscription_row(sb: Client, user_id: str) -> dict[str, Any] | None:
    res = (
        sb.table("subscriptions")
        .select("tier,is_active,product_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return _first_row(res)


@dataclass
class Access:
    feature: str
    price: int
    category: str
    will_charge: bool          # coin düşecek mi
    covered_by: str            # 'free' | 'subscription' | 'coin'
    balance: int


def _already_unlocked(sb: Client, unlock_key: str | None) -> bool:
    """Bu unlock_key ile daha önce ücret alındıysa (kimlik/dönem başına bir kez)."""
    if not unlock_key:
        return False
    res = (
        sb.table("coin_transactions")
        .select("id")
        .eq("idempotency_key", unlock_key)
        .limit(1)
        .execute()
    )
    return bool(getattr(res, "data", None))


def check_access(
    sb: Client, user_id: str, feature: str, unlock_key: str | None = None
) -> Access:
    """Üretimden ÖNCE çağrılır. Yetersiz bakiyede 402 fırlatır.

    unlock_key verilirse (kimlik/dönem başına bir kez ödenen özellikler için) ve
    daha önce o key ile ödenmişse ücret alınmaz (tekrar erişim serbest).
    """
    price, category = feature_price(sb, feature)
    if not get_settings().coins_enabled:
        # Coin ekonomisi kapalı: erişim serbest, ücret yok (mevcut davranış).
        return Access(feature, price, category, False, "disabled", get_balance(sb, user_id))
    sub = _subscription_row(sb, user_id)
    subscriber = bool(sub and sub.get("is_active") and sub.get("tier") in ("premium", "elite"))
    balance = get_balance(sb, user_id)

    if category == "free":
        return Access(feature, 0, category, False, "free", balance)
    if category == "continuous" and subscriber:
        return Access(feature, price, category, False, "subscription", balance)
    if _already_unlocked(sb, unlock_key):
        return Access(feature, price, category, False, "already_unlocked", balance)
    # one_time (her zaman) veya continuous (abone değil) → coin gerekir
    if balance < price:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "INSUFFICIENT_COINS",
                "feature": feature,
                "needed": price,
                "balance": balance,
                "message": "Bu analiz için yeterli Yıldız Tozu yok.",
            },
        )
    return Access(feature, price, category, True, "coin", balance)


def commit_charge(
    sb: Client, user_id: str, feature: str, idempotency_key: str | None = None
) -> dict[str, Any]:
    """Üretim BAŞARILI olduktan sonra çağrılır; gerçek coin düşümü (idempotent).

    Abonelik/ücretsiz kapsamındaysa 0 tutarla no-op çalışır (bakiye döner).
    """
    if not get_settings().coins_enabled:
        return {"charged": False, "cost": 0, "balance": get_balance(sb, user_id)}
    price, category = feature_price(sb, feature)
    sub = _subscription_row(sb, user_id)
    subscriber = bool(sub and sub.get("is_active") and sub.get("tier") in ("premium", "elite"))

    amount = price
    if category == "free":
        amount = 0
    elif category == "continuous" and subscriber:
        amount = 0

    try:
        res = sb.rpc(
            "spend_coins",
            {
                "p_user": user_id,
                "p_amount": amount,
                "p_reason": "spend",
                "p_module": feature,
                "p_idempotency_key": idempotency_key,
            },
        ).execute()
        data = getattr(res, "data", None) or []
        row = data[0] if isinstance(data, list) and data else data
        return {
            "charged": bool(row.get("charged")) if isinstance(row, dict) else amount > 0,
            "cost": amount,
            "balance": int(row["balance"]) if isinstance(row, dict) and row.get("balance") is not None else get_balance(sb, user_id),
        }
    except Exception as exc:  # noqa: BLE001 — yarış/kenar durumu: üretim bitti, düşüm başarısız
        # Nadir yarış (bakiye üretim sırasında tükendi). Okuma verildi; loglayıp geç.
        import logging

        logging.getLogger("astrype.wallet").warning(
            "commit_charge başarısız (%s/%s): %s", user_id, feature, exc
        )
        return {"charged": False, "cost": 0, "balance": get_balance(sb, user_id), "error": str(exc)}


def grant(
    sb: Client,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
) -> int:
    """Coin kazandır (satın alma/abonelik/bonus). Yeni bakiyeyi döner."""
    res = sb.rpc(
        "grant_coins",
        {
            "p_user": user_id,
            "p_amount": int(amount),
            "p_reason": reason,
            "p_idempotency_key": idempotency_key,
            "p_metadata": metadata or {},
        },
    ).execute()
    data = getattr(res, "data", None)
    if isinstance(data, int):
        return data
    if isinstance(data, list) and data:
        return int(data[0])
    return get_balance(sb, user_id)


def ensure_signup_bonus(sb: Client, user_id: str) -> int:
    """Kayıt hediyesini bir kez yatırır (idempotent). Yeni bakiyeyi döner."""
    return grant(
        sb,
        user_id,
        cat.SIGNUP_BONUS_COINS,
        "signup_bonus",
        idempotency_key=f"signup_bonus:{user_id}",
    )


# ---- Lyra sohbet metreleme ----
def charge_lyra_message(
    sb: Client, user_id: str, idempotency_key: str | None = None
) -> dict[str, Any]:
    """Bir Lyra mesajı için ücretlendir. Abone günlük hakkı içindeyse ücretsiz."""
    if not get_settings().coins_enabled:
        return {"charged": False, "cost": 0, "balance": get_balance(sb, user_id),
                "daily_used": 0, "daily_limit": 0}
    sub = _subscription_row(sb, user_id)
    subscriber = bool(sub and sub.get("is_active") and sub.get("tier") in ("premium", "elite"))
    daily_limit = cat.lyra_daily_limit(sub.get("product_id") if sub else None) if subscriber else 0

    today = _dt.now(tz=timezone.utc).date().isoformat()
    used = sb.rpc("incr_chat_usage", {"p_user": user_id, "p_date": today}).execute()
    used_count = getattr(used, "data", None)
    if isinstance(used_count, list) and used_count:
        used_count = used_count[0]
    used_count = int(used_count or 1)

    if subscriber and used_count <= daily_limit:
        return {"charged": False, "cost": 0, "balance": get_balance(sb, user_id),
                "daily_used": used_count, "daily_limit": daily_limit}

    cost = cat.LYRA_MSG_COST_SUBSCRIBER if subscriber else cat.LYRA_MSG_COST
    balance = get_balance(sb, user_id)
    if balance < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "INSUFFICIENT_COINS", "feature": "lyra_chat",
                    "needed": cost, "balance": balance,
                    "message": "Lyra ile konuşmaya devam için Yıldız Tozu gerekli."},
        )
    res = sb.rpc(
        "spend_coins",
        {"p_user": user_id, "p_amount": cost, "p_reason": "spend",
         "p_module": "lyra_chat", "p_idempotency_key": idempotency_key},
    ).execute()
    data = getattr(res, "data", None) or []
    row = data[0] if isinstance(data, list) and data else data
    return {"charged": True, "cost": cost,
            "balance": int(row["balance"]) if isinstance(row, dict) else balance - cost,
            "daily_used": used_count, "daily_limit": daily_limit}

"""Supabase istemci yardımcıları.

Backend, service-role key ile bağlanır (RLS'yi bypass eder); bu yüzden her
sorguda user_id ile filtreleme YAPILMALIDIR. RLS son savunma hattıdır,
backend'in kendisi de kullanıcı izolasyonunu uygular.
"""
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


def _first_row(res: Any) -> dict[str, Any] | None:
    """maybe_single() sıfır satırda None response dönebildiği için güvenli erişim."""
    if res is None:
        return None
    data = getattr(res, "data", None)
    if not data:
        return None
    return data[0] if isinstance(data, list) else data


def _parse_ts(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def subscription_is_current(row: dict[str, Any] | None, now: datetime | None = None) -> bool:
    """Abonelik ŞU AN geçerli mi: is_active VE (expires_at yok = lifetime VEYA gelecekte).

    Zamana dayalı kontrol sayesinde kaçırılan bir EXPIRATION webhook'u kalıcı
    premium vermez; iptal eden kullanıcı dönem sonunda doğal olarak erişimi kaybeder.
    """
    if not row or not row.get("is_active"):
        return False
    raw = row.get("expires_at")
    if raw in (None, ""):
        return True
    try:
        exp = _parse_ts(raw)
    except ValueError:
        # Okunamayan tarih: ödeyen kullanıcıyı kesmemek için is_active'e güven.
        logging.getLogger("astrype.subscription").warning("expires_at parse edilemedi: %r", raw)
        return True
    if exp is None:
        return True
    return exp > (now or datetime.now(timezone.utc))


def get_user_tier(sb: Client, user_id: str) -> str:
    res = (
        sb.table("subscriptions")
        .select("tier,is_active,expires_at")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _first_row(res)
    if not subscription_is_current(row):
        return "free"
    return row.get("tier", "free")


def ensure_profile(sb: Client, user_id: str) -> None:
    """Anonim kullanıcılar için minimal profil satırı garanti eder (FK için)."""
    sb.table("profiles").upsert({"id": user_id}, on_conflict="id").execute()


def get_profile(sb: Client, user_id: str) -> dict[str, Any] | None:
    res = (
        sb.table("profiles")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return _first_row(res)

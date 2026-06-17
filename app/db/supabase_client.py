"""Supabase istemci yardımcıları.

Backend, service-role key ile bağlanır (RLS'yi bypass eder); bu yüzden her
sorguda user_id ile filtreleme YAPILMALIDIR. RLS son savunma hattıdır,
backend'in kendisi de kullanıcı izolasyonunu uygular.
"""
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


def get_user_tier(sb: Client, user_id: str) -> str:
    res = (
        sb.table("subscriptions")
        .select("tier,is_active")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _first_row(res)
    if not row or not row.get("is_active"):
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

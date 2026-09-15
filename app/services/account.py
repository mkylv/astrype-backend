"""Hesap ve geçmiş silme (Apple 5.1.1(v) + KVKK/GDPR).

Kurallar:
- Kullanıcıya ait TÜM tablolar açıkça silinir (cascade'e güvenilmez; prod şeması
  migration'lardan farklı olabilir).
- Önemli bir adım başarısız olursa `AccountDeletionError` fırlatılır; route bunu
  makine-okunur bir hata koduna çevirir (iç ayrıntı sızdırılmaz, loglanır).
- İdempotent: satır yoksa silme 0 satır etkiler; auth kullanıcısı zaten yoksa
  başarı sayılır. Böylece kısmi hatadan sonra tekrar deneme işi tamamlar.
- Sıra: veri tabloları → profil → EN SON auth kullanıcısı. Erken bir hata akışı
  durdurur; kullanıcı hâlâ giriş yapabilir ve tekrar deneyebilir.
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("astrype.account")

# Hesap silmede temizlenen kullanıcı tabloları (user_id kolonu ile).
# Kaynak: app/ içindeki tüm `.table(...)` yazımları + coin RPC'lerinin yazdığı
# tablolar (wallets, coin_transactions, chat_usage).
ACCOUNT_USER_TABLES: tuple[str, ...] = (
    "chat_messages",
    "memory_chunks",
    "readings",
    "relationships",
    "daily_insight_cache",
    "charts",
    "chat_usage",
    "coin_transactions",
    "wallets",
    "subscriptions",
)

# "Hafıza / geçmiş sil": UI metni "tüm analiz geçmişi, sohbet kayıtları ve
# Cosmic Memory özetleri silinir; profil ve doğum bilgileri kalır" der.
# Bu yüzden natal chart (charts) ve coin/abonelik kayıtları KORUNUR.
MEMORY_SCOPES: dict[str, tuple[str, ...]] = {
    "all": (
        "chat_messages",
        "readings",
        "memory_chunks",
        "relationships",
        "daily_insight_cache",
    ),
    "chat": ("chat_messages",),
    "readings": ("readings", "relationships", "daily_insight_cache"),
    "vectors": ("memory_chunks",),
}

# PostgREST "tablo yok" kodları (eski: Postgres 42P01, yeni: PGRST205).
_MISSING_TABLE_CODES = {"42P01", "PGRST205"}


class AccountDeletionError(Exception):
    def __init__(self, step: str) -> None:
        super().__init__(step)
        self.step = step


def _is_missing_table(exc: Exception) -> bool:
    return str(getattr(exc, "code", "") or "") in _MISSING_TABLE_CODES


def _is_user_not_found(exc: Exception) -> bool:
    status = getattr(exc, "status", None)
    code = str(getattr(exc, "code", "") or "")
    return status == 404 or code == "user_not_found"


def delete_user_rows(sb: Any, user_id: str, tables: tuple[str, ...]) -> list[str]:
    """Verilen tablolardan kullanıcı satırlarını siler. Silinen tabloları döner.

    Var olmayan tablo (prod şema farkı) atlanır ve loglanır; diğer her hata
    `AccountDeletionError(step=<tablo>)` fırlatır.
    """
    deleted: list[str] = []
    for table in tables:
        try:
            sb.table(table).delete().eq("user_id", user_id).execute()
            deleted.append(table)
        except Exception as exc:  # noqa: BLE001
            if _is_missing_table(exc):
                log.warning("delete: table %s not found, skipping", table)
                continue
            log.error("delete failed at table %s for user %s: %r", table, user_id, exc)
            raise AccountDeletionError(table) from exc
    return deleted


def delete_account(sb: Any, user_id: str) -> list[str]:
    """Hesabı ve tüm verisini kalıcı siler. Başarısızlıkta AccountDeletionError."""
    deleted = delete_user_rows(sb, user_id, ACCOUNT_USER_TABLES)

    try:
        sb.table("profiles").delete().eq("id", user_id).execute()
        deleted.append("profiles")
    except Exception as exc:  # noqa: BLE001
        log.error("delete failed at profiles for user %s: %r", user_id, exc)
        raise AccountDeletionError("profile") from exc

    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as exc:  # noqa: BLE001
        if _is_user_not_found(exc):
            log.info("auth user %s already deleted", user_id)
        else:
            log.error("auth user deletion failed for %s: %r", user_id, exc)
            raise AccountDeletionError("auth_user") from exc
    deleted.append("auth_user")
    return deleted

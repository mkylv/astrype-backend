"""Geçmiş analiz arşivi + memory/geçmiş silme (KVKK/GDPR)."""
from fastapi import APIRouter, Depends, Query

from app.db.supabase_client import get_supabase
from app.deps import CurrentUser, current_user

router = APIRouter(tags=["readings"])


@router.get("/readings")
async def list_readings(
    type: str | None = Query(default=None),
    user: CurrentUser = Depends(current_user),
):
    sb = get_supabase()
    q = (
        sb.table("readings")
        .select("id,type,input_meta,result,created_at")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
    )
    if type:
        q = q.eq("type", type)
    return {"items": q.execute().data or []}


@router.delete("/memory")
async def delete_memory(
    scope: str = Query(default="all", pattern="^(all|chat|readings|vectors)$"),
    user: CurrentUser = Depends(current_user),
):
    """Veri minimizasyonu: kullanıcı geçmişini/vektörlerini silebilmeli."""
    sb = get_supabase()
    deleted: list[str] = []
    if scope in ("all", "chat"):
        sb.table("chat_messages").delete().eq("user_id", user.id).execute()
        deleted.append("chat_messages")
    if scope in ("all", "readings"):
        sb.table("readings").delete().eq("user_id", user.id).execute()
        deleted.append("readings")
    if scope in ("all", "vectors"):
        sb.table("memory_chunks").delete().eq("user_id", user.id).execute()
        deleted.append("memory_chunks")
    return {"deleted": deleted}


# Kullanıcının tüm verisini tuttuğu tablolar (hesap silmede temizlenir).
_USER_TABLES = (
    "chat_messages",
    "memory_chunks",
    "readings",
    "relationships",
    "daily_insight_cache",
    "charts",
    "subscriptions",
)


@router.delete("/account")
async def delete_account(user: CurrentUser = Depends(current_user)):
    """Hesabı ve TÜM kullanıcı verisini kalıcı siler (App Store/Play + KVKK/GDPR).

    Önce veri tabloları, sonra profil, en son Supabase Auth kullanıcısı silinir.
    (profiles → auth.users cascade olsa da her tabloyu açıkça temizleriz ki
    denetlenebilir olsun ve cascade'e bağımlı kalmayalım.)
    """
    sb = get_supabase()
    deleted: list[str] = []
    for table in _USER_TABLES:
        try:
            sb.table(table).delete().eq("user_id", user.id).execute()
            deleted.append(table)
        except Exception:
            pass  # tablo yoksa/boşsa devam et — silme akışı bloke olmamalı
    try:
        sb.table("profiles").delete().eq("id", user.id).execute()
        deleted.append("profiles")
    except Exception:
        pass
    # Auth kullanıcısını sil (service-role admin API).
    auth_deleted = False
    try:
        sb.auth.admin.delete_user(user.id)
        auth_deleted = True
    except Exception:
        pass
    return {"deleted": deleted, "auth_user_deleted": auth_deleted}

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

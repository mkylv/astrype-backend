"""Geçmiş analiz arşivi + memory/geçmiş silme (KVKK/GDPR)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.supabase_client import get_supabase
from app.deps import CurrentUser, current_user
from app.services import account

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
    """Veri minimizasyonu: kullanıcı geçmişini/vektörlerini silebilmeli.

    UI vaadi: analiz geçmişi + sohbet + Cosmic Memory silinir; profil, doğum
    bilgisi (natal chart) ve coin/abonelik kayıtları kalır.
    """
    sb = get_supabase()
    try:
        deleted = account.delete_user_rows(sb, user.id, account.MEMORY_SCOPES[scope])
    except account.AccountDeletionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MEMORY_DELETE_FAILED", "step": exc.step},
        ) from exc
    return {"deleted": deleted}


@router.delete("/account")
async def delete_account(user: CurrentUser = Depends(current_user)):
    """Hesabı ve TÜM kullanıcı verisini kalıcı siler (App Store/Play + KVKK/GDPR).

    Veri tabloları → profil → EN SON Supabase Auth kullanıcısı. Herhangi bir
    önemli adım başarısız olursa 500 + {"code":"ACCOUNT_DELETE_FAILED","step":..}
    döner (ayrıntı loglanır). İdempotent: tekrar deneme kalan adımları tamamlar.
    """
    sb = get_supabase()
    try:
        deleted = account.delete_account(sb, user.id)
    except account.AccountDeletionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ACCOUNT_DELETE_FAILED", "step": exc.step},
        ) from exc
    return {"deleted": True, "tables": deleted, "auth_user_deleted": True}

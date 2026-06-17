"""Profil — doğum bilgisi al/güncelle."""
from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import ProfileIn

router = APIRouter(tags=["profile"])


@router.get("/profile")
async def read_profile(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    profile = get_profile(sb, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil bulunamadı.")
    return profile


@router.put("/profile")
async def upsert_profile(body: ProfileIn, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    payload = body.model_dump(mode="json", exclude_none=True)
    payload["id"] = user.id
    sb.table("profiles").upsert(payload, on_conflict="id").execute()
    return get_profile(sb, user.id)

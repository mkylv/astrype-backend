"""RevenueCat abonelik webhook'u."""
from fastapi import APIRouter, Header, HTTPException, Request

from app.db.supabase_client import get_supabase
from app.services.subscription.revenuecat import handle_event, verify_signature

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/revenuecat")
async def revenuecat_webhook(
    request: Request,
    authorization: str = Header(default=""),
):
    if not verify_signature(authorization):
        raise HTTPException(status_code=401, detail="Geçersiz webhook imzası.")
    payload = await request.json()
    await handle_event(get_supabase(), payload)
    return {"ok": True}

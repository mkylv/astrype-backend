"""Web ödemeleri (Stripe Checkout) — STRIPE_ENABLED kapalıyken 503."""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings
from app.db.supabase_client import get_supabase
from app.deps import CurrentUser, current_user
from app.services.subscription import stripe_billing as sb_billing

router = APIRouter(tags=["billing"])
log = logging.getLogger("astrype.stripe")


class CheckoutRequest(BaseModel):
    product_id: str
    success_url: str
    cancel_url: str
    kind: str | None = None  # bilgi amaçlı (pack|subscription); ürün kataloğu belirler


@router.get("/billing/status")
async def billing_status():
    s = get_settings()
    return {"stripe": bool(s.stripe_enabled and s.stripe_secret_key)}


@router.post("/billing/checkout")
async def checkout(body: CheckoutRequest, user: CurrentUser = Depends(current_user)):
    try:
        url = sb_billing.create_checkout(user.id, user.email, body.product_id, body.success_url, body.cancel_url)
    except sb_billing.BillingDisabled:
        raise HTTPException(status_code=503, detail="PAYMENTS_DISABLED")
    except sb_billing.BillingInputError as e:
        raise HTTPException(status_code=422, detail=f"INVALID_{str(e).upper()}")
    return {"url": url}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(default="")):
    payload = await request.body()
    try:
        event = sb_billing.verify_event(payload, stripe_signature)
    except sb_billing.BillingDisabled:
        raise HTTPException(status_code=503, detail="PAYMENTS_DISABLED")
    except Exception:  # noqa: BLE001 — imza / gövde geçersiz
        raise HTTPException(status_code=400, detail="Geçersiz Stripe imzası.")
    try:
        sb_billing.handle_event(get_supabase(), event)
    except Exception:  # noqa: BLE001 — Stripe yeniden dener; log yeter
        log.exception("Stripe olayı işlenemedi (%s)", event.get("type"))
        raise HTTPException(status_code=500, detail="processing_failed")
    return {"ok": True}

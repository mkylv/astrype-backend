"""Coin cüzdanı uçları — bakiye, defter ve ürün kataloğu.

Yetki her zaman backend'de; bakiye Flutter'a güvenilmeden sunucudan okunur.
"""
from fastapi import APIRouter, Depends

from app.db.supabase_client import _first_row, get_supabase
from app.deps import CurrentUser, current_user
from app.services import billing_catalog as cat
from app.services import wallet

router = APIRouter(tags=["wallet"])


@router.get("/wallet")
async def get_wallet(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    # Kayıt hediyesi (idempotent — yalnızca bir kez yatar).
    balance = wallet.ensure_signup_bonus(sb, user.id)

    w = _first_row(
        sb.table("wallets").select("first_purchase_done").eq("user_id", user.id).limit(1).execute()
    )
    tx = (
        sb.table("coin_transactions")
        .select("amount,balance_after,reason,module,created_at")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {
        "balance": balance,
        "first_purchase_done": bool(w and w.get("first_purchase_done")),
        "transactions": getattr(tx, "data", None) or [],
    }


@router.get("/wallet/catalog")
async def get_catalog(user: CurrentUser = Depends(current_user)):
    """Uygulamanın göstereceği fiyat + ürün kataloğu (tek kaynak)."""
    sb = get_supabase()
    prices = sb.table("feature_prices").select("feature,coin_price,category,label").execute()
    return {
        "features": getattr(prices, "data", None) or [],
        "coin_packs": [
            {"product_id": pid, **info} for pid, info in cat.COIN_PACKS.items()
        ],
        "subscriptions": [
            {"product_id": pid, **info} for pid, info in cat.SUBSCRIPTIONS.items()
        ],
        "first_purchase_bonus_rate": cat.FIRST_PURCHASE_BONUS_RATE,
        "subscriber_pack_discount_rate": cat.SUBSCRIBER_PACK_DISCOUNT_RATE,
        "lyra_msg_cost": cat.LYRA_MSG_COST,
        "lyra_msg_cost_subscriber": cat.LYRA_MSG_COST_SUBSCRIBER,
    }

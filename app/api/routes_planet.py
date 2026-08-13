"""Gezegen detayı — natal chart'ta bir gök cismine tıklayınca meta + görsel +
o gezegenin kullanıcının burcundaki/evindeki kişisel, dile-göre AI yorumu.

Yorum, kullanıcının en güncel natal snapshot'ından üretilir ve (user, gezegen,
burç) başına süreç-içi cache'lenir (tekrar tıklamada AI maliyeti çıkmaz).
"""
from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall
from app.services.ai.openai_client import complete_json
from app.services.astro import planet_reference as pref

router = APIRouter(tags=["planet"])

# (user_id, planet, sign) -> insight (süreç ömrü; redeploy'da yenilenir).
_cache: dict[tuple[str, str, str], dict] = {}


@router.get("/planets")
async def list_planets():
    """Tüm gezegenlerin meta + görsel URL'i (app önden cache'leyebilir)."""
    return {"planets": pref.all_meta()}


@router.get("/planet/{key}")
async def planet_insight(key: str, user: CurrentUser = Depends(current_user)):
    meta = pref.meta(key)
    if meta is None:
        raise HTTPException(status_code=404, detail="Bilinmeyen gök cismi.")

    sb = get_supabase()
    chart = (
        sb.table("charts")
        .select("raw_json")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not chart.data:
        raise HTTPException(status_code=400, detail="Önce doğum haritanı oluştur.")

    bc = (chart.data[0].get("raw_json") or {}).get("birth_chart", {})
    body = bc.get(key) or {}
    sign = body.get("sign")
    house = body.get("house")
    if not sign:
        # Gezegen haritada yok (ör. saat yoksa yükselen) — meta + görsel yeter.
        return {**meta, "sign": None, "house": None, "insight": None}

    ck = (user.id, key, str(sign))
    cached = _cache.get(ck)
    if cached is not None:
        return {**meta, "sign": sign, "house": house, "insight": cached}

    profile = get_profile(sb, user.id) or {}
    recalled = await recall(sb, user.id, f"{meta['name']} {sign} yerleşimi")
    context = build_context_block(
        profile,
        recalled,
        {"Gök cismi": meta["name"], "Burç": str(sign), "Ev": str(house or "?")},
    )
    insight = await complete_json(prompts.PLANET_INSIGHT, context)
    _cache[ck] = insight
    return {**meta, "sign": sign, "house": house, "insight": insight}

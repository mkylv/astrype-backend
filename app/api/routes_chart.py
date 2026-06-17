"""Natal chart hesapla/kaydet + istemciye gösterilebilir özet döndür."""
from typing import Any

from fastapi import APIRouter, Depends, Response

from app.api._helpers import resolve_birth
from app.db.supabase_client import ensure_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import ChartRequest
from app.services.astro import get_astro_provider

router = APIRouter(tags=["chart"])

# Ekranda gösterilecek ana gök cisimleri (sırasıyla).
_BODIES = [
    "sun", "moon", "ascendant", "mercury", "venus", "mars", "jupiter",
    "saturn", "uranus", "neptune", "pluto",
]


def _snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    """Ham natal JSON'dan kompakt, gösterilebilir özet çıkarır."""
    bc = raw.get("birth_chart", raw)
    bodies = []
    for key in _BODIES:
        b = bc.get(key)
        if isinstance(b, dict):
            bodies.append(
                {
                    "name": b.get("name", key.capitalize()),
                    "sign": b.get("sign"),
                    "emoji": b.get("emoji"),
                    "house": b.get("house"),
                    "retrograde": bool(b.get("retrograde", False)),
                    "element": b.get("element"),
                }
            )
    sun = bc.get("sun", {})
    moon = bc.get("moon", {})
    asc = bc.get("ascendant", {})
    return {
        "sun_sign": sun.get("sign"),
        "moon_sign": moon.get("sign"),
        "rising_sign": asc.get("sign"),
        "house_system": bc.get("houses_system_name"),
        "zodiac_type": bc.get("zodiac_type"),
        "bodies": bodies,
    }


@router.post("/chart")
async def create_chart(body: ChartRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    ensure_profile(sb, user.id)
    birth = resolve_birth(sb, user.id, body.birth)
    provider = get_astro_provider()
    raw = await provider.natal_chart(birth)

    sb.table("charts").insert(
        {"user_id": user.id, "raw_json": raw, "provider": provider.name}
    ).execute()
    # Ham sağlayıcı yorumu kullanıcıya gösterilmez; yalnızca kompakt özet döner.
    return {"provider": provider.name, "snapshot": _snapshot(raw)}


@router.get("/chart/svg")
async def chart_svg(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    birth = resolve_birth(sb, user.id, None)
    svg = await get_astro_provider().natal_chart_svg(birth, theme="dark")
    return Response(content=svg, media_type="image/svg+xml")

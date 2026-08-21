"""Natal chart hesapla/kaydet + AI yorumu + istemciye gösterilebilir özet."""
import json
from typing import Any

from fastapi import APIRouter, Depends, Response

from app.api._helpers import resolve_birth
from app.db.supabase_client import (
    _first_row,
    ensure_profile,
    get_profile,
    get_supabase,
)
from app.deps import CurrentUser, current_user
from app.models import ChartRequest
from app.services import wallet
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
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
                    "key": key,  # gezegen tıklama detayı için (/planet/{key})
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


@router.get("/chart")
async def get_chart(user: CurrentUser = Depends(current_user)):
    """Kullanıcının KAYITLI doğum haritasını döner (yeniden hesaplamadan).

    İlk girişte hesaplanıp kaydedilir; her ziyarette buradan gösterilir.
    """
    sb = get_supabase()
    row = _first_row(
        sb.table("charts")
        .select("display,raw_json")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not row:
        return {"exists": False}
    display = row.get("display")
    if display:
        return {"exists": True, **display}
    # Eski kayıt (display yok): en azından snapshot türet.
    return {
        "exists": True,
        "snapshot": _snapshot(row.get("raw_json") or {}),
        "interpretation": None,
        "svg": None,
    }


@router.post("/chart")
async def create_chart(body: ChartRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    ensure_profile(sb, user.id)

    # Mevcut kayıtlı (kendi) harita var mı? İlk harita bir kez ödenir; yeniden
    # oluşturma (kendisi ya da başkası) her seferinde stardust ister.
    existing = _first_row(
        sb.table("charts").select("id").eq("user_id", user.id).limit(1).execute()
    )
    is_first = body.for_self and existing is None
    # İlk (kendi) harita ÜCRETSİZ — onboarding değeri. Yeniden-oluşturma ya da
    # başkası için harita her seferinde stardust ister.
    if not is_first:
        wallet.check_access(sb, user.id, "natal", unlock_key=None)  # yetersizse 402

    birth = resolve_birth(sb, user.id, body.birth)
    provider = get_astro_provider()
    raw = await provider.natal_chart(birth)
    snap = _snapshot(raw)

    # Kişiselleştirilmiş AI natal yorumu.
    interpretation: dict[str, Any] | None = None
    try:
        profile = get_profile(sb, user.id) or {}
        recalled = await recall(sb, user.id, "natal harita kişilik temaları")
        context = build_context_block(
            profile, recalled, {"Natal özet": json.dumps(snap, ensure_ascii=False)}
        )
        interpretation = await complete_json(prompts.NATAL, context)
    except Exception:
        interpretation = None  # yorum başarısız olsa da snapshot/svg dönmeli

    # Natal wheel SVG (koyu tema).
    svg: str | None = None
    try:
        svg = (await provider.natal_chart_svg(birth, theme="dark")).decode("utf-8")
    except Exception:
        svg = None

    display = {"snapshot": snap, "interpretation": interpretation, "svg": svg}

    if body.for_self:
        # KENDİ haritası: eskiyi sil, yenisini kaydet (tek kanonik harita).
        try:
            sb.table("charts").delete().eq("user_id", user.id).execute()
        except Exception:
            pass
        sb.table("charts").insert(
            {
                "user_id": user.id,
                "raw_json": raw,
                "provider": provider.name,
                "display": display,
            }
        ).execute()
        # Cosmic Memory: yalnız KENDİ haritası hafızaya (AI sohbet bilsin).
        bodies_txt = ", ".join(
            f"{b['name']} {b['sign']}{' ℞' if b.get('retrograde') else ''}"
            for b in snap.get("bodies", [])
        )
        summary = (
            f"Natal harita — Güneş {snap.get('sun_sign')}, Ay {snap.get('moon_sign')}, "
            f"Yükselen {snap.get('rising_sign') or '?'}. Gezegenler: {bodies_txt}."
        )
        try:
            await remember(sb, user.id, "chart", summary)
        except Exception:
            pass
    # body.for_self False → BAŞKASI için: hesaba KAYDETME (tek seferlik).

    if is_first:
        charge = {"charged": False, "cost": 0,
                  "balance": wallet.get_balance(sb, user.id)}
    else:
        charge = wallet.commit_charge(sb, user.id, "natal", None)

    return {
        "provider": provider.name,
        "snapshot": snap,
        "interpretation": interpretation,
        "svg": svg,
        "saved": body.for_self,
        "is_first": is_first,
        "charge": charge,
    }


@router.get("/chart/svg")
async def chart_svg(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    birth = resolve_birth(sb, user.id, None)
    svg = await get_astro_provider().natal_chart_svg(birth, theme="dark")
    return Response(content=svg, media_type="image/svg+xml")

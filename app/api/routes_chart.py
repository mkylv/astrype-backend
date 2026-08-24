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


# İnteraktif doğum haritası çarkı için geometri (design_handoff_interactive_natal_chart).
_GEO_PLANETS = [
    "sun", "moon", "mercury", "venus", "mars", "jupiter",
    "saturn", "uranus", "neptune", "pluto",
]
_HOUSE_KEYS = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]
_HOUSE_NUM = {
    "First": 1, "Second": 2, "Third": 3, "Fourth": 4, "Fifth": 5, "Sixth": 6,
    "Seventh": 7, "Eighth": 8, "Ninth": 9, "Tenth": 10, "Eleventh": 11,
    "Twelfth": 12,
}
# (tam açı, ad, sembol, kategori H/T/N, orb toleransı derece)
_ASPECT_DEFS = [
    (0, "Conjunction", "☌", "N", 8.0),
    (60, "Sextile", "✶", "H", 5.0),
    (90, "Square", "□", "T", 7.0),
    (120, "Trine", "△", "H", 7.0),
    (180, "Opposition", "☍", "T", 8.0),
]


# Burç adı (tam veya 3-harf) -> 0..11 indeks; abs_pos yoksa hesaplamak için.
_SIGN_IDX = {}
for _i, (_full, _abbr) in enumerate([
    ("Aries", "Ari"), ("Taurus", "Tau"), ("Gemini", "Gem"), ("Cancer", "Can"),
    ("Leo", "Leo"), ("Virgo", "Vir"), ("Libra", "Lib"), ("Scorpio", "Sco"),
    ("Sagittarius", "Sag"), ("Capricorn", "Cap"), ("Aquarius", "Aqu"),
    ("Pisces", "Pis"),
]):
    _SIGN_IDX[_full] = _i
    _SIGN_IDX[_abbr] = _i


def _abs(obj: dict[str, Any]) -> float | None:
    """Noktanın mutlak boylamı: abs_pos varsa onu, yoksa burç+dereceden hesapla
    (eski indirgenmiş haritalar abs_pos taşımıyor)."""
    ap = obj.get("abs_pos")
    if ap is not None:
        return float(ap)
    idx = _SIGN_IDX.get(obj.get("sign"))
    pos = obj.get("position")
    if idx is None or pos is None:
        return None
    return (idx * 30.0 + float(pos)) % 360.0


def _deg_str(abs_pos: float | None) -> str:
    """Mutlak boylamdan burç-içi 'DD°MM'' üretir."""
    if abs_pos is None:
        return ""
    pos = abs_pos % 30.0
    d = int(pos)
    m = int(round((pos - d) * 60))
    if m == 60:
        d += 1
        m = 0
    return f"{d}°{m:02d}'"


def _house_num(house_str: str | None) -> int:
    return _HOUSE_NUM.get((house_str or "").split("_")[0], 0)


def _geometry(raw: dict[str, Any]) -> dict[str, Any]:
    """Çark için ham geometri: gezegen boylamları, ev köşeleri, açılar,
    hesaplanmış major aspect'ler. Renk/glyph/stil Flutter tarafında."""
    bc = raw.get("birth_chart", raw)
    planets: list[dict[str, Any]] = []
    for key in _GEO_PLANETS:
        b = bc.get(key)
        if not isinstance(b, dict):
            continue
        lon = _abs(b)
        if lon is None:
            continue
        planets.append(
            {
                "key": key,
                "name": b.get("name", key.capitalize()),
                "lon": lon,
                "sign": b.get("sign"),
                "deg": _deg_str(lon),
                "house": _house_num(b.get("house")),
                "retro": bool(b.get("retrograde", False)),
                "element": b.get("element"),
            }
        )

    asc_obj = bc.get("ascendant") if isinstance(bc.get("ascendant"), dict) else {}
    asc_lon = _abs(asc_obj)

    houses: list[dict[str, Any]] = []
    for i, hk in enumerate(_HOUSE_KEYS, start=1):
        h = bc.get(hk)
        if isinstance(h, dict) and _abs(h) is not None:
            houses.append({"num": i, "cusp": _abs(h), "sign": h.get("sign")})
    # Ev köşesi yoksa (eski indirgenmiş harita) ASC'den eşit-ev türet.
    if not houses and asc_lon is not None:
        houses = [
            {"num": i, "cusp": (asc_lon + (i - 1) * 30.0) % 360.0, "sign": None}
            for i in range(1, 13)
        ]

    def _ang(o: Any, fallback: float | None = None) -> dict[str, Any]:
        o = o if isinstance(o, dict) else {}
        lon = _abs(o)
        if lon is None:
            lon = fallback
        return {"lon": lon, "sign": o.get("sign"), "deg": _deg_str(lon)}

    _f = lambda off: (asc_lon + off) % 360.0 if asc_lon is not None else None  # noqa: E731
    angles = {
        "asc": _ang(asc_obj),
        "dsc": _ang(bc.get("descendant"), _f(180)),
        "mc": _ang(bc.get("medium_coeli"), _f(270)),
        "ic": _ang(bc.get("imum_coeli"), _f(90)),
    }

    aspects: list[dict[str, Any]] = []
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            la, lb = planets[i]["lon"], planets[j]["lon"]
            d = abs(la - lb) % 360
            if d > 180:
                d = 360 - d
            for exact, name, sym, cat, orb in _ASPECT_DEFS:
                if abs(d - exact) <= orb:
                    aspects.append(
                        {
                            "a": planets[i]["key"],
                            "b": planets[j]["key"],
                            "type": name,
                            "sym": sym,
                            "orb": f"{abs(d - exact):.1f}°",
                            "cat": cat,
                        }
                    )
                    break
    return {
        "asc": asc_lon,
        "planets": planets,
        "houses": houses,
        "angles": angles,
        "aspects": aspects,
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
    raw = row.get("raw_json") or {}
    if display:
        # Eski display'de geometri yoksa raw_json'dan türet (interaktif çark).
        if not display.get("geometry") and raw:
            try:
                display = {**display, "geometry": _geometry(raw)}
            except Exception:
                pass
        return {"exists": True, **display}
    # Eski kayıt (display yok): en azından snapshot + geometri türet.
    return {
        "exists": True,
        "snapshot": _snapshot(raw),
        "interpretation": None,
        "svg": None,
        "geometry": _geometry(raw) if raw else None,
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

    display = {
        "snapshot": snap,
        "interpretation": interpretation,
        "svg": svg,
        "geometry": _geometry(raw),
    }

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

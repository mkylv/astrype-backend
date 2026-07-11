"""Burç yorumu + günlük harita — maliyet için modül-içi bellek cache'i.

Günlük/aylık burç yorumu burç bazında ÜRETİLİR (kullanıcıya özel değil), böylece
günde en fazla 12 üretim olur; global sözlükte cache'lenir. /sky/today ise
kişiseldir (natal + transit) ve kullanıcı+tarih bazında cache'lenir.
"""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.api._helpers import resolve_birth
from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.astro import get_astro_provider
from app.services.astro.signs import normalize_sign, sign_tr, sun_sign_from_date

router = APIRouter(tags=["horoscope"])

# Modül-içi cache'ler (süreç ömrü boyunca). Anahtarlar tarih/ayı içerir; bayat
# anahtarlar birikir, tek süreç için sorun değil.
_daily_cache: dict[tuple[str, str], dict] = {}    # (sign_key, date) -> response
_monthly_cache: dict[tuple[str, str], dict] = {}  # (sign_key, month) -> response
_sky_cache: dict[tuple[str, str], dict] = {}      # (user_id, date) -> response

# Türkçe ay adları (aylık burç context'i için).
_TR_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
_TR_WEEKDAYS = [
    "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar",
]


def _resolve_sign_key(sb, user_id: str, sign: str | None) -> str:
    """sign verilmişse normalize et; yoksa profildeki doğum tarihinden çöz."""
    if sign:
        key = normalize_sign(sign)
        if key is None:
            raise HTTPException(status_code=400, detail="Geçersiz burç.")
        return key
    profile = get_profile(sb, user_id)
    if profile and profile.get("birth_date"):
        key, _ = sun_sign_from_date(date.fromisoformat(str(profile["birth_date"])[:10]))
        return key
    raise HTTPException(
        status_code=400,
        detail="Burç belirlenemedi — doğum tarihi ekleyin veya burç seçin.",
    )


@router.get("/horoscope/daily")
async def horoscope_daily(
    sign: str | None = None, user: CurrentUser = Depends(current_user)
):
    sb = get_supabase()
    sign_key = _resolve_sign_key(sb, user.id, sign)
    name_tr = sign_tr(sign_key)
    today = date.today().isoformat()

    cached = _daily_cache.get((sign_key, today))
    if cached is not None:
        return cached

    d = date.today()
    context = (
        f"Burç: {name_tr}\n"
        f"Tarih: {today} ({_TR_WEEKDAYS[d.weekday()]})"
    )
    content = await complete_json(prompts.HOROSCOPE_DAILY, context)

    resp = {"sign_key": sign_key, "sign": name_tr, "date": today, "content": content}
    _daily_cache[(sign_key, today)] = resp
    return resp


@router.get("/horoscope/monthly")
async def horoscope_monthly(
    sign: str | None = None, user: CurrentUser = Depends(current_user)
):
    sb = get_supabase()
    sign_key = _resolve_sign_key(sb, user.id, sign)
    name_tr = sign_tr(sign_key)
    d = date.today()
    month = d.strftime("%Y-%m")

    cached = _monthly_cache.get((sign_key, month))
    if cached is not None:
        return cached

    context = f"Burç: {name_tr}\nAy: {_TR_MONTHS[d.month - 1]} {d.year}"
    content = await complete_json(prompts.HOROSCOPE_MONTHLY, context)

    resp = {"sign_key": sign_key, "sign": name_tr, "month": month, "content": content}
    _monthly_cache[(sign_key, month)] = resp
    return resp


@router.get("/sky/today")
async def sky_today(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    try:
        birth = resolve_birth(sb, user.id, None)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Önce doğum bilgini ekle.")

    today = date.today().isoformat()
    cached = _sky_cache.get((user.id, today))
    if cached is not None:
        return cached

    provider = get_astro_provider()
    transits = await provider.daily_transits(birth, today)

    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, "bugünün gökyüzü ve kişisel odak")
    context = build_context_block(
        profile, recalled, {"Günün transitleri": json.dumps(transits)[:4000]}
    )
    content = await complete_json(prompts.SKY_TODAY, context)

    await remember(
        sb, user.id, "chart", f"Günlük gökyüzü ({today}): {content.get('summary', '')}"
    )

    resp = {"date": today, "content": content}
    _sky_cache[(user.id, today)] = resp
    return resp

"""Numeroloji — saf Pythagorean hesap + OpenAI Astrype yorumu (Cosmic Memory'li)."""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import NumerologyRequest
from app.services import numerology
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json

router = APIRouter(tags=["numerology"])


def _parse_date(value) -> date | None:
    """Supabase'ten gelen str / date değerini date'e çevirir."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


@router.post("/numerology")
async def create_numerology(
    body: NumerologyRequest, user: CurrentUser = Depends(current_user)
):
    sb = get_supabase()
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}

    # Profil > body önceliği.
    full_name = profile.get("display_name") or body.full_name
    birth_date = _parse_date(profile.get("birth_date")) or body.birth_date

    if not full_name:
        raise HTTPException(status_code=400, detail="full_name gerekli (profil veya body).")
    if not birth_date:
        raise HTTPException(status_code=400, detail="birth_date gerekli (profil veya body).")

    # 1) Saf, deterministik numeroloji hesabı.
    numbers = numerology.full_profile(full_name, birth_date, date.today())

    # 2) Ham sayıları + Cosmic Memory context'ini OpenAI'a verip Astrype yorumu üret.
    recalled = await recall(sb, user.id, "numeroloji çekirdek sayıları ve yaşam teması")
    context = build_context_block(
        profile,
        recalled,
        {"Numeroloji sayıları": json.dumps(numbers, ensure_ascii=False)},
    )
    result = await complete_json(prompts.NUMEROLOGY, context)

    # 3) Arşivle + hafıza. type='numerology' CHECK ile reddedilirse input_meta'ya düşür.
    record = {"user_id": user.id, "input_meta": {"numbers": numbers}, "result": result}
    try:
        sb.table("readings").insert({**record, "type": "numerology"}).execute()
    except Exception:
        fallback = dict(record)
        fallback["input_meta"] = {"kind": "numerology", "numbers": numbers}
        sb.table("readings").insert({**fallback, "type": "reading"}).execute()
    await remember(sb, user.id, "numerology", f"Numeroloji: {result.get('summary', '')}")

    return {"numbers": numbers, "result": result}

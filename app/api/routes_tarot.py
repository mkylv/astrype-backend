"""Tarot — RapidAPI okuması (görselli) + OpenAI Astrype yorumu."""
import json

from fastapi import APIRouter, Depends

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import TarotPullRequest, TarotSpreadRequest
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.tarot_api import fetch_tarot

router = APIRouter(tags=["tarot"])


async def _reading(sb, user: CurrentUser, question: str | None):
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}
    name = profile.get("display_name") or "Friend"
    dob = str(profile.get("birth_date") or "2000-01-01")

    # 1) RapidAPI tarot okuması (görseller + temel anlamlar)
    reading = await fetch_tarot(name, dob, mode="random")
    cards = reading.get("reading", [])
    backcover = reading.get("card_backcover")

    # 2) Kartları + temel anlamları OpenAI'a verip Astrype yorumu üret
    recalled = await recall(sb, user.id, question or "tarot açılımı genel tema")
    base = [
        {
            "card": c.get("card"),
            "position": c.get("position"),
            "reversed": c.get("reversed"),
            "meaning": c.get("meaning"),
        }
        for c in cards
    ]
    context = build_context_block(
        profile,
        recalled,
        {"Kartlar (API)": json.dumps(base, ensure_ascii=False), "Soru": question or "(genel)"},
    )
    result = await complete_json(prompts.TAROT, context)

    # 3) Arşivle + hafıza (görsel saklamadan, sadece kart adları + sonuç)
    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "tarot",
            "input_meta": {"cards": base, "question": question},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Tarot: {result.get('summary', '')}")

    # İstemciye görselli kartlar + AI yorumu
    return {"cards": cards, "backcover": backcover, "result": result}


@router.post("/tarot/spread")
async def tarot_spread(body: TarotSpreadRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    return await _reading(sb, user, body.question)


@router.post("/tarot/pull")
async def tarot_pull(body: TarotPullRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    return await _reading(sb, user, body.question)

"""Tarot — lokal RWS desteden çekim + OpenAI Astrype yorumu."""
import json

from fastapi import APIRouter, Depends

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import TarotPullRequest, TarotSpreadRequest
from app.services import tarot
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json

router = APIRouter(tags=["tarot"])

_SPREAD_POSITIONS = ["past", "present", "future"]


async def _reading(sb, user: CurrentUser, question: str | None, count: int):
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}

    # 1) Lokal desteden tekrarsız kart çek (görsel slug'lar dahil)
    cards = tarot.draw(count)

    # 2) Temel anlamları OpenAI'a verip Astrype yorumu üret
    recalled = await recall(sb, user.id, question or "tarot açılımı genel tema")
    base = []
    for i, c in enumerate(cards):
        position = _SPREAD_POSITIONS[i] if count > 1 and i < len(_SPREAD_POSITIONS) else "single"
        base.append({
            "card": c["name"],
            "position": position,
            "reversed": c["orientation"] == "reversed",
            "meaning": c["meaning"],
        })
    context = build_context_block(
        profile,
        recalled,
        {"Kartlar": json.dumps(base, ensure_ascii=False), "Soru": question or "(genel)"},
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

    # İstemciye zengin kartlar + AI yorumu
    return {"cards": cards, "result": result}


@router.post("/tarot/spread")
async def tarot_spread(body: TarotSpreadRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    return await _reading(sb, user, body.question, count=3)


@router.post("/tarot/pull")
async def tarot_pull(body: TarotPullRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    return await _reading(sb, user, body.question, count=1)

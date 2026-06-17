"""Tarot — tek kart ve üç kart açılımı."""
import json

from fastapi import APIRouter, Depends

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import TarotPullRequest, TarotSpreadRequest
from app.services import tarot
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json

router = APIRouter(tags=["tarot"])


async def _interpret(sb, user: CurrentUser, cards: list[dict], question: str | None):
    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, question or "tarot açılımı genel tema")
    context = build_context_block(
        profile,
        recalled,
        {"Çekilen kartlar": json.dumps(cards), "Soru": question or "(genel)"},
    )
    result = await complete_json(prompts.TAROT, context)

    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "tarot",
            "input_meta": {"cards": cards, "question": question},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Tarot: {result.get('summary', '')}")
    return {"cards": cards, "result": result}


@router.post("/tarot/pull")
async def tarot_pull(body: TarotPullRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    cards = tarot.draw(1)
    return await _interpret(sb, user, cards, body.question)


@router.post("/tarot/spread")
async def tarot_spread(body: TarotSpreadRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    cards = tarot.draw(3)  # geçmiş / şimdi / gelecek
    return await _interpret(sb, user, cards, body.question)

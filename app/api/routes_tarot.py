"""Tarot — lokal RWS desteden çekim + OpenAI Astrype yorumu."""
import json

from fastapi import APIRouter, Depends

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user, require_feature
from app.models import TarotPullRequest, TarotSpreadRequest
from app.services import tarot, wallet
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json

router = APIRouter(tags=["tarot"])

# Odağa göre pozisyon adları (revizyon §3).
_POS_GENERAL = ["past", "present", "future"]
_POS_FOCUSED = ["current_energy", "obstacle", "advice"]
_POS_SINGLE_Q = ["root", "hidden_factor", "likely_path"]

_FOCUS_TR = {
    "general": "Genel",
    "love": "Aşk",
    "career": "Kariyer",
    "wellness": "Sağlık",
    "single_question": "Tek Soru",
}


def _positions(focus: str | None, count: int) -> list[str]:
    if count == 1:
        return ["single"]
    if focus == "single_question":
        return _POS_SINGLE_Q
    if focus in ("love", "career", "wellness"):
        return _POS_FOCUSED
    return _POS_GENERAL


async def _reading(
    sb, user: CurrentUser, question: str | None, count: int, focus: str | None
):
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}

    # 1) Lokal desteden tekrarsız kart çek (görsel slug'lar dahil)
    cards = tarot.draw(count)

    # 2) Temel anlamları OpenAI'a verip Astrype yorumu üret (odağa göre)
    positions = _positions(focus, count)
    recalled = await recall(sb, user.id, question or "tarot açılımı genel tema")
    base = []
    for i, c in enumerate(cards):
        position = positions[i] if i < len(positions) else "single"
        base.append({
            "card": c["name"],
            "position": position,
            "reversed": c["orientation"] == "reversed",
            "meaning": c["meaning"],
        })
    focus_tr = _FOCUS_TR.get(focus or "general", "Genel")
    context = build_context_block(
        profile,
        recalled,
        {
            "Odak": focus_tr,
            "Kartlar": json.dumps(base, ensure_ascii=False),
            "Soru": question if focus == "single_question" and question else "(yok)",
        },
    )
    result = await complete_json(prompts.TAROT, context)

    # 3) Arşivle + hafıza (görsel saklamadan, sadece kart adları + sonuç)
    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "tarot",
            "input_meta": {"cards": base, "question": question, "focus": focus},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Tarot ({focus_tr}): {result.get('summary', '')}")

    # İstemciye zengin kartlar + AI yorumu + coin düşümü
    charge = wallet.commit_charge(sb, user.id, "tarot")
    return {"cards": cards, "result": result, "charge": charge}


@router.post("/tarot/spread")
async def tarot_spread(
    body: TarotSpreadRequest, user: CurrentUser = Depends(require_feature("tarot"))
):
    sb = get_supabase()
    return await _reading(sb, user, body.question, count=3, focus=body.focus)


@router.post("/tarot/pull")
async def tarot_pull(
    body: TarotPullRequest, user: CurrentUser = Depends(require_feature("tarot"))
):
    sb = get_supabase()
    return await _reading(sb, user, body.question, count=1, focus=body.focus)

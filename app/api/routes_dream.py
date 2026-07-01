"""Rüya yorumu — metin anlatım + mod (psikoloji/mistik) → Lyra yorumu."""
from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import DreamRequest
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json

router = APIRouter(tags=["dream"])


@router.post("/reading/dream")
async def dream_reading(body: DreamRequest, user: CurrentUser = Depends(current_user)):
    dream = (body.dream or "").strip()
    if len(dream) < 10:
        raise HTTPException(status_code=400, detail="Rüyanı birkaç cümleyle anlat.")

    sb = get_supabase()
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, f"rüya teması: {dream[:200]}")
    context = build_context_block(
        profile,
        recalled,
        {"Rüya": dream, "mode": body.mode},
    )
    result = await complete_json(prompts.DREAM, context)

    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "dream",
            "input_meta": {"dream": dream[:2000], "mode": body.mode},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Rüya ({body.mode}): {result.get('summary', '')}")
    return {"result": result}

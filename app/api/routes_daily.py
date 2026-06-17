"""Günlük kişisel yorum — gün boyu cache'li (maliyet kontrolü)."""
import json
from datetime import date as date_cls

from fastapi import APIRouter, Depends

from app.api._helpers import resolve_birth
from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.astro import get_astro_provider

router = APIRouter(tags=["daily"])


@router.get("/daily-insight")
async def daily_insight(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    today = date_cls.today().isoformat()

    # 1) Cache: aynı kullanıcı + tarih için tek üretim.
    cached = (
        sb.table("daily_insight_cache")
        .select("content")
        .eq("user_id", user.id)
        .eq("insight_date", today)
        .limit(1)
        .execute()
    )
    if cached.data:
        return {"cached": True, "content": cached.data[0]["content"]}

    # 2) Ham astro + Cosmic Memory context.
    profile = get_profile(sb, user.id)
    birth = resolve_birth(sb, user.id, None)
    provider = get_astro_provider()
    transits = await provider.daily_transits(birth, today)
    recalled = await recall(sb, user.id, "bugünün genel teması ve kişisel öncelikler")
    context = build_context_block(profile, recalled, {"Günün transitleri": json.dumps(transits)[:4000]})

    # 3) OpenAI -> kişiselleştirilmiş yorum (safety client içinde).
    content = await complete_json(prompts.DAILY_INSIGHT, context)

    # 4) Cache'le.
    sb.table("daily_insight_cache").upsert(
        {"user_id": user.id, "insight_date": today, "content": content},
        on_conflict="user_id,insight_date",
    ).execute()

    # 5) Anlamlı özeti Cosmic Memory'ye yaz.
    await remember(sb, user.id, "chart", f"Günlük yorum ({today}): {content.get('summary', '')}")

    return {"cached": False, "content": content}

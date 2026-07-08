"""Bilinçaltı Keşfi — 4 adımlı gölge testi + doğum haritası harmanı + Lyra.

Akış: GET /subconscious/test → test soruları. POST /subconscious → cevapları
puanla, natal Güneş/Ay/Satürn ile birleştir, LLM'den Jungcu rapor JSON'u üret.
Sonuç Cosmic Memory'ye yazılır; Lyra sohbeti birincil gölgeyi bilerek başlar.
"""
import json
from typing import Any

from fastapi import APIRouter, Depends

from app.api._helpers import resolve_birth
from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import SubconsciousRequest
from app.services.ai import prompts
from app.services.ai.memory import recall, remember
from app.services.ai.openai_client import complete_json
from app.services.astro import get_astro_provider
from app.services.subconscious.engine import (
    SHADOW_CATEGORY,
    SHADOWS,
    TEST,
    rank_shadows,
    sign_element,
)

router = APIRouter(tags=["subconscious"])


@router.get("/subconscious/test")
async def subconscious_test():
    """Frontend'in render edeceği 4 adımlı test verisi."""
    return {"test": TEST}


async def _natal_signs(sb, user_id: str) -> dict[str, Any]:
    """Güneş/Ay/Satürn burçlarını cache'ten al; yoksa profilden hesapla."""
    chart = (
        sb.table("charts")
        .select("raw_json")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    bc = None
    if chart.data:
        bc = (chart.data[0].get("raw_json") or {}).get("birth_chart")
    if not bc:
        try:
            birth = resolve_birth(sb, user_id, None)
            raw = await get_astro_provider().natal_chart(birth)
            bc = raw.get("birth_chart", raw)
        except Exception:
            bc = {}

    def sign(k: str) -> str | None:
        return (bc.get(k) or {}).get("sign")

    return {"sun": sign("sun"), "moon": sign("moon"), "saturn": sign("saturn")}


@router.post("/subconscious")
async def subconscious(body: SubconsciousRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}

    natal = await _natal_signs(sb, user.id)
    ranked, counts = rank_shadows(body.answers, natal.get("sun"), natal.get("moon"))
    primary, secondary, tertiary = ranked[0], ranked[1], ranked[2]

    def shadow_line(key: str, rank: str) -> str:
        return f"{rank}: {SHADOWS[key]} ({key}) — alan: {SHADOW_CATEGORY[key]}"

    recalled = await recall(sb, user.id, "bilinçaltı gölge arketip kader temaları")
    context_parts = [
        f"Güneş Burcu: {natal.get('sun')} ({sign_element(natal.get('sun'))})",
        f"Ay Burcu: {natal.get('moon')} ({sign_element(natal.get('moon'))})",
        f"Satürn Burcu: {natal.get('saturn')}",
        shadow_line(primary, "Birincil Gölge"),
        shadow_line(secondary, "İkincil Gölge"),
        shadow_line(tertiary, "Üçüncül Gölge"),
        f"Ham puanlar: {json.dumps(counts, ensure_ascii=False)}",
    ]
    if profile.get("display_name"):
        context_parts.insert(0, f"İsim: {profile['display_name']}")
    if recalled:
        context_parts.append("Geçmiş içgörüler:\n- " + "\n- ".join(recalled))
    context = "\n".join(context_parts)

    result = await complete_json(prompts.SUBCONSCIOUS, context)

    # Kayıtlar arşivi + Cosmic Memory (Lyra birincil gölgeyi hatırlasın).
    record = {
        "user_id": user.id,
        "input_meta": {"ranked": ranked, "counts": counts, "natal": natal},
        "result": result,
    }
    try:
        sb.table("readings").insert({**record, "type": "subconscious"}).execute()
    except Exception:
        try:
            sb.table("readings").insert({**record, "type": "reading"}).execute()
        except Exception:
            pass

    summary = (result.get("user_summary") or {}).get("intro_text", "")
    await remember(
        sb, user.id, "chat",
        f"Bilinçaltı testi: birincil gölge '{SHADOWS[primary]}' ({SHADOW_CATEGORY[primary]}), "
        f"ikincil '{SHADOWS[secondary]}', üçüncül '{SHADOWS[tertiary]}'. {summary}",
    )

    return {
        "ranked": ranked,
        "counts": counts,
        "primary_shadow": {"key": primary, "name": SHADOWS[primary]},
        "result": result,
    }

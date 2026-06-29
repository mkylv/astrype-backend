"""İnsan Tasarımı (Human Design) — bodygraph hesabı + AI yorumu (Cosmic Memory'li)."""
import json

from fastapi import APIRouter, Depends

from app.api._helpers import resolve_birth
from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import ChartRequest
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.humandesign.engine import calculate_bodygraph

router = APIRouter(tags=["human-design"])


@router.post("/human-design")
async def human_design(body: ChartRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    ensure_profile(sb, user.id)
    birth = resolve_birth(sb, user.id, body.birth)

    # 1) Bodygraph'ı lokal Swiss Ephemeris ile hesapla.
    bodygraph = calculate_bodygraph(birth)

    # 2) Kompakt özet + Cosmic Memory context → AI yorumu.
    compact = {
        k: bodygraph[k]
        for k in (
            "type", "strategy", "authority", "profile", "signature", "not_self",
            "defined_centers", "undefined_centers", "active_channels", "time_known",
        )
    }
    profile = get_profile(sb, user.id) or {}
    recalled = await recall(sb, user.id, "insan tasarımı tip ve strateji temaları")
    context = build_context_block(
        profile, recalled, {"İnsan Tasarımı": json.dumps(compact, ensure_ascii=False)}
    )
    result = await complete_json(prompts.HUMAN_DESIGN, context)

    # 3) Kayıtlar arşivi + Cosmic Memory.
    record = {
        "user_id": user.id,
        "input_meta": {"type": bodygraph["type"], "profile": bodygraph["profile"]},
        "result": {"bodygraph": compact, "interpretation": result},
    }
    try:
        sb.table("readings").insert({**record, "type": "human_design"}).execute()
    except Exception:
        try:
            sb.table("readings").insert({**record, "type": "reading"}).execute()
        except Exception:
            pass
    await remember(
        sb, user.id, "chart",
        f"İnsan Tasarımı: {bodygraph['type']} {bodygraph['profile']}, "
        f"{bodygraph['authority']} otorite.",
    )

    return {"bodygraph": bodygraph, "result": result}

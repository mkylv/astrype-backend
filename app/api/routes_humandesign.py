"""İnsan Tasarımı (Human Design) — bodygraph hesabı + AI yorumu (Cosmic Memory'li)."""
import json

from fastapi import APIRouter, Depends

from app.api._helpers import resolve_birth
from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import ChartRequest, RelationshipRequest
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.humandesign.engine import (
    calculate_bodygraph,
    calculate_composite,
    calculate_transit,
)

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


@router.post("/human-design/transit")
async def human_design_transit(
    body: ChartRequest, user: CurrentUser = Depends(current_user)
):
    """Bugünün transitinin kullanıcının tasarımına etkisi + AI 'tasarım havası'."""
    sb = get_supabase()
    ensure_profile(sb, user.id)
    birth = resolve_birth(sb, user.id, body.birth)

    transit = calculate_transit(birth)
    profile = get_profile(sb, user.id) or {}
    recalled = await recall(sb, user.id, "insan tasarımı günlük transit teması")
    compact = {
        "type": transit["type"],
        "transit_gates": transit["transit_gates"],
        "highlight_channels": transit["highlight_channels"],
        "date": transit["date"],
    }
    context = build_context_block(
        profile, recalled, {"HD Transit": json.dumps(compact, ensure_ascii=False)}
    )
    result = await complete_json(prompts.HD_TRANSIT, context)
    return {"transit": transit, "result": result}


@router.post("/human-design/composite")
async def human_design_composite(
    body: RelationshipRequest, user: CurrentUser = Depends(current_user)
):
    """İki kişinin tasarımı arası bağlantı (composite) + AI ilişki yorumu."""
    sb = get_supabase()
    ensure_profile(sb, user.id)
    birth = resolve_birth(sb, user.id, None)

    composite = calculate_composite(birth, body.partner_birth)
    profile = get_profile(sb, user.id) or {}
    recalled = await recall(sb, user.id, "insan tasarımı ilişki uyumu temaları")
    context = build_context_block(
        profile, recalled,
        {
            "HD Composite": json.dumps(
                {
                    "person_a": composite["person_a"],
                    "person_b": composite["person_b"],
                    "counts": composite["counts"],
                    "connection_channels": composite["connection_channels"],
                },
                ensure_ascii=False,
            ),
            "Partner": body.partner_name or "(isimsiz)",
        },
    )
    result = await complete_json(prompts.HD_COMPOSITE, context)

    record = {
        "user_id": user.id,
        "input_meta": {"partner": body.partner_name, "counts": composite["counts"]},
        "result": {"composite": composite, "interpretation": result},
    }
    try:
        sb.table("readings").insert({**record, "type": "human_design"}).execute()
    except Exception:
        try:
            sb.table("readings").insert({**record, "type": "reading"}).execute()
        except Exception:
            pass

    return {"composite": composite, "result": result}

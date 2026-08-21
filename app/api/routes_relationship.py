"""İlişki uyumu — sinastri ham veri → AI yorumu."""
import json

from fastapi import APIRouter, Depends

from app.api._helpers import resolve_birth
from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, require_feature
from app.models import RelationshipRequest
from app.services import wallet
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.astro import get_astro_provider

router = APIRouter(tags=["relationship"])


@router.post("/relationship")
async def relationship(
    body: RelationshipRequest, user: CurrentUser = Depends(require_feature("compatibility"))
):
    sb = get_supabase()
    me = resolve_birth(sb, user.id, None)
    synastry_raw = await get_astro_provider().synastry(me, body.partner_birth)

    _KIND_TR = {
        "relationship": "İlişki (aşk/romantik)",
        "business": "İş ortaklığı",
        "friendship": "Arkadaşlık",
    }
    kind_tr = _KIND_TR.get(body.kind or "relationship", "İlişki (aşk/romantik)")

    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, "ilişki uyumu ve ortak temalar")
    context = build_context_block(
        profile,
        recalled,
        {
            "Karşılaştırma türü": kind_tr,
            "Partner": body.partner_name or "(isimsiz)",
            "Sinastri": json.dumps(synastry_raw)[:4000],
        },
    )
    result = await complete_json(prompts.RELATIONSHIP, context)

    sb.table("relationships").insert(
        {
            "user_id": user.id,
            "partner_name": body.partner_name,
            "partner_birth": body.partner_birth.model_dump(mode="json"),
            "synastry_raw": synastry_raw,
            "result": result,
        }
    ).execute()
    await remember(
        sb, user.id, "relationship",
        f"İlişki ({body.partner_name or 'partner'}): {result.get('summary', '')}",
    )
    charge = wallet.commit_charge(sb, user.id, "compatibility")
    return {"result": result, "charge": charge}

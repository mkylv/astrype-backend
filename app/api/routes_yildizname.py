"""Yıldızname — anne ismiyle açılan geleneksel yorum (ebced tabanı + natal destek)."""
import json

from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import YildiznameRequest
from app.services.ai import prompts
from app.services.ai.memory import recall, remember
from app.services.ai.openai_client import complete_json
from app.services.ebced.engine import compute_ebced

router = APIRouter(tags=["yildizname"])


@router.post("/reading/yildizname")
async def yildizname(body: YildiznameRequest, user: CurrentUser = Depends(current_user)):
    mother = (body.mother_name or "").strip()
    if not mother:
        raise HTTPException(status_code=400, detail="Anne adı gerekli.")

    sb = get_supabase()
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}

    # 1) Deterministik taban: anne adının harf/ebced/unsur dökümü.
    mother_ebced = compute_ebced(mother)

    # 2) Doğum haritası desteği (varsa son natal snapshot).
    natal_summary = None
    chart = (
        sb.table("charts")
        .select("raw_json")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if chart.data:
        bc = (chart.data[0].get("raw_json") or {}).get("birth_chart", {})
        natal_summary = {
            k: (bc.get(k) or {}).get("sign")
            for k in ("sun", "moon", "ascendant")
            if (bc.get(k) or {}).get("sign")
        }

    recalled = await recall(sb, user.id, "yıldızname kader kısmet manevi temalar")
    parts = [
        f"Kişi: {profile.get('display_name') or '(isimsiz)'}",
        f"Anne adı: {mother}",
        f"Anne adı harf/ebced dökümü: {json.dumps(mother_ebced, ensure_ascii=False)}",
        f"Doğum: {profile.get('birth_date')} {profile.get('birth_time') or '(saat bilinmiyor)'} {profile.get('birth_place') or ''}",
    ]
    if natal_summary:
        parts.append(f"Natal özet: {json.dumps(natal_summary, ensure_ascii=False)}")
    if recalled:
        parts.append("Geçmiş içgörüler:\n- " + "\n- ".join(recalled))
    context = "\n\n".join(parts)

    result = await complete_json(prompts.YILDIZNAME, context)

    record = {
        "user_id": user.id,
        "input_meta": {"mother": mother, "elements": mother_ebced["elements"]},
        "result": {"ebced": mother_ebced, "interpretation": result},
    }
    try:
        sb.table("readings").insert({**record, "type": "yildizname"}).execute()
    except Exception:
        try:
            sb.table("readings").insert({**record, "type": "reading"}).execute()
        except Exception:
            pass
    await remember(
        sb, user.id, "reading",
        f"Yıldızname (anne: {mother}): {result.get('summary', '')}",
    )
    return {"ebced": mother_ebced, "result": result}

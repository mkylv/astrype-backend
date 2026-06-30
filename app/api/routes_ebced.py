"""Ebced / ilm-i hurûf — deterministik ebced + Gemini (Osmanlı müneccim) yorumu."""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import ensure_profile, get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import EbcedRequest
from app.services.ai import prompts
from app.services.ai.gemini_client import complete_json_gemini
from app.services.ai.memory import recall, remember
from app.services.ebced.engine import compute_ebced

router = APIRouter(tags=["ebced"])


def _parse_date(value) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


@router.post("/ebced")
async def ebced(body: EbcedRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    ensure_profile(sb, user.id)
    profile = get_profile(sb, user.id) or {}

    full_name = (body.full_name or profile.get("display_name") or "").strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="full_name gerekli (profil veya body).")
    mother_name = (body.mother_name or "").strip()

    # 1) Deterministik ebced dökümü (isim + anne adı).
    name_ebced = compute_ebced(full_name)
    mother_ebced = compute_ebced(mother_name) if mother_name else None

    # 2) Doğum bağlamı (yıldızname için) + Cosmic Memory.
    birth_info = {
        "tarih": str(profile.get("birth_date") or ""),
        "saat": str(profile.get("birth_time") or "(bilinmiyor)"),
        "yer": profile.get("birth_place") or "",
    }
    recalled = await recall(sb, user.id, "ebced ilm-i hurûf isim ve kader temaları")

    context_parts = [
        f"Ad Soyad: {full_name}",
        f"Anne adı: {mother_name or '(verilmedi)'}",
        f"Doğum: {json.dumps(birth_info, ensure_ascii=False)}",
        f"İsim ebced dökümü: {json.dumps(name_ebced, ensure_ascii=False)}",
    ]
    if mother_ebced:
        context_parts.append(f"Anne adı ebced: {json.dumps(mother_ebced, ensure_ascii=False)}")
    if recalled:
        context_parts.append("Geçmiş içgörüler:\n- " + "\n- ".join(recalled))
    context = "\n\n".join(context_parts)

    # 3) Gemini (Osmanlı müneccim üslubu) yorumu.
    result = await complete_json_gemini(prompts.EBCED, context)

    # 4) Kayıtlar arşivi + Cosmic Memory.
    record = {
        "user_id": user.id,
        "input_meta": {"name": full_name, "mother": mother_name, "total": name_ebced["total"]},
        "result": {"ebced": name_ebced, "interpretation": result},
    }
    try:
        sb.table("readings").insert({**record, "type": "ebced"}).execute()
    except Exception:
        try:
            sb.table("readings").insert({**record, "type": "reading"}).execute()
        except Exception:
            pass
    await remember(
        sb, user.id, "reading",
        f"Ebced: {full_name} → toplam {name_ebced['total']}, baskın unsur "
        f"{name_ebced['dominant_element']}.",
    )

    return {"ebced": name_ebced, "mother_ebced": mother_ebced, "result": result}

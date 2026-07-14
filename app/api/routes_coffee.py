"""Kahve falı — foto yükle → vision sembol çıkar → FOTO SİL → yorum.

Fotoğraf yalnızca request ömrü boyunca bellekte tutulur; diske/Storage'a
asla yazılmaz. Sadece sembol listesi + metin sonucu arşivlenir.
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, require_premium
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.vision.coffee_palm import extract_coffee_symbols

router = APIRouter(tags=["coffee"])


@router.post("/reading/coffee")
async def coffee_reading(
    photo: UploadFile = File(...),
    note: str | None = Form(default=None),
    user: CurrentUser = Depends(require_premium),
):
    sb = get_supabase()

    # 1) Fotoğrafı belleğe oku.
    image_bytes = await photo.read()
    try:
        # 2) Vision: yalnızca sembol listesi çıkar.
        symbols = await extract_coffee_symbols(image_bytes)
    finally:
        # 3) FOTO SİL: bellekteki referansı bırak (diske hiç yazılmadı).
        image_bytes = b""

    # 4) Sembolleri context'le yorumla.
    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, note or "kahve falı genel tema")
    context = build_context_block(
        profile, recalled, {"Semboller": symbols, "Not": note or "(yok)"}
    )
    result = await complete_json(prompts.COFFEE, context)

    # 5) Arşivle (FOTO YOK — yalnızca sembol + sonuç).
    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "coffee",
            "input_meta": {"symbols": symbols, "note": note},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Kahve falı: {result.get('summary', '')}")
    return {"symbols": symbols, "result": result, "photo_deleted": True}

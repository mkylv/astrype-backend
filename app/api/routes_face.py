"""Yüz falı (sima ilmi) — foto yükle → vision özellik çıkar → FOTO SİL → yorum.

Fotoğraf yalnızca request ömrü boyunca bellekte tutulur; diske/Storage'a asla
yazılmaz. Kimlik tespiti yapılmaz; sadece özellik listesi + metin arşivlenir.
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.vision.coffee_palm import extract_face_features

router = APIRouter(tags=["face"])


@router.post("/reading/face")
async def face_reading(
    photo: UploadFile = File(...),
    note: str | None = Form(default=None),
    user: CurrentUser = Depends(current_user),
):
    sb = get_supabase()

    image_bytes = await photo.read()
    try:
        features = await extract_face_features(image_bytes)
    finally:
        image_bytes = b""  # FOTO SİL — diske hiç yazılmadı.

    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, note or "yüz falı sima ilmi genel tema")
    context = build_context_block(
        profile, recalled, {"Yüz özellikleri": features, "Not": note or "(yok)"}
    )
    result = await complete_json(prompts.FACE, context)

    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "face",
            "input_meta": {"features": features, "note": note},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Yüz falı: {result.get('summary', '')}")
    return {"features": features, "result": result, "photo_deleted": True}

"""El falı — foto yükle → vision çizgi çıkar → FOTO SİL → yorum."""
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.db.supabase_client import get_profile, get_supabase
# TODO(yayın): require_premium'a geri çevrilecek (test dönemi serbest).
from app.deps import CurrentUser, current_user
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.vision.coffee_palm import extract_palm_lines

router = APIRouter(tags=["palm"])


@router.post("/reading/palm")
async def palm_reading(
    photo: UploadFile = File(...),
    note: str | None = Form(default=None),
    user: CurrentUser = Depends(current_user),
):
    sb = get_supabase()

    image_bytes = await photo.read()
    try:
        lines = await extract_palm_lines(image_bytes)
    finally:
        image_bytes = b""  # FOTO SİL — diske hiç yazılmadı.

    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, note or "el falı genel tema")
    context = build_context_block(
        profile, recalled, {"Çizgiler": lines, "Not": note or "(yok)"}
    )
    result = await complete_json(prompts.PALM, context)

    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "palm",
            "input_meta": {"lines": lines, "note": note},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"El falı: {result.get('summary', '')}")
    return {"lines": lines, "result": result, "photo_deleted": True}

"""Kahve falı — 1-3 foto yükle → vision sembol çıkar → FOTO SİL → yorum.

Fotoğraflar yalnızca request ömrü boyunca bellekte tutulur; diske/Storage'a
asla yazılmaz. Sadece sembol listesi + metin sonucu arşivlenir. Revizyon §6.3:
farklı açılardan 3 görsel; hepsinden ortak sembol haritası çıkarılır.
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, require_feature
from app.services import wallet
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.vision.coffee_palm import extract_coffee_symbols

router = APIRouter(tags=["coffee"])

_FOCUS_TR = {
    "general": "Genel",
    "love": "Aşk",
    "career": "Kariyer",
    "wellness": "Sağlık",
    "single_question": "Tek Soru",
}


@router.post("/reading/coffee")
async def coffee_reading(
    photos: list[UploadFile] = File(default=[]),  # yeni: 1-3 görsel
    photo: UploadFile | None = File(default=None),  # eski istemci uyumu (tek foto)
    note: str | None = Form(default=None),
    focus: str | None = Form(default=None),
    user: CurrentUser = Depends(require_feature("coffee")),
):
    sb = get_supabase()

    files = [f for f in (photos or []) if f is not None]
    if not files and photo is not None:
        files = [photo]
    files = files[:3]
    if not files:
        raise HTTPException(status_code=422, detail="En az bir fotoğraf gerekli.")

    # 1) Her görselden sembol çıkar; birleştir (sıra koruyarak benzersizleştir).
    collected: list[str] = []
    for f in files:
        image_bytes = await f.read()
        try:
            collected.extend(await extract_coffee_symbols(image_bytes))
        finally:
            image_bytes = b""  # FOTO SİL — diske hiç yazılmadı.

    seen: set[str] = set()
    symbols: list[str] = []
    for s in collected:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            symbols.append(s)

    # 2) Sembolleri odağa göre context'le yorumla.
    focus_tr = _FOCUS_TR.get(focus or "general", "Genel")
    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, note or "kahve falı genel tema")
    context = build_context_block(
        profile,
        recalled,
        {
            "Odak": focus_tr,
            "Görsel sayısı": str(len(files)),
            "Semboller": symbols,
            "Soru": note if focus == "single_question" and note else "(yok)",
        },
    )
    result = await complete_json(prompts.COFFEE, context)

    # 3) Arşivle (FOTO YOK — yalnızca sembol + sonuç).
    sb.table("readings").insert(
        {
            "user_id": user.id,
            "type": "coffee",
            "input_meta": {"symbols": symbols, "note": note, "focus": focus,
                           "image_count": len(files)},
            "result": result,
        }
    ).execute()
    await remember(sb, user.id, "reading", f"Kahve falı ({focus_tr}): {result.get('summary', '')}")
    charge = wallet.commit_charge(sb, user.id, "coffee")
    return {"symbols": symbols, "result": result, "photo_deleted": True, "charge": charge}

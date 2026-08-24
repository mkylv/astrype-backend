"""Cosmic Memory — embedding + pgvector RAG.

Kural: "her şeyi sakla" değil, yalnızca ANLAMLI analiz özetleri vektörlenir.
Context toplama (recall) ile yazma (remember) burada birleşir.
"""
from typing import Any

from supabase import Client

from app.services.ai.openai_client import embed

# RAG'a eklenecek context için varsayılan üst sınır.
_TOP_K = 6

# Dil kodu -> yanıt dilinin insan-okur adı. Tüm AI modülleri tek noktadan
# kullanıcının seçtiği dile bu talimatla uyar (20 dil).
_LANG_NAMES = {
    "en": "English", "tr": "Türkçe", "es": "Español", "ar": "العربية",
    "hi": "हिन्दी", "pt": "Português", "ru": "Русский", "fr": "Français",
    "de": "Deutsch", "it": "Italiano", "id": "Bahasa Indonesia", "zh": "中文",
    "ja": "日本語", "ko": "한국어", "fa": "فارسی", "ur": "اردو",
    "az": "Azərbaycanca", "uk": "Українська", "pl": "Polski", "nl": "Nederlands",
}

# Birbirine çok yakın diller Luna'yı kaydırıyor (Türkçe sordu, Azerice yanıt).
# Açık ayrım notu.
_LANG_DISAMBIG = {
    "tr": " (Türkiye Türkçesi — Azerice/Azərbaycanca DEĞİL)",
    "az": " (Azərbaycan dili — Türkiyə türkcəsi DEYİL)",
}


async def remember(sb: Client, user_id: str, source: str, summary: str) -> None:
    """Anlamlı bir özeti vektörleyip memory_chunks'a yaz.

    Embedding sağlayıcısı (OpenAI) çökerse sessizce atlanır — hafıza yazımı
    hiçbir modülü çökertmemeli.
    """
    summary = summary.strip()
    if len(summary) < 12:
        return  # çok kısa / anlamsız özetleri saklama
    try:
        vector = await embed(summary)
        sb.table("memory_chunks").insert(
            {
                "user_id": user_id,
                "source": source,
                "summary": summary,
                "embedding": vector,
            }
        ).execute()
    except Exception:
        return  # embedding/DB hatası → hafıza yazımı atlanır


async def recall(sb: Client, user_id: str, query: str, top_k: int = _TOP_K) -> list[str]:
    """Sorguya en yakın geçmiş özetleri döner (pgvector cosine).

    `match_memory` RPC'si migration'da tanımlıdır; RLS yerine açık user_id
    filtresiyle çalışır (backend service-role).
    """
    try:
        vector = await embed(query)
        res = sb.rpc(
            "match_memory",
            {"p_user_id": user_id, "p_query": vector, "p_match_count": top_k},
        ).execute()
        rows: list[dict[str, Any]] = res.data or []
        return [r["summary"] for r in rows]
    except Exception:
        return []  # embedding/RPC hatası → context'siz devam (modül çökmesin)


def build_context_block(
    profile: dict[str, Any] | None,
    recalled: list[str],
    extra: dict[str, Any] | None = None,
) -> str:
    """Profil + RAG özetleri + ek veriyi tek bir context metnine derler."""
    parts: list[str] = []
    if profile:
        parts.append(
            "Profil: "
            f"dil={profile.get('language')}, "
            f"doğum={profile.get('birth_date')} {profile.get('birth_time') or '(saat bilinmiyor)'}, "
            f"yer={profile.get('birth_place')}, "
            f"ilgi={profile.get('interests')}"
        )
    if recalled:
        parts.append("Geçmiş içgörüler:\n- " + "\n- ".join(recalled))
    if extra:
        for k, v in extra.items():
            parts.append(f"{k}: {v}")
    # Dil talimatı HER dilde açıkça verilir (Türkçe dahil) — yoksa Luna yakın
    # dile (Azerice) kayabiliyor. tr/az için ayrım notu eklenir.
    if profile:
        lang = (profile.get("language") or "en").split("-")[0]
        lang_name = _LANG_NAMES.get(lang, lang)
        note = _LANG_DISAMBIG.get(lang, "")
        parts.append(
            f"ÇOK ÖNEMLİ: Tüm yanıtını ve tüm JSON alanlarının metinlerini "
            f"yalnızca {lang_name}{note} dilinde yaz."
        )
    return "\n\n".join(parts) if parts else "(henüz context yok)"

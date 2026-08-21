"""Cosmic Memory'li AI sohbet."""
from fastapi import APIRouter, Depends

from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.models import ChatRequest
from app.services import wallet
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_chat
from app.services.ai.safety import is_crisis_signal

router = APIRouter(tags=["chat"])

_HISTORY_LIMIT = 10


@router.post("/chat")
async def chat(body: ChatRequest, user: CurrentUser = Depends(current_user)):
    sb = get_supabase()

    # Lyra mesaj ücreti: abone günlük hakkı içindeyse ücretsiz, sonrası coin.
    # Yetersiz bakiyede üretimden önce 402 döner.
    charge = wallet.charge_lyra_message(sb, user.id)

    # Son N mesajı kronolojik history olarak al.
    hist = (
        sb.table("chat_messages")
        .select("role,content")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .limit(_HISTORY_LIMIT)
        .execute()
    )
    history = list(reversed(hist.data or []))

    # Cosmic Memory recall + profil -> context.
    profile = get_profile(sb, user.id)
    recalled = await recall(sb, user.id, body.message)

    # En güncel natal haritayı HER ZAMAN context'e ekle (recall'a bağlı kalmadan).
    extra: dict[str, str] = {}
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
        def _sign(k: str) -> str | None:
            return (bc.get(k) or {}).get("sign")
        bodies = ", ".join(
            f"{k.capitalize()} {(bc.get(k) or {}).get('sign')}"
            for k in ("mercury", "venus", "mars", "jupiter", "saturn")
            if (bc.get(k) or {}).get("sign")
        )
        extra["Natal harita"] = (
            f"Güneş {_sign('sun')}, Ay {_sign('moon')}, Yükselen {_sign('ascendant')}"
            + (f"; {bodies}" if bodies else "")
        )

    # Son okumaları (tarot/kahve/rüya/...) HER ZAMAN context'e ekle ki Lyra
    # "ne çektim" gibi soruları hafızadan doğru yanıtlasın (recall'a bağlı kalmadan).
    try:
        recent = (
            sb.table("readings")
            .select("type,input_meta,result,created_at")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        lines = []
        for r in (recent.data or []):
            rtype = r.get("type", "okuma")
            res = r.get("result") or {}
            summ = ""
            if isinstance(res, dict):
                summ = str(res.get("summary") or res.get("direct_answer") or "")[:180]
            meta = r.get("input_meta") or {}
            extra_bit = ""
            if rtype == "tarot" and isinstance(meta, dict):
                cards = meta.get("cards") or []
                names = ", ".join(str(c.get("card")) for c in cards if isinstance(c, dict) and c.get("card"))
                if names:
                    extra_bit = f" (kartlar: {names})"
            if summ or extra_bit:
                lines.append(f"{rtype}{extra_bit}: {summ}")
        if lines:
            extra["Son okumalar"] = "\n  - " + "\n  - ".join(lines)
    except Exception:
        pass  # okuma geçmişi alınamazsa context'siz devam

    context = build_context_block(profile, recalled, extra or None)
    system = f"{prompts.CHAT}\n\n# Kullanıcı Context\n{context}"

    answer = await complete_chat(system, history, body.message)

    # Kullanıcı + asistan mesajlarını kaydet.
    sb.table("chat_messages").insert(
        [
            {"user_id": user.id, "role": "user", "content": body.message},
            {"user_id": user.id, "role": "assistant", "content": answer},
        ]
    ).execute()

    # Kriz sinyali işaretle (yanıt zaten safety promptuyla üretildi).
    crisis = is_crisis_signal(body.message)
    return {"answer": answer, "crisis_support_suggested": crisis, "charge": charge}

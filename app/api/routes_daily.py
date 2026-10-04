"""Günlük kişisel yorum — gün boyu cache'li (maliyet kontrolü).

Hız: yorum üretimi (~15-20 sn, reasoning modeli) kullanıcıyı açılış ekranında
bekletiyordu. Bugünün yorumu servis edildiğinde YARININ yorumu arka planda
hazırlanır → ertesi gün açılış anında cache'ten gelir. Maliyet değişmez
(kullanıcı başına günde bir üretim); yalnızca ertesi gün dönmeyen kullanıcıda
bir üretim boşa gider.
"""
import asyncio
import json
import logging
from datetime import date as date_cls
from datetime import timedelta

from fastapi import APIRouter, Depends

from app.api._helpers import resolve_birth
from app.db.supabase_client import get_profile, get_supabase
from app.deps import CurrentUser, current_user
from app.services import wallet
from app.services.ai import prompts
from app.services.ai.memory import build_context_block, recall, remember
from app.services.ai.openai_client import complete_json
from app.services.astro import get_astro_provider

router = APIRouter(tags=["daily"])
log = logging.getLogger(__name__)

# (user_id, tarih) → üretim görevi. Aynı gün için eşzamanlı istekler (ör. ön
# ısıtma sürerken kullanıcının açması) tek OpenAI çağrısını paylaşır.
_TASKS: dict[tuple[str, str], asyncio.Task] = {}


def _cached(sb, user_id: str, day: str) -> dict | None:
    res = (
        sb.table("daily_insight_cache")
        .select("content")
        .eq("user_id", user_id)
        .eq("insight_date", day)
        .limit(1)
        .execute()
    )
    return res.data[0]["content"] if res.data else None


async def _generate_and_store(user_id: str, day: str) -> dict:
    sb = get_supabase()
    profile = get_profile(sb, user_id)
    birth = resolve_birth(sb, user_id, None)
    transits = await get_astro_provider().daily_transits(birth, day)
    recalled = await recall(sb, user_id, "bugünün genel teması ve kişisel öncelikler")
    context = build_context_block(profile, recalled, {"Günün transitleri": json.dumps(transits)[:4000]})
    content = await complete_json(prompts.DAILY_INSIGHT, context)  # safety client içinde
    sb.table("daily_insight_cache").upsert(
        {"user_id": user_id, "insight_date": day, "content": content},
        on_conflict="user_id,insight_date",
    ).execute()
    return content


def _task(user_id: str, day: str) -> asyncio.Task:
    key = (user_id, day)
    t = _TASKS.get(key)
    if t is None:
        t = asyncio.create_task(_generate_and_store(user_id, day))
        _TASKS[key] = t
        t.add_done_callback(lambda _t: _TASKS.pop(key, None))
    return t


async def _prewarm(user_id: str, day: str) -> None:
    """Verilen günün yorumunu yoksa arka planda hazırla. Hata sessiz geçer —
    o gün kullanıcı açınca normal yoldan yeniden denenir."""
    try:
        if _cached(get_supabase(), user_id, day) is None:
            await _task(user_id, day)
    except Exception as e:  # noqa: BLE001
        log.warning("daily prewarm %s %s: %s", user_id, day, e)


def _schedule_prewarm(user_id: str, today: date_cls) -> None:
    tomorrow = (today + timedelta(days=1)).isoformat()
    if (user_id, tomorrow) not in _TASKS:
        asyncio.create_task(_prewarm(user_id, tomorrow))


@router.get("/daily-insight")
async def daily_insight(user: CurrentUser = Depends(current_user)):
    sb = get_supabase()
    today_d = date_cls.today()
    today = today_d.isoformat()

    # Günlük harita kullanıcı başına günde bir ödenir (continuous → abonede ücretsiz).
    unlock = f"daily_map:{user.id}:{today}"
    wallet.check_access(sb, user.id, "daily_map", unlock_key=unlock)  # yetersizse 402

    # 1) Cache: aynı kullanıcı + tarih için tek üretim (ön ısıtılmış olabilir).
    content = _cached(sb, user.id, today)
    from_cache = content is not None
    if not from_cache:
        # 2-4) Ham astro + Cosmic Memory → OpenAI → cache. Ön ısıtma sürüyorsa
        # aynı görevi bekler; istemci koparsa üretim yine tamamlanır (shield).
        content = await asyncio.shield(_task(user.id, today))
        # 5) Anlamlı özeti Cosmic Memory'ye yaz (yalnızca kendi gününde).
        await remember(sb, user.id, "chart", f"Günlük yorum ({today}): {content.get('summary', '')}")

    _schedule_prewarm(user.id, today_d)
    charge = wallet.commit_charge(sb, user.id, "daily_map", unlock)
    return {"cached": from_cache, "content": content, "charge": charge}

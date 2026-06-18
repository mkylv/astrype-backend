"""The Numerology API (RapidAPI) tarot okuması.

GET /tarot/reading?name=..&dob=YYYY-MM-DD&mode=random
Yanıt: card_backcover + reading[3] {card, image_url, meaning, position, reversed}.

Bu ham kartlar + temel anlamlar OpenAI'a girdi olur (Astrype yorumu); görseller
(image_url, backcover) istemciye iletilir.
"""
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

_TIMEOUT = httpx.Timeout(30.0)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def fetch_tarot(name: str, dob: str, mode: str = "random") -> dict[str, Any]:
    s = get_settings()
    headers = {
        "x-rapidapi-key": s.rapidapi_key,
        "x-rapidapi-host": s.rapidapi_host,
    }
    params = {"name": name or "Friend", "dob": dob, "mode": mode}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(
            f"https://{s.rapidapi_host}/tarot/reading", params=params, headers=headers
        )
        r.raise_for_status()
        return r.json()

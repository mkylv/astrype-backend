"""The Numerology API (RapidAPI / Dakidarts) implementasyonu.

RapidAPI gateway'indeki Birth Chart Report ucu **GET** ve parametreleri
query string'de (11 param): name, year, month, day, hour, minute, lat, lng,
city, country, tz.

Host: the-numerology-api.p.rapidapi.com  (header: x-rapidapi-key/host)

Cevap Kerykeion tarzı tam natal veri döner: birth_chart.{sun,moon,ascendant,
mercury,...} her biri {sign, house, position, retrograde, element, quality}.
Narrative/SVG yok — yalnızca ham veri (spec'e uygun: OpenAI yorumlar).
"""
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import BirthData
from app.services.astro.base import AstroProvider

_TIMEOUT = httpx.Timeout(30.0)


class NumerologyAPIProvider(AstroProvider):
    name = "numerology_api"

    def __init__(self) -> None:
        s = get_settings()
        self._base = f"https://{s.rapidapi_host}"
        self._headers = {
            "x-rapidapi-key": s.rapidapi_key,
            "x-rapidapi-host": s.rapidapi_host,
        }

    def _params(self, birth: BirthData, name: str = "Astrype") -> dict[str, Any]:
        """BirthData -> gateway'in beklediği 11 query parametresi."""
        if birth.birth_time_known and birth.birth_time is not None:
            hour, minute = birth.birth_time.hour, birth.birth_time.minute
        else:
            hour, minute = 12, 0  # saat bilinmiyor: öğlen varsayımı
        return {
            "name": name,
            "year": birth.birth_date.year,
            "month": birth.birth_date.month,
            "day": birth.birth_date.day,
            "hour": hour,
            "minute": minute,
            "lat": birth.lat,
            "lng": birth.lng,
            "city": birth.place or "NA",
            "country": "NA",   # hesaplama lat/lng/tz ile yapılır
            "tz": birth.tz,
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                f"{self._base}{path}", params=params, headers=self._headers
            )
            r.raise_for_status()
            return r.json()

    async def natal_chart(self, birth: BirthData) -> dict[str, Any]:
        """Ham natal chart (gezegen pozisyonları, evler, açılar)."""
        return await self._get("/birth-chart", self._params(birth))

    async def daily_transits(self, birth: BirthData, date: str) -> dict[str, Any]:
        """Bu gateway ucu transit döndürmediğinden natal haritayı + tarihi
        döneriz; günün bağlamını OpenAI natal veriye göre yorumlar."""
        natal = await self.natal_chart(birth)
        return {"date": date, "natal": natal.get("birth_chart", natal)}

    async def synastry(self, a: BirthData, b: BirthData) -> dict[str, Any]:
        """Ayrı sinastri ucu olmadığından iki natal haritayı ham döneriz;
        karşılaştırmayı OpenAI yapar (spec'e uygun)."""
        chart_a = await self.natal_chart(a)
        chart_b = await self.natal_chart(b)
        return {
            "person_a": chart_a.get("birth_chart", chart_a),
            "person_b": chart_b.get("birth_chart", chart_b),
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def natal_chart_svg(self, birth: BirthData, theme: str = "dark") -> bytes:
        """Kerykeion natal wheel SVG'sini döner (GET /birth-chart/svg)."""
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                f"{self._base}/birth-chart/svg",
                params=self._params(birth),
                headers=self._headers,
            )
            r.raise_for_status()
            return r.content

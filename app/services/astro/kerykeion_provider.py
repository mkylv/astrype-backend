"""Lokal Kerykeion (Swiss Ephemeris üzerine) astro sağlayıcısı.

Doğum haritası hesaplaması artık dışa bağımlı RapidAPI yerine **lokal**
yapılır: `pyswisseph` + `kerykeion` ile offline gezegen pozisyonları,
evler, açılar ve natal wheel SVG üretilir.

Çıktı sözleşmesi, eski The Numerology API implementasyonunu BİREBİR taklit
eder; böylece `routes_chart._snapshot` ve OpenAI promptları bozulmaz:

    {"birth_chart": {
        "sun": {name, sign, emoji, house, retrograde, element, quality, position},
        "moon": {...}, "ascendant": {...}, "mercury"..."pluto": {...},
        "houses_system_name": <str>,
        "zodiac_type": <str>,
    }}

Lisans notu: Kerykeion AGPL-3.0 lisanslıdır; pyswisseph (Swiss Ephemeris)
GPL/ticari ikili lisanslıdır. Dağıtım koşullarına dikkat edilmelidir.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import tempfile
from datetime import datetime
from typing import Any

from kerykeion import (
    AstrologicalSubjectFactory,
    KerykeionChartSVG,
    SynastryAspects,
)

from app.models import BirthData
from app.services.astro.base import AstroProvider

# Kerykeion burç kısaltması -> tam ad (snapshot/prompt tutarlılığı için).
_SIGN_FULL = {
    "Ari": "Aries",
    "Tau": "Taurus",
    "Gem": "Gemini",
    "Can": "Cancer",
    "Leo": "Leo",
    "Vir": "Virgo",
    "Lib": "Libra",
    "Sco": "Scorpio",
    "Sag": "Sagittarius",
    "Cap": "Capricorn",
    "Aqu": "Aquarius",
    "Pis": "Pisces",
}

# birth_chart içinde döndürülecek gök cisimleri ve subject attribute adları.
_BODY_ATTRS = {
    "sun": "sun",
    "moon": "moon",
    "ascendant": "ascendant",
    "mercury": "mercury",
    "venus": "venus",
    "mars": "mars",
    "jupiter": "jupiter",
    "saturn": "saturn",
    "uranus": "uranus",
    "neptune": "neptune",
    "pluto": "pluto",
}


_VAR_DEF = re.compile(r"--([\w-]+)\s*:\s*([^;}]+)\s*[;}]")
_VAR_USE = re.compile(r"var\(\s*--([\w-]+)\s*(?:,\s*([^)]+))?\)")


def _flatten_css_vars(svg: str) -> str:
    """Kerykeion SVG'sindeki CSS değişkenlerini (:root --x + var(--x)) gerçek
    hex/değerle düzleştirir. flutter_svg `var()` desteklemediğinden, çözülmemiş
    değişkenler haritayı boş render eder. Burada sunucuda statik olarak çözülür.
    """
    # 1) Tüm --name: value tanımlarını topla (son tanım kazanır).
    defs: dict[str, str] = {m.group(1): m.group(2).strip() for m in _VAR_DEF.finditer(svg)}

    # 2) var() referanslarını özyinelemeli çöz (değişken değişkene bakabilir).
    def resolve(name: str, seen: set[str]) -> str | None:
        if name in seen:
            return None
        val = defs.get(name)
        if val is None:
            return None
        m = _VAR_USE.fullmatch(val.strip())
        if m:
            inner = resolve(m.group(1), seen | {name})
            return inner if inner is not None else (m.group(2).strip() if m.group(2) else None)
        return val

    flat = {k: resolve(k, set()) for k in defs}

    def sub(match: re.Match[str]) -> str:
        name, fallback = match.group(1), match.group(2)
        value = flat.get(name)
        if value is not None:
            return value
        return fallback.strip() if fallback else "none"

    return _VAR_USE.sub(sub, svg)


def _point_to_dict(point: Any) -> dict[str, Any]:
    """Kerykeion point objesini snapshot/prompt sözleşmesine map eder."""
    sign_abbr = getattr(point, "sign", None)
    return {
        "name": getattr(point, "name", None),
        "sign": _SIGN_FULL.get(sign_abbr, sign_abbr),
        "emoji": getattr(point, "emoji", None),
        "house": getattr(point, "house", None),  # ör. "Ninth_House"
        "retrograde": bool(getattr(point, "retrograde", False) or False),
        "element": getattr(point, "element", None),
        "quality": getattr(point, "quality", None),
        "position": getattr(point, "position", None),
    }


class KerykeionProvider(AstroProvider):
    """Lokal Swiss Ephemeris tabanlı astro sağlayıcı."""

    name = "kerykeion"

    def _subject(
        self, birth: BirthData, name: str = "Astrype", date_override: Any = None
    ) -> Any:
        """BirthData -> AstrologicalSubject (lat/lng/tz elle, online=False).

        date_override verilirse (datetime.date) o tarih için 12:00 subject
        üretir (transit hesabı). Saat bilinmiyorsa öğlen (12:00) varsayılır.
        """
        if date_override is not None:
            year, month, day = (
                date_override.year,
                date_override.month,
                date_override.day,
            )
            hour, minute = 12, 0
        else:
            year, month, day = (
                birth.birth_date.year,
                birth.birth_date.month,
                birth.birth_date.day,
            )
            if birth.birth_time_known and birth.birth_time is not None:
                hour, minute = birth.birth_time.hour, birth.birth_time.minute
            else:
                hour, minute = 12, 0  # saat bilinmiyor: öğlen varsayımı

        return AstrologicalSubjectFactory.from_birth_data(
            name,
            year,
            month,
            day,
            hour,
            minute,
            lng=birth.lng,
            lat=birth.lat,
            tz_str=birth.tz or "UTC",
            city=birth.place or "NA",
            online=False,  # geonames yok; lat/lng/tz elle veriliyor
        )

    def _birth_chart(self, subject: Any) -> dict[str, Any]:
        """Subject -> birth_chart sözleşme dict'i."""
        bc: dict[str, Any] = {}
        for key, attr in _BODY_ATTRS.items():
            point = getattr(subject, attr, None)
            if point is not None:
                bc[key] = _point_to_dict(point)
        bc["houses_system_name"] = getattr(subject, "houses_system_name", None)
        bc["zodiac_type"] = getattr(subject, "zodiac_type", None)
        return bc

    async def natal_chart(self, birth: BirthData) -> dict[str, Any]:
        """Lokal natal chart (gezegen pozisyonları, evler) — ham sözleşme dict."""
        subject = self._subject(birth)
        return {"birth_chart": self._birth_chart(subject)}

    async def daily_transits(self, birth: BirthData, date: str) -> dict[str, Any]:
        """Verilen tarih (YYYY-MM-DD) için noon transit pozisyonları + natal."""
        natal_subject = self._subject(birth)
        natal_bc = self._birth_chart(natal_subject)

        transits: dict[str, Any] = {}
        try:
            parsed = datetime.strptime(date, "%Y-%m-%d").date()
            transit_subject = self._subject(
                birth, name="Transit", date_override=parsed
            )
            transits = self._birth_chart(transit_subject)
        except Exception:
            transits = {}

        return {"date": date, "natal": natal_bc, "transits": transits}

    async def synastry(self, a: BirthData, b: BirthData) -> dict[str, Any]:
        """İki kişi arası sinastri: natal haritalar + (varsa) gerçek açılar."""
        subject_a = self._subject(a, name="PersonA")
        subject_b = self._subject(b, name="PersonB")

        result: dict[str, Any] = {
            "person_a": self._birth_chart(subject_a),
            "person_b": self._birth_chart(subject_b),
        }

        try:
            syn = SynastryAspects(subject_a, subject_b)
            aspects = []
            for asp in syn.relevant_aspects:
                if hasattr(asp, "model_dump"):
                    aspects.append(asp.model_dump())
                elif isinstance(asp, dict):
                    aspects.append(asp)
            if aspects:
                result["aspects"] = aspects
        except Exception:
            pass  # açı hesabı başarısız olursa person_a/b yine döner

        return result

    async def natal_chart_svg(self, birth: BirthData, theme: str = "dark") -> bytes:
        """Natal wheel SVG'sini bytes olarak döner (lokal üretim)."""
        subject = self._subject(birth)
        tmp_dir = tempfile.mkdtemp(prefix="astrype_svg_")
        try:
            chart = KerykeionChartSVG(
                subject,
                chart_type="Natal",
                new_output_directory=tmp_dir,
                theme=theme,  # type: ignore[arg-type]
            )
            chart.save_svg()
            files = glob.glob(os.path.join(tmp_dir, "*.svg"))
            if not files:
                raise RuntimeError("Kerykeion SVG dosyası üretilemedi.")
            with open(files[0], "r", encoding="utf-8") as fh:
                svg = fh.read()
            # flutter_svg CSS var() desteklemez → sunucuda düzleştir.
            return _flatten_css_vars(svg).encode("utf-8")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

"""Lokal Kerykeion natal chart sağlayıcısı testleri.

pytest-asyncio bağımlılığı olmadan: her test kendi async iç fonksiyonunu
asyncio.run(...) ile sarmalar.
"""
import asyncio
from datetime import date, time

from app.api.routes_chart import _snapshot
from app.models import BirthData
from app.services.astro import get_astro_provider
from app.services.astro.kerykeion_provider import KerykeionProvider

# Bakü, 1990-05-12 14:30 -> Güneş Boğa (Taurus) burcunda olmalı.
BIRTH = BirthData(
    birth_date=date(1990, 5, 12),
    birth_time=time(14, 30),
    birth_time_known=True,
    lat=40.4093,
    lng=49.8671,
    tz="Asia/Baku",
    place="Baku",
)


def test_factory_returns_kerykeion():
    provider = get_astro_provider()
    assert provider.name == "kerykeion"
    assert isinstance(provider, KerykeionProvider)


def test_natal_chart_contract():
    async def _inner():
        provider = KerykeionProvider()
        raw = await provider.natal_chart(BIRTH)

        assert "birth_chart" in raw
        bc = raw["birth_chart"]

        # Güneş Boğa burcunda (tam ad).
        assert bc["sun"]["sign"] == "Taurus"

        # Alanlar dolu.
        for field in ("name", "sign", "emoji", "element", "house"):
            assert bc["sun"].get(field), f"sun.{field} boş"

        # Ay ve yükselen mevcut.
        assert bc["moon"]["sign"]
        assert bc["ascendant"]["sign"]

        # Sözleşme alanları.
        assert bc.get("houses_system_name")
        assert bc.get("zodiac_type")

    asyncio.run(_inner())


def test_snapshot_integration():
    """routes_chart._snapshot ile gerçek entegrasyon kanıtı."""

    async def _inner():
        provider = KerykeionProvider()
        raw = await provider.natal_chart(BIRTH)
        snap = _snapshot(raw)

        assert snap["sun_sign"] is not None
        assert snap["moon_sign"] is not None
        assert snap["rising_sign"] is not None
        assert snap["sun_sign"] == "Taurus"
        assert snap["house_system"]
        assert snap["zodiac_type"]
        assert len(snap["bodies"]) >= 3

    asyncio.run(_inner())

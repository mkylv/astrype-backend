"""Astro provider seçimi — tek noktadan değiştirilebilir.

İleride Swiss Ephemeris / Skyfield'e geçmek için yalnızca bu fabrika ve
ilgili implementasyon dosyası değişir; backend'in geri kalanı yalnızca
AstroProvider arayüzünü tanır.
"""
from functools import lru_cache

from app.services.astro.base import AstroProvider
from app.services.astro.numerology_api import NumerologyAPIProvider


@lru_cache
def get_astro_provider() -> AstroProvider:
    return NumerologyAPIProvider()

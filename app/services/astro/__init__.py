"""Astro provider seçimi — tek noktadan değiştirilebilir.

Sağlayıcı **lokal Kerykeion** (Swiss Ephemeris üzerine): doğum haritası dışa
bağımlı RapidAPI olmadan, offline hesaplanır. İleride Skyfield vb. bir
sağlayıcıya geçmek için yalnızca bu fabrika + ilgili implementasyon dosyası
değişir — backend'in geri kalanı yalnızca AstroProvider arayüzünü tanır.
"""
from functools import lru_cache

from app.services.astro.base import AstroProvider
from app.services.astro.kerykeion_provider import KerykeionProvider


@lru_cache
def get_astro_provider() -> AstroProvider:
    return KerykeionProvider()

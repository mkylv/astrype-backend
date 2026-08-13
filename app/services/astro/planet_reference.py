"""Gezegen referansı — natal chart'ta bir gök cismine tıklayınca gösterilecek
meta (glyph, anahtar kelime) + Supabase Storage'daki gerçek gezegen görseli.

Görseller Wikipedia/Wikimedia (çoğu NASA, public domain) kaynağından çekilip
Supabase `planets` bucket'ına (public) yüklendi. URL:
  {SUPABASE_URL}/storage/v1/object/public/planets/{key}.{ext}
"""
from app.config import get_settings

# key -> (Türkçe ad, astrolojik glyph, kısa anahtar kelime, görsel uzantısı)
PLANETS: dict[str, dict] = {
    "sun":     {"name": "Güneş",  "glyph": "☉", "keyword": "Öz kimlik, irade",     "ext": "jpg"},
    "moon":    {"name": "Ay",     "glyph": "☽", "keyword": "Duygular, iç dünya",    "ext": "jpg"},
    "mercury": {"name": "Merkür", "glyph": "☿", "keyword": "Zihin, iletişim",       "ext": "jpg"},
    "venus":   {"name": "Venüs",  "glyph": "♀", "keyword": "Aşk, değer, uyum",       "ext": "jpg"},
    "mars":    {"name": "Mars",   "glyph": "♂", "keyword": "Arzu, eylem, cesaret",   "ext": "png"},
    "jupiter": {"name": "Jüpiter","glyph": "♃", "keyword": "Şans, genişleme, bereket","ext": "png"},
    "saturn":  {"name": "Satürn", "glyph": "♄", "keyword": "Sınav, sınır, olgunluk", "ext": "png"},
    "uranus":  {"name": "Uranüs", "glyph": "♅", "keyword": "Özgürlük, ani değişim",  "ext": "png"},
    "neptune": {"name": "Neptün", "glyph": "♆", "keyword": "Hayal, sezgi, ilham",    "ext": "png"},
    "pluto":   {"name": "Plüton", "glyph": "♇", "keyword": "Dönüşüm, güç, yeniden doğuş", "ext": "png"},
}

# natal snapshot / birth_chart anahtar eşlemesi (ascendant bir nokta, gezegen değil).
_ALIASES = {"asc": "ascendant", "ascendant": "ascendant"}


def image_url(key: str) -> str | None:
    p = PLANETS.get(key)
    if not p:
        return None
    base = get_settings().supabase_url.rstrip("/")
    return f"{base}/storage/v1/object/public/planets/{key}.{p['ext']}"


def meta(key: str) -> dict | None:
    p = PLANETS.get(key)
    if not p:
        return None
    return {
        "key": key,
        "name": p["name"],
        "glyph": p["glyph"],
        "keyword": p["keyword"],
        "image_url": image_url(key),
    }


def all_meta() -> list[dict]:
    return [meta(k) for k in PLANETS]

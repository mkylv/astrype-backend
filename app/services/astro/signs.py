"""Deterministik burç yardımcıları — dış çağrı yok, sadece tarih aritmetiği.

Güneş burcunu doğum tarihinden hesaplar (tropik zodyak, standart tarih
aralıkları). Burç yorumları per-sign cache'lenebildiği için burada dış
sağlayıcıya (Kerykeion/RapidAPI) ihtiyaç yoktur.
"""
from datetime import date

# İngilizce anahtar -> Türkçe burç adı (12 burç, sırayla).
SIGNS: dict[str, str] = {
    "aries": "Koç",
    "taurus": "Boğa",
    "gemini": "İkizler",
    "cancer": "Yengeç",
    "leo": "Aslan",
    "virgo": "Başak",
    "libra": "Terazi",
    "scorpio": "Akrep",
    "sagittarius": "Yay",
    "capricorn": "Oğlak",
    "aquarius": "Kova",
    "pisces": "Balık",
}

# Her burcun SON gününü (month*100 + day) kodlar. Tarihi bu eşiklere göre
# sırayla karşılaştırır; ilk eşleşen burç döner. Oğlak yıl sınırını aştığı
# için hem başta (1/19) hem sonda (12/31) yer alır.
_CUTOFFS: list[tuple[int, str]] = [
    (119, "capricorn"),
    (218, "aquarius"),
    (320, "pisces"),
    (419, "aries"),
    (520, "taurus"),
    (620, "gemini"),
    (722, "cancer"),
    (822, "leo"),
    (922, "virgo"),
    (1022, "libra"),
    (1121, "scorpio"),
    (1221, "sagittarius"),
    (1231, "capricorn"),
]


def sun_sign_from_date(d: date) -> tuple[str, str]:
    """Doğum tarihinden (key_en, name_tr) döner (tropik zodyak)."""
    val = d.month * 100 + d.day
    for cutoff, key in _CUTOFFS:
        if val <= cutoff:
            return key, SIGNS[key]
    return "capricorn", SIGNS["capricorn"]  # güvenlik ağı (teoride ulaşılmaz)


def sign_tr(key: str) -> str:
    """İngilizce anahtardan Türkçe burç adı; bilinmiyorsa anahtarı döner."""
    return SIGNS.get(key.lower().strip(), key)


def normalize_sign(s: str) -> str | None:
    """İngilizce anahtar ya da Türkçe adı normalize eder → key_en | None."""
    if not s:
        return None
    q = s.lower().strip()
    if q in SIGNS:
        return q
    for key, name_tr in SIGNS.items():
        if q == name_tr.lower():
            return key
    return None

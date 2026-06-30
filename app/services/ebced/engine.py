"""Ebced (Abjad) hesaplama motoru — ilm-i hurûf temel verisi.

Latin (Türkçe/Azerice) ismi geleneksel Arap harflerine eşler, her harfin
**ebced-i kebir** değerini ve dört unsurdan (ateş/hava/su/toprak) hangisine
ait olduğunu döner. Deterministik taban; mistik yorumu OpenAI (Osmanlı
müneccim üslubu) üretir.
"""
from __future__ import annotations

from typing import Any

# Ebced-i kebir değerleri (Arap harfi → sayı).
ABJAD: dict[str, int] = {
    "ا": 1, "ب": 2, "ج": 3, "د": 4, "ه": 5, "و": 6, "ز": 7, "ح": 8, "ط": 9,
    "ي": 10, "ك": 20, "ل": 30, "م": 40, "ن": 50, "س": 60, "ع": 70, "ف": 80,
    "ص": 90, "ق": 100, "ر": 200, "ش": 300, "ت": 400, "ث": 500, "خ": 600,
    "ذ": 700, "ض": 800, "ظ": 900, "غ": 1000,
}

# Dört unsur (anâsır-ı erbaa) — klasik 28 harf bölümü.
_ELEMENT_GROUPS: dict[str, str] = {}
for _ar in "اهطمفشذ":
    _ELEMENT_GROUPS[_ar] = "ateş"
for _ar in "بوينصتض":
    _ELEMENT_GROUPS[_ar] = "hava"
for _ar in "جزكسقثظ":
    _ELEMENT_GROUPS[_ar] = "su"
for _ar in "دحلعرخغ":
    _ELEMENT_GROUPS[_ar] = "toprak"

# Latin (Türkçe/Azerice) → Arap harfi (ebced geleneğine yakın yaklaşıklama).
_LATIN_TO_ARABIC: dict[str, str] = {
    "a": "ا", "â": "ا", "b": "ب", "c": "ج", "ç": "ج", "d": "د", "e": "ه",
    "f": "ف", "g": "ك", "ğ": "غ", "h": "ح", "ı": "ي", "i": "ي", "î": "ي",
    "j": "ز", "k": "ك", "l": "ل", "m": "م", "n": "ن", "o": "و", "ö": "و",
    "p": "ب", "q": "ق", "r": "ر", "s": "س", "ş": "ش", "t": "ت", "u": "و",
    "ü": "و", "û": "و", "v": "و", "w": "و", "x": "خ", "y": "ي", "z": "ز",
}


def _element_of(arabic: str) -> str:
    return _ELEMENT_GROUPS.get(arabic, "toprak")


def compute_ebced(text: str) -> dict[str, Any]:
    """Bir ismin ebced dökümü: harf harf değer + unsur + toplam + baskın unsur."""
    letters: list[dict[str, Any]] = []
    elements = {"ateş": 0, "hava": 0, "su": 0, "toprak": 0}
    total = 0

    for ch in (text or "").lower():
        ar = _LATIN_TO_ARABIC.get(ch)
        if ar is None:
            continue
        val = ABJAD.get(ar, 0)
        el = _element_of(ar)
        letters.append({"latin": ch, "arabic": ar, "value": val, "element": el})
        elements[el] += 1
        total += val

    # Baskın unsur: en çok harfi olan unsur (eşitlikte sabit öncelik).
    dominant = (
        max(elements, key=lambda k: (elements[k], -["ateş", "hava", "su", "toprak"].index(k)))
        if letters
        else None
    )
    arabic_word = "".join(l["arabic"] for l in letters)

    return {
        "input": text,
        "arabic": arabic_word,
        "letters": letters,
        "total": total,
        "elements": elements,
        "dominant_element": dominant,
        "first_letter": letters[0] if letters else None,
        "last_letter": letters[-1] if letters else None,
        "reduced": _reduce(total),
    }


def _reduce(n: int) -> int:
    """Ebced toplamını tek haneye indirger (cifir/yıldızname'de kullanılır)."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

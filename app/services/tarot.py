"""Tarot deste + kart çekme yardımcıları.

Kart çekme backend'de yapılır (deterministik test için seed verilebilir).
Tam 78 kartlık RWS destesi `tarot_deck.FULL_DECK` üzerinden gelir.
"""
import secrets
from typing import Any

from app.services import tarot_deck

# Geriye dönük uyumluluk: Major Arcana isim listesi (deck'ten türetilir).
MAJOR_ARCANA = [c["name"] for c in tarot_deck.FULL_DECK if c["arcana"] == "major"]


def draw(count: int = 1, deck: str = "full") -> list[dict[str, Any]]:
    """Tekrarsız `count` kart çek; her biri düz/ters olabilir.

    deck="full"  -> tam 78 kart havuzu
    deck="major" -> sadece 22 Major Arcana
    Her çekilen kart zenginleştirilmiş döner:
    {name, orientation, arcana, suit, upright, reversed, image, meaning}.
    """
    if deck == "major":
        pool = [c for c in tarot_deck.FULL_DECK if c["arcana"] == "major"]
    else:
        pool = list(tarot_deck.FULL_DECK)

    idx = list(range(len(pool)))
    picked: list[dict[str, Any]] = []
    for _ in range(min(count, len(idx))):
        j = secrets.randbelow(len(idx))
        card = pool[idx.pop(j)]
        orientation = "reversed" if secrets.randbelow(2) else "upright"
        meaning = card["reversed"] if orientation == "reversed" else card["upright"]
        picked.append({
            "name": card["name"],
            "orientation": orientation,
            "arcana": card["arcana"],
            "suit": card["suit"],
            "upright": card["upright"],
            "reversed": card["reversed"],
            "image": card["image"],
            "meaning": meaning,
        })
    return picked

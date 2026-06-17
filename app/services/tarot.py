"""Tarot deste + kart çekme yardımcıları.

Kart çekme backend'de yapılır (deterministik test için seed verilebilir).
Major Arcana (22 kart) MVP için yeterli.
"""
import secrets

MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil",
    "The Tower", "The Star", "The Moon", "The Sun",
    "Judgement", "The World",
]


def draw(count: int = 1) -> list[dict[str, str]]:
    """Tekrarsız `count` kart çek; her biri düz/ters olabilir."""
    idx = list(range(len(MAJOR_ARCANA)))
    picked: list[dict[str, str]] = []
    for _ in range(min(count, len(idx))):
        j = secrets.randbelow(len(idx))
        card_i = idx.pop(j)
        orientation = "reversed" if secrets.randbelow(2) else "upright"
        picked.append({"name": MAJOR_ARCANA[card_i], "orientation": orientation})
    return picked

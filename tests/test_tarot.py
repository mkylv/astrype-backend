"""Lokal tarot destesi + çekim testleri (OpenAI/API çağrısı YOK)."""
from app.services import tarot
from app.services.tarot_deck import FULL_DECK, get_card, validate_deck


def test_validate_deck():
    # 78 kart, isim tekrarsızlığı, major=22 / minor=56
    validate_deck()
    assert len(FULL_DECK) == 78
    names = [c["name"] for c in FULL_DECK]
    assert len(names) == len(set(names))
    assert sum(1 for c in FULL_DECK if c["arcana"] == "major") == 22
    assert sum(1 for c in FULL_DECK if c["arcana"] == "minor") == 56


def test_get_card():
    card = get_card("The Fool")
    assert card["arcana"] == "major"
    assert card["suit"] is None
    ace = get_card("Ace of Cups")
    assert ace["arcana"] == "minor"
    assert ace["suit"] == "cups"


def test_draw_three_unique_with_fields():
    cards = tarot.draw(3)
    assert len(cards) == 3
    # tekrarsız
    assert len({c["name"] for c in cards}) == 3
    for c in cards:
        assert c["orientation"] in ("upright", "reversed")
        assert c["meaning"]
        # orientation'a uygun meaning
        expected = c["reversed"] if c["orientation"] == "reversed" else c["upright"]
        assert c["meaning"] == expected
        assert "image" in c and "arcana" in c


def test_draw_major_mode_only_major():
    cards = tarot.draw(5, deck="major")
    assert len(cards) == 5
    assert all(c["arcana"] == "major" for c in cards)
    assert all(c["suit"] is None for c in cards)


def test_draw_single_default():
    cards = tarot.draw(1)
    assert len(cards) == 1
    assert cards[0]["meaning"]

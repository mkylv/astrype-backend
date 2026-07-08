"""Bilinçaltı gölge motoru — deterministik testler (ağ/AI yok)."""
from app.services.subconscious.engine import (
    SHADOWS,
    TEST,
    rank_shadows,
    sign_element,
)


def test_test_structure():
    assert len(TEST) == 4
    for step in TEST:
        assert step["question"] and step["options"]
        for o in step["options"]:
            assert o["points_to"] in SHADOWS


def test_clear_winner():
    picked = ["shadow_control", "shadow_control", "shadow_control", "shadow_abandon"]
    ranked, counts = rank_shadows(picked)
    assert ranked[0] == "shadow_control"
    assert counts["shadow_control"] == 3


def test_element_breaks_tie():
    # 2-2 beraberlik; Güneş Toprak (Capricorn) → control kazanır.
    picked = ["shadow_control", "shadow_control", "shadow_abandon", "shadow_abandon"]
    ranked, _ = rank_shadows(picked, sun_sign="Capricorn")
    assert ranked[0] == "shadow_control"
    # Su (Cancer) → abandon kazanır.
    ranked2, _ = rank_shadows(picked, sun_sign="Cancer")
    assert ranked2[0] == "shadow_abandon"


def test_element_never_overtakes_real_lead():
    # control 3, abandon 1; Güneş Su olsa bile control lider kalır (boost < 1).
    picked = ["shadow_control", "shadow_control", "shadow_control", "shadow_abandon"]
    ranked, _ = rank_shadows(picked, sun_sign="Pisces")
    assert ranked[0] == "shadow_control"


def test_sign_element():
    assert sign_element("Capricorn") == "Earth"
    assert sign_element("cancer") == "Water"
    assert sign_element("Aries") == "Fire"
    assert sign_element("Libra") == "Air"
    assert sign_element(None) is None

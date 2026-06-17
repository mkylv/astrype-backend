"""Ağ gerektirmeyen saf mantık testleri."""
from app.services import tarot
from app.services.ai.memory import build_context_block
from app.services.ai.safety import SAFETY_SYSTEM_PROMPT, is_crisis_signal
from app.services.subscription.revenuecat import _tier_from_event


def test_tarot_draw_unique_and_count():
    cards = tarot.draw(3)
    assert len(cards) == 3
    names = [c["name"] for c in cards]
    assert len(set(names)) == 3  # tekrarsız
    for c in cards:
        assert c["orientation"] in ("upright", "reversed")


def test_tarot_draw_caps_at_deck_size():
    cards = tarot.draw(100)
    assert len(cards) == len(tarot.MAJOR_ARCANA)


def test_safety_prompt_present():
    assert "kesin kader" in SAFETY_SYSTEM_PROMPT
    assert "profesyonel" in SAFETY_SYSTEM_PROMPT


def test_crisis_signal_detection():
    assert is_crisis_signal("kendime zarar vermek istiyorum")
    assert is_crisis_signal("I want to kill myself")
    assert not is_crisis_signal("bugün harika hissediyorum")


def test_context_block_empty():
    assert build_context_block(None, []) == "(henüz context yok)"


def test_context_block_with_profile_and_recall():
    block = build_context_block(
        {"language": "tr", "birth_date": "1990-01-01", "interests": ["aşk"]},
        ["geçmiş içgörü 1"],
    )
    assert "tr" in block
    assert "geçmiş içgörü 1" in block


def test_revenuecat_purchase_active():
    tier, active = _tier_from_event(
        {"type": "INITIAL_PURCHASE", "entitlement_ids": ["premium"]}
    )
    assert tier == "premium" and active is True


def test_revenuecat_expiration_inactive():
    tier, active = _tier_from_event(
        {"type": "EXPIRATION", "entitlement_ids": ["premium"]}
    )
    assert tier == "free" and active is False


def test_revenuecat_elite_mapping():
    tier, active = _tier_from_event(
        {"type": "RENEWAL", "entitlement_ids": ["elite"]}
    )
    assert tier == "elite" and active is True

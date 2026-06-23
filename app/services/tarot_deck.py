"""Statik 78 kart Rider-Waite-Smith (RWS) tarot destesi.

RapidAPI bağımlılığı kaldırıldı; kart havuzu artık tamamen lokal.

Her kart temel (kısa, İngilizce keyword tarzı) anlam taşır — Astrype'ın asıl
kişiselleştirilmiş yorumunu OpenAI üretir, buradaki anlamlar yalnızca taban
girdidir.

NOT (image alanı): "image" değerleri kamu malı RWS deck için slug placeholder
biçimindedir ("rws/<slug>.jpg"). Gerçek görsellerin bir CDN/Storage üzerinde
host edilmesi ve bu slug'ların oraya map'lenmesi gerekir; deste verisi görsel
ikilisi içermez.
"""
from typing import Any, Optional


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "")


# --- Major Arcana (22) — tarot.py'deki MAJOR_ARCANA ile UYUMLU ---
_MAJOR: list[tuple[str, int, str, str]] = [
    ("The Fool", 0, "new beginnings, spontaneity, free spirit, leap of faith",
     "recklessness, naivety, hesitation, holding back"),
    ("The Magician", 1, "manifestation, willpower, skill, resourcefulness",
     "manipulation, untapped potential, self-doubt"),
    ("The High Priestess", 2, "intuition, mystery, inner voice, the subconscious",
     "secrets withheld, disconnected intuition, surface knowledge"),
    ("The Empress", 3, "abundance, nurturing, fertility, sensuality",
     "creative block, dependence, neglect of self"),
    ("The Emperor", 4, "authority, structure, stability, leadership",
     "rigidity, domination, loss of control"),
    ("The Hierophant", 5, "tradition, guidance, belief systems, mentorship",
     "rebellion, dogma questioned, personal beliefs"),
    ("The Lovers", 6, "love, union, harmony, meaningful choices",
     "disharmony, imbalance, misaligned values"),
    ("The Chariot", 7, "willpower, drive, victory, determination",
     "lack of direction, scattered focus, loss of control"),
    ("Strength", 8, "courage, inner strength, patience, compassion",
     "self-doubt, raw emotion, low confidence"),
    ("The Hermit", 9, "introspection, solitude, inner guidance, searching",
     "isolation, withdrawal, lost in thought"),
    ("Wheel of Fortune", 10, "cycles, change, fate, turning point",
     "resistance to change, bad luck, broken cycles"),
    ("Justice", 11, "fairness, truth, cause and effect, accountability",
     "unfairness, dishonesty, avoiding responsibility"),
    ("The Hanged Man", 12, "surrender, new perspective, pause, letting go",
     "stalling, indecision, needless sacrifice"),
    ("Death", 13, "endings, transformation, transition, release",
     "resistance to change, stagnation, fear of endings"),
    ("Temperance", 14, "balance, moderation, patience, blending",
     "imbalance, excess, lack of harmony"),
    ("The Devil", 15, "attachment, temptation, materialism, shadow self",
     "release, breaking free, reclaiming power"),
    ("The Tower", 16, "sudden change, upheaval, revelation, awakening",
     "fear of change, averting disaster, delayed collapse"),
    ("The Star", 17, "hope, renewal, inspiration, serenity",
     "despair, disconnection, lost faith"),
    ("The Moon", 18, "illusion, intuition, the unknown, dreams",
     "confusion lifting, releasing fear, clarity"),
    ("The Sun", 19, "joy, success, vitality, positivity",
     "temporary gloom, blocked optimism, delays"),
    ("Judgement", 20, "reckoning, awakening, renewal, inner calling",
     "self-doubt, ignoring the call, harsh self-judgment"),
    ("The World", 21, "completion, fulfillment, integration, achievement",
     "incompletion, shortcuts, lack of closure"),
]

# --- Minor Arcana suits ---
_SUITS = ("wands", "cups", "swords", "pentacles")

_RANKS: list[tuple[str, Optional[int]]] = [
    ("Ace", 1), ("Two", 2), ("Three", 3), ("Four", 4), ("Five", 5),
    ("Six", 6), ("Seven", 7), ("Eight", 8), ("Nine", 9), ("Ten", 10),
    ("Page", None), ("Knight", None), ("Queen", None), ("King", None),
]

# Kısa keyword anlamları: (suit, rank-key) -> (upright, reversed)
_MINOR_MEANINGS: dict[tuple[str, str], tuple[str, str]] = {
    # Wands — passion, energy, action
    ("wands", "Ace"): ("inspiration, new energy, creative spark", "delays, lack of direction, false start"),
    ("wands", "Two"): ("planning, future vision, personal power", "fear of change, playing safe, bad planning"),
    ("wands", "Three"): ("expansion, foresight, progress", "delays, obstacles, lack of foresight"),
    ("wands", "Four"): ("celebration, harmony, home, milestone", "instability, lack of support, transition"),
    ("wands", "Five"): ("conflict, competition, tension", "avoiding conflict, resolution, tension easing"),
    ("wands", "Six"): ("victory, recognition, progress", "ego, fall from grace, lack of recognition"),
    ("wands", "Seven"): ("defense, perseverance, standing firm", "overwhelm, giving up, exhaustion"),
    ("wands", "Eight"): ("speed, movement, swift action", "delays, frustration, scattered energy"),
    ("wands", "Nine"): ("resilience, persistence, last stand", "exhaustion, defensiveness, paranoia"),
    ("wands", "Ten"): ("burden, responsibility, hard work", "overload, release, delegation needed"),
    ("wands", "Page"): ("curiosity, exploration, fresh ideas", "hesitation, distraction, redirect energy"),
    ("wands", "Knight"): ("adventure, passion, bold action", "haste, impulsiveness, recklessness"),
    ("wands", "Queen"): ("confidence, warmth, determination", "self-doubt, jealousy, draining energy"),
    ("wands", "King"): ("vision, leadership, bold direction", "impulsiveness, domineering, high expectations"),
    # Cups — emotion, relationships, intuition
    ("cups", "Ace"): ("new love, compassion, emotional opening", "blocked emotions, emptiness, repressed feeling"),
    ("cups", "Two"): ("partnership, connection, mutual respect", "imbalance, breakup, tension"),
    ("cups", "Three"): ("friendship, community, celebration", "overindulgence, gossip, isolation"),
    ("cups", "Four"): ("apathy, contemplation, reevaluation", "new awareness, acceptance, moving on"),
    ("cups", "Five"): ("loss, grief, disappointment", "acceptance, recovery, moving forward"),
    ("cups", "Six"): ("nostalgia, memories, innocence", "stuck in the past, naivety, letting go"),
    ("cups", "Seven"): ("choices, fantasy, illusion", "clarity, focus, decision made"),
    ("cups", "Eight"): ("walking away, seeking meaning, transition", "fear of change, stagnation, drifting"),
    ("cups", "Nine"): ("contentment, satisfaction, wishes fulfilled", "inner happiness, complacency, dissatisfaction"),
    ("cups", "Ten"): ("harmony, lasting happiness, fulfillment", "broken harmony, misalignment, disconnect"),
    ("cups", "Page"): ("creativity, intuition, gentle message", "emotional immaturity, insecurity, blocked creativity"),
    ("cups", "Knight"): ("romance, charm, following the heart", "moodiness, unrealistic ideals, disappointment"),
    ("cups", "Queen"): ("compassion, empathy, emotional security", "emotional overwhelm, dependence, insecurity"),
    ("cups", "King"): ("emotional balance, diplomacy, calm", "emotional manipulation, moodiness, volatility"),
    # Swords — intellect, truth, conflict
    ("swords", "Ace"): ("clarity, breakthrough, new idea, truth", "confusion, clouded judgment, miscommunication"),
    ("swords", "Two"): ("difficult choice, stalemate, indecision", "indecision lifting, information revealed, release"),
    ("swords", "Three"): ("heartbreak, sorrow, painful truth", "recovery, forgiveness, releasing pain"),
    ("swords", "Four"): ("rest, recovery, contemplation", "restlessness, burnout, slow recovery"),
    ("swords", "Five"): ("conflict, defeat, winning at a cost", "reconciliation, making amends, moving past"),
    ("swords", "Six"): ("transition, moving on, gradual change", "stuck, resistance, unfinished business"),
    ("swords", "Seven"): ("strategy, cunning, acting alone", "coming clean, conscience, getting caught"),
    ("swords", "Eight"): ("restriction, feeling trapped, self-limiting", "freedom, new perspective, releasing limits"),
    ("swords", "Nine"): ("anxiety, worry, sleepless nights", "hope returning, releasing worry, recovery"),
    ("swords", "Ten"): ("painful ending, rock bottom, betrayal", "recovery, regeneration, survival"),
    ("swords", "Page"): ("curiosity, vigilance, sharp mind", "deception, hasty words, scattered thoughts"),
    ("swords", "Knight"): ("ambition, drive, fast action, focus", "recklessness, aggression, burnout"),
    ("swords", "Queen"): ("clarity, independence, honest judgment", "coldness, bitterness, harsh criticism"),
    ("swords", "King"): ("authority, truth, intellectual power", "manipulation, cruelty, misuse of power"),
    # Pentacles — material, work, body, resources
    ("pentacles", "Ace"): ("opportunity, prosperity, new venture", "missed chance, instability, lack of planning"),
    ("pentacles", "Two"): ("balance, adaptability, prioritizing", "imbalance, overwhelm, disorganization"),
    ("pentacles", "Three"): ("teamwork, collaboration, skill building", "lack of teamwork, disharmony, poor work"),
    ("pentacles", "Four"): ("security, stability, holding on", "greed, control, releasing attachment"),
    ("pentacles", "Five"): ("hardship, insecurity, scarcity", "recovery, support found, end of struggle"),
    ("pentacles", "Six"): ("generosity, giving, fairness", "strings attached, inequality, debt"),
    ("pentacles", "Seven"): ("patience, investment, long-term view", "impatience, poor return, frustration"),
    ("pentacles", "Eight"): ("diligence, mastery, skill development", "perfectionism, lack of focus, uninspired work"),
    ("pentacles", "Nine"): ("abundance, self-reliance, comfort", "overinvestment in work, financial setback, dependence"),
    ("pentacles", "Ten"): ("wealth, legacy, family, lasting success", "instability, fleeting success, family conflict"),
    ("pentacles", "Page"): ("ambition, study, new opportunity", "lack of progress, procrastination, missed lessons"),
    ("pentacles", "Knight"): ("hard work, reliability, routine", "boredom, stagnation, feeling stuck"),
    ("pentacles", "Queen"): ("nurturing, practicality, abundance", "imbalance, self-care neglect, smothering"),
    ("pentacles", "King"): ("wealth, security, leadership, success", "greed, materialism, poor financial decisions"),
}


def _build_full_deck() -> list[dict[str, Any]]:
    deck: list[dict[str, Any]] = []

    for name, number, upright, reversed_ in _MAJOR:
        deck.append({
            "name": name,
            "arcana": "major",
            "suit": None,
            "number": number,
            "upright": upright,
            "reversed": reversed_,
            "image": f"rws/{_slug(name)}.jpg",
        })

    for suit in _SUITS:
        for rank_name, rank_num in _RANKS:
            card_name = f"{rank_name} of {suit.capitalize()}"
            upright, reversed_ = _MINOR_MEANINGS[(suit, rank_name)]
            deck.append({
                "name": card_name,
                "arcana": "minor",
                "suit": suit,
                "number": rank_num,
                "upright": upright,
                "reversed": reversed_,
                "image": f"rws/{_slug(card_name)}.jpg",
            })

    return deck


FULL_DECK: list[dict[str, Any]] = _build_full_deck()

_BY_NAME: dict[str, dict[str, Any]] = {c["name"]: c for c in FULL_DECK}


def get_card(name: str) -> dict[str, Any]:
    """İsme göre kart döndür (KeyError yerine ValueError, anlamlı mesaj)."""
    card = _BY_NAME.get(name)
    if card is None:
        raise ValueError(f"Unknown tarot card: {name!r}")
    return card


def validate_deck() -> None:
    """Deste bütünlüğünü doğrula (testte çağrılır)."""
    assert len(FULL_DECK) == 78, f"Expected 78 cards, got {len(FULL_DECK)}"

    names = [c["name"] for c in FULL_DECK]
    assert len(names) == len(set(names)), "Duplicate card names in deck"

    majors = [c for c in FULL_DECK if c["arcana"] == "major"]
    minors = [c for c in FULL_DECK if c["arcana"] == "minor"]
    assert len(majors) == 22, f"Expected 22 major arcana, got {len(majors)}"
    assert len(minors) == 56, f"Expected 56 minor arcana, got {len(minors)}"

    for c in FULL_DECK:
        assert c["arcana"] in ("major", "minor")
        assert c["upright"] and c["reversed"], f"Missing meaning for {c['name']}"
        if c["arcana"] == "major":
            assert c["suit"] is None
        else:
            assert c["suit"] in _SUITS

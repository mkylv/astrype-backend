"""Ebced motoru — deterministik testler (ağ/AI yok)."""
from app.services.ebced.engine import ABJAD, compute_ebced


def test_known_total():
    # ك(20)+ا(1)+ن(50)+ا(1)+ن(50) = 122
    r = compute_ebced("Kanan")
    assert r["arabic"] == "كانان"
    assert r["total"] == 122
    assert r["letters"][0]["value"] == 20  # k → ك
    assert r["dominant_element"] in {"ateş", "hava", "su", "toprak"}


def test_structure_and_elements():
    r = compute_ebced("Maryam")
    assert sum(r["elements"].values()) == len(r["letters"])
    assert r["first_letter"] and r["last_letter"]
    assert r["reduced"] == _digit_root(r["total"])
    # Tüm harfler dört unsurdan birinde
    assert all(l["element"] in {"ateş", "hava", "su", "toprak"} for l in r["letters"])


def test_empty_and_nonletters():
    r = compute_ebced("  123 !! ")
    assert r["total"] == 0
    assert r["letters"] == []
    assert r["dominant_element"] is None


def test_abjad_table():
    assert ABJAD["ا"] == 1 and ABJAD["ي"] == 10 and ABJAD["غ"] == 1000
    assert len(ABJAD) == 28


def _digit_root(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

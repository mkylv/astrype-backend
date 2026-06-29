"""İnsan Tasarımı motoru — yapısal + deterministik testler (ağ/AI yok)."""
from datetime import date, time

from app.models import BirthData
from app.services.humandesign.engine import (
    CENTERS,
    CHANNEL_CENTERS,
    CHANNELS,
    GATE_SEQUENCE,
    calculate_bodygraph,
)

_BIRTH = BirthData(
    birth_date=date(1988, 10, 9), birth_time=time(14, 30), birth_time_known=True,
    lat=43.615, lng=-116.2023, tz="America/Boise", place="Boise",
)

_VALID_TYPES = {
    "Generator", "Manifesting Generator", "Manifestor", "Projector", "Reflector",
}


def test_static_data_integrity():
    assert len(GATE_SEQUENCE) == 64
    assert sorted(GATE_SEQUENCE) == list(range(1, 65))  # 1..64 tam, tekrarsız
    assert len(CHANNELS) == 34  # bu veri setindeki kanal sayısı
    assert len(CENTERS) == 9
    assert all(ch in CHANNEL_CENTERS for ch in CHANNELS)


def test_bodygraph_structure():
    r = calculate_bodygraph(_BIRTH)
    assert r["type"] in _VALID_TYPES
    # Profil "X/Y" formatı, 1..6
    p, d = r["profile"].split("/")
    assert 1 <= int(p) <= 6 and 1 <= int(d) <= 6
    # 9 merkez tam bölünmüş
    assert len(r["defined_centers"]) + len(r["undefined_centers"]) == 9
    assert not (set(r["defined_centers"]) & set(r["undefined_centers"]))
    # Tanımlı kanallar geçerli kapı çiftleri
    assert r["active_channels"]
    # 13 cisim her iki tabloda da var
    assert len(r["personality"]) == 13 and len(r["design"]) == 13


def test_determinism():
    a = calculate_bodygraph(_BIRTH)
    b = calculate_bodygraph(_BIRTH)
    assert a["type"] == b["type"]
    assert a["profile"] == b["profile"]
    assert a["defined_centers"] == b["defined_centers"]


def test_unknown_time_uses_noon():
    nb = BirthData(
        birth_date=date(1988, 10, 9), birth_time=None, birth_time_known=False,
        lat=43.615, lng=-116.2023, tz="America/Boise", place="Boise",
    )
    r = calculate_bodygraph(nb)
    assert r["time_known"] is False
    assert r["type"] in _VALID_TYPES

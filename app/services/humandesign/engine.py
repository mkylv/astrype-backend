"""Human Design (İnsan Tasarımı) hesaplama motoru.

Swiss Ephemeris (pyswisseph — kerykeion ile zaten kurulu) üzerine kurulu.
Veri tabloları (kapı çark sırası, 36 kanal, 9 merkez, tip/otorite kuralları)
MIT lisanslı geodetheseeker/human-design-py implementasyonundan uyarlanmıştır
(bodygraph.io'ya karşı doğrulanmış).

Akış: doğum anı (personality) + Güneş'in 88° yay öncesi (design) için 13 gök
cisminin ekliptik boylamı → kapı/çizgi → aktif kapılar → tanımlı kanallar →
tanımlı merkezler → Tip / Otorite / Profil.

NOT: Global swe.set_ephe_path ÇAĞRILMAZ — kerykeion'un ayarladığı Swiss
Ephemeris yolu kullanılır (moshier'dan daha doğru).
"""
from __future__ import annotations

from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

from app.models import BirthData

# ─────────────────────────────────────────────────────────────────────────
# Statik veri (Rave Mandala kapı sırası + kanallar + merkezler)
# ─────────────────────────────────────────────────────────────────────────

GATE_SEQUENCE = [
    25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20,
    16, 35, 45, 12, 15, 52,
    39, 53, 62, 56, 31, 33,
    7, 4, 29, 59, 40, 64,
    47, 6, 46, 18, 48, 57,
    32, 50, 28, 44, 1, 43,
    14, 34, 9, 5, 26, 11,
    10, 58, 38, 54, 61, 60,
    41, 19, 13, 49, 30, 55,
    37, 63, 22, 36,
]

HD_START_DEGREE = 358.25  # 28°15' Balık — Rave Mandala başlangıcı

CENTERS: dict[str, list[int]] = {
    "Head": [61, 63, 64],
    "Ajna": [4, 11, 17, 24, 43, 47],
    "Throat": [8, 12, 16, 20, 23, 31, 33, 35, 45, 56, 62],
    "Self": [1, 2, 7, 10, 13, 15, 25, 46],
    "Sacral": [3, 5, 9, 14, 27, 29, 34, 42, 59],
    "Root": [19, 28, 38, 39, 41, 52, 53, 54, 58, 60],
    "Spleen": [18, 28, 32, 44, 48, 50, 57],
    "Solar Plexus": [6, 22, 30, 36, 37, 49, 55],
    "Heart": [21, 26, 40, 51],
}

CHANNELS: list[tuple[int, int]] = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15),
    (6, 59), (7, 31), (9, 52), (10, 20), (11, 56),
    (12, 22), (13, 33), (16, 48), (17, 62), (18, 58),
    (19, 49), (20, 34), (20, 57), (21, 45), (23, 43),
    (24, 61), (25, 51), (26, 44), (27, 50), (28, 38),
    (29, 46), (30, 41), (32, 54), (34, 57), (35, 36),
    (37, 40), (39, 55), (42, 53), (47, 64),
]

CHANNEL_CENTERS: dict[tuple[int, int], tuple[str, str]] = {
    (1, 8): ("Self", "Throat"), (2, 14): ("Self", "Sacral"),
    (3, 60): ("Sacral", "Root"), (4, 63): ("Ajna", "Head"),
    (5, 15): ("Sacral", "Self"), (6, 59): ("Solar Plexus", "Sacral"),
    (7, 31): ("Self", "Throat"), (9, 52): ("Sacral", "Root"),
    (10, 20): ("Self", "Throat"), (11, 56): ("Ajna", "Throat"),
    (12, 22): ("Throat", "Solar Plexus"), (13, 33): ("Self", "Throat"),
    (16, 48): ("Throat", "Spleen"), (17, 62): ("Ajna", "Throat"),
    (18, 58): ("Spleen", "Root"), (19, 49): ("Root", "Solar Plexus"),
    (20, 34): ("Throat", "Sacral"), (20, 57): ("Throat", "Spleen"),
    (21, 45): ("Heart", "Throat"), (23, 43): ("Throat", "Ajna"),
    (24, 61): ("Ajna", "Head"), (25, 51): ("Self", "Heart"),
    (26, 44): ("Heart", "Spleen"), (27, 50): ("Sacral", "Spleen"),
    (28, 38): ("Spleen", "Root"), (29, 46): ("Sacral", "Self"),
    (30, 41): ("Solar Plexus", "Root"), (32, 54): ("Spleen", "Root"),
    (34, 57): ("Sacral", "Spleen"), (35, 36): ("Throat", "Solar Plexus"),
    (37, 40): ("Solar Plexus", "Heart"), (39, 55): ("Root", "Solar Plexus"),
    (42, 53): ("Sacral", "Root"), (47, 64): ("Ajna", "Head"),
}

# Tip → strateji / imza / not-self (Astrype yorumu için taban).
TYPE_INFO: dict[str, dict[str, str]] = {
    "Generator": {
        "strategy": "Tepki vermek (To Respond)",
        "signature": "Tatmin",
        "not_self": "Hayal kırıklığı",
    },
    "Manifesting Generator": {
        "strategy": "Tepki ver, sonra bilgilendir",
        "signature": "Tatmin",
        "not_self": "Hayal kırıklığı / Öfke",
    },
    "Manifestor": {
        "strategy": "Harekete geçmeden önce bilgilendirmek",
        "signature": "Huzur",
        "not_self": "Öfke",
    },
    "Projector": {
        "strategy": "Daveti beklemek",
        "signature": "Başarı",
        "not_self": "Acılık",
    },
    "Reflector": {
        "strategy": "Bir ay döngüsü (28 gün) beklemek",
        "signature": "Sürpriz",
        "not_self": "Hayal kırıklığı",
    },
}

_PLANETS = {
    "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
}


def _degree_to_gate_line(degree: float) -> tuple[int, int]:
    gate_size = 360 / 64
    line_size = gate_size / 6
    adjusted = (degree - HD_START_DEGREE) % 360
    index = int(adjusted / gate_size)
    line = int((adjusted % gate_size) / line_size) + 1
    return GATE_SEQUENCE[index], line


def _lon(jd: float, body: int) -> float:
    return swe.calc_ut(jd, body)[0][0]


def _positions(jd: float) -> dict[str, dict[str, Any]]:
    """13 gök cismi için boylam + kapı/çizgi (Jovian Archive sırası)."""
    out: dict[str, dict[str, Any]] = {}

    sun = _lon(jd, swe.SUN)
    g, l = _degree_to_gate_line(sun)
    out["Sun"] = {"degree": round(sun, 4), "gate": g, "line": l}

    earth = (sun + 180) % 360
    g, l = _degree_to_gate_line(earth)
    out["Earth"] = {"degree": round(earth, 4), "gate": g, "line": l}

    nn = _lon(jd, swe.TRUE_NODE)
    g, l = _degree_to_gate_line(nn)
    out["N.Node"] = {"degree": round(nn, 4), "gate": g, "line": l}

    sn = (nn + 180) % 360
    g, l = _degree_to_gate_line(sn)
    out["S.Node"] = {"degree": round(sn, 4), "gate": g, "line": l}

    for name, pid in _PLANETS.items():
        d = _lon(jd, pid)
        g, l = _degree_to_gate_line(d)
        out[name] = {"degree": round(d, 4), "gate": g, "line": l}
    return out


def _defined_channels(gate_set: set[int]) -> list[tuple[int, int]]:
    return [(a, b) for a, b in CHANNELS if a in gate_set and b in gate_set]


def _defined_centers(channels: list[tuple[int, int]]) -> set[str]:
    defined: set[str] = set()
    for ch in channels:
        c1, c2 = CHANNEL_CENTERS[ch]
        defined.add(c1)
        defined.add(c2)
    return defined


def _determine_type(defined_centers: set[str], channels: list[tuple[int, int]]) -> str:
    has_sacral = "Sacral" in defined_centers
    motor_centers = {"Sacral", "Heart", "Solar Plexus", "Root"}

    graph: dict[str, set[str]] = {c: set() for c in CENTERS}
    for ch in channels:
        c1, c2 = CHANNEL_CENTERS[ch]
        graph[c1].add(c2)
        graph[c2].add(c1)

    motor_to_throat = False
    if "Throat" in defined_centers:
        visited: set[str] = set()
        queue = ["Throat"]
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            if cur in motor_centers:
                motor_to_throat = True
                break
            queue.extend(graph[cur] - visited)

    if not defined_centers:
        return "Reflector"
    if has_sacral and motor_to_throat:
        return "Manifesting Generator"
    if has_sacral:
        return "Generator"
    if motor_to_throat:
        return "Manifestor"
    return "Projector"


def _determine_authority(defined_centers: set[str]) -> str:
    for center, authority in [
        ("Solar Plexus", "Duygusal (Emotional)"),
        ("Sacral", "Sakral (Sacral)"),
        ("Spleen", "Dalak (Splenic)"),
        ("Heart", "Ego (Heart)"),
        ("Self", "Benlik (Self-Projected)"),
    ]:
        if center in defined_centers:
            return authority
    return "Zihinsel / Dış otorite (Mental)"


def _jd_from_birth(birth: BirthData) -> float:
    """BirthData → personality Julian Day (UTC). Saat bilinmiyorsa öğlen."""
    bt: time = birth.birth_time if (birth.birth_time_known and birth.birth_time) else time(12, 0)
    local = datetime(
        birth.birth_date.year, birth.birth_date.month, birth.birth_date.day,
        bt.hour, bt.minute, tzinfo=ZoneInfo(birth.tz or "UTC"),
    )
    u = local.astimezone(ZoneInfo("UTC"))
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def _jd_design(jd_personality: float) -> float:
    """Güneş'in personality konumundan 88° yay geri gittiği an (~88 gün önce)."""
    target = (_lon(jd_personality, swe.SUN) - 88) % 360
    lo, hi = jd_personality - 100, jd_personality - 80
    mid = (lo + hi) / 2
    for _ in range(60):
        mid = (lo + hi) / 2
        diff = (_lon(mid, swe.SUN) - target + 180) % 360 - 180
        if abs(diff) < 1e-5:
            break
        if diff > 0:
            hi = mid
        else:
            lo = mid
    return mid


def calculate_bodygraph(birth: BirthData) -> dict[str, Any]:
    """BirthData → tam bodygraph dict (Tip/Otorite/Profil/merkezler/kapılar)."""
    jd_p = _jd_from_birth(birth)
    jd_d = _jd_design(jd_p)

    personality = _positions(jd_p)
    design = _positions(jd_d)

    gate_set = {p["gate"] for p in personality.values()} | {p["gate"] for p in design.values()}
    channels = _defined_channels(gate_set)
    defined = _defined_centers(channels)

    hd_type = _determine_type(defined, channels)
    info = TYPE_INFO[hd_type]
    profile = f"{personality['Sun']['line']}/{design['Sun']['line']}"

    return {
        "type": hd_type,
        "strategy": info["strategy"],
        "signature": info["signature"],
        "not_self": info["not_self"],
        "authority": _determine_authority(defined),
        "profile": profile,
        "definition_centers_count": len(defined),
        "defined_centers": sorted(defined),
        "undefined_centers": sorted(set(CENTERS) - defined),
        "active_channels": [f"{a}-{b}" for a, b in channels],
        "active_gates": sorted(gate_set),
        "incarnation_cross": {
            "personality_sun": personality["Sun"]["gate"],
            "personality_earth": personality["Earth"]["gate"],
            "design_sun": design["Sun"]["gate"],
            "design_earth": design["Earth"]["gate"],
        },
        "time_known": bool(birth.birth_time_known and birth.birth_time),
        "personality": personality,
        "design": design,
    }

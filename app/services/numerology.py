"""Pythagorean numeroloji — saf, deterministik fonksiyonlar (sıfır dış bağımlılık).

Tüm hesaplar Pythagorean sistemine dayanır: A=1..I=9 döngüsel tablo, sayılar
tek haneye indirgenir; 11/22/33 master sayıları korunur. OpenAI/ağ erişimi
yoktur — bu modül tamamen deterministiktir ve birim testle doğrulanabilir.
"""
from __future__ import annotations

from datetime import date

# Türkçe karakter -> ASCII indirgemesi (büyük/küçük ele alınır).
_TR_MAP = {
    "ç": "c", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ı": "i", "â": "a",
    "î": "i", "û": "u",
}

# Pythagorean harf -> sayı (A=1..I=9, sonra döngüsel devam eder).
_LETTER_VALUE = {
    "a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9,
    "j": 1, "k": 2, "l": 3, "m": 4, "n": 5, "o": 6, "p": 7, "q": 8, "r": 9,
    "s": 1, "t": 2, "u": 3, "v": 4, "w": 5, "x": 6, "y": 7, "z": 8,
}

_VOWELS = frozenset("aeiou")  # y sesli sayılmaz

_MASTER_NUMBERS = frozenset({11, 22, 33})

# Her ana sayı için kısa anahtar kelimeler (1..9 + master sayılar).
NUMBER_KEYWORDS: dict[int, str] = {
    1: "öncülük, bağımsızlık, irade",
    2: "uyum, denge, işbirliği",
    3: "ifade, yaratıcılık, neşe",
    4: "düzen, istikrar, emek",
    5: "özgürlük, değişim, macera",
    6: "sorumluluk, sevgi, şefkat",
    7: "içe dönüş, bilgelik, sezgi",
    8: "güç, başarı, bolluk",
    9: "şefkat, tamamlanma, vizyon",
    11: "sezgi, ilham, ruhsal farkındalık",
    22: "usta inşacı, büyük vizyon, gerçekleştirme",
    33: "usta öğretmen, koşulsuz sevgi, şifa",
}


def _normalize(text: str) -> str:
    """Metni küçük harfe çevirir ve Türkçe karakterleri ASCII'ye indirger."""
    out = []
    for ch in text.lower():
        out.append(_TR_MAP.get(ch, ch))
    return "".join(out)


def _reduce(n: int, keep_master: bool = True) -> int:
    """Bir sayının rakamlarını tek haneye indirir; master sayıları (11/22/33) korur."""
    n = abs(n)
    while n > 9:
        if keep_master and n in _MASTER_NUMBERS:
            return n
        n = sum(int(d) for d in str(n))
    return n


def _letter_sum(name: str, predicate) -> int:
    """İsimdeki, predicate'ı sağlayan harflerin Pythagorean değerlerini toplar."""
    total = 0
    for ch in _normalize(name):
        if ch in _LETTER_VALUE and predicate(ch):
            total += _LETTER_VALUE[ch]
    return _reduce(total)


def life_path(birth_date: date) -> int:
    """Yaşam Yolu: doğum gün+ay+yıl rakamlarının indirgenmiş toplamı (master korunur)."""
    digits = f"{birth_date.day:02d}{birth_date.month:02d}{birth_date.year:04d}"
    return _reduce(sum(int(d) for d in digits))


def expression(full_name: str) -> int:
    """İfade (Kader) Sayısı: tam isimdeki TÜM harflerin Pythagorean toplamı."""
    return _letter_sum(full_name, lambda ch: True)


def soul_urge(full_name: str) -> int:
    """Ruh Arzusu: yalnızca sesli harfler (a,e,i,o,u; y sesli sayılmaz)."""
    return _letter_sum(full_name, lambda ch: ch in _VOWELS)


def personality(full_name: str) -> int:
    """Kişilik Sayısı: yalnızca sessiz harfler (sesliler hariç)."""
    return _letter_sum(full_name, lambda ch: ch not in _VOWELS)


def birthday_number(birth_date: date) -> int:
    """Doğum Günü Sayısı: ayın günü, indirgenir (master korunur)."""
    return _reduce(birth_date.day)


def personal_year(birth_date: date, ref_date: date) -> int:
    """Kişisel Yıl: doğum gün+ay + referans yılın rakamları, indirgenir."""
    digits = f"{birth_date.day:02d}{birth_date.month:02d}{ref_date.year:04d}"
    return _reduce(sum(int(d) for d in digits))


def full_profile(full_name: str, birth_date: date, ref_date: date) -> dict:
    """Tüm çekirdek sayıları + her sayı için anahtar kelimeleri içeren bir dict döner."""
    numbers = {
        "life_path": life_path(birth_date),
        "expression": expression(full_name),
        "soul_urge": soul_urge(full_name),
        "personality": personality(full_name),
        "birthday": birthday_number(birth_date),
        "personal_year": personal_year(birth_date, ref_date),
    }
    return {
        key: {
            "value": value,
            "keywords": NUMBER_KEYWORDS.get(value, ""),
        }
        for key, value in numbers.items()
    }

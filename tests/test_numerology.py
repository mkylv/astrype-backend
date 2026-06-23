"""Saf numeroloji fonksiyon testleri — API/OpenAI çağrısı YOK, deterministik."""
from datetime import date

from app.services import numerology
from app.services.numerology import NUMBER_KEYWORDS, _reduce


def test_reduce_basic():
    # 1+5 = 6
    assert _reduce(15) == 6
    # 9+9 = 18 -> 1+8 = 9
    assert _reduce(99) == 9
    # tek hane değişmez
    assert _reduce(7) == 7


def test_reduce_keeps_master_numbers():
    assert _reduce(11) == 11
    assert _reduce(22) == 22
    assert _reduce(33) == 33
    # master koruması kapatıldığında indirgenir: 11 -> 2
    assert _reduce(11, keep_master=False) == 2


def test_life_path_reduction():
    # 1990-05-12 -> 1+2 0+5 1+9+9+0 = 12+05+19 ... rakam toplamı:
    # 1+2+0+5+1+9+9+0 = 27 -> 9
    assert numerology.life_path(date(1990, 5, 12)) == 9


def test_life_path_master_preserved():
    # Rakam toplamı 29 -> 11 master sayısı korunur.
    # 2000-11-29 -> 2+9+1+1+2+0+0+0 = 15 -> 6 (kontrol amaçlı farklı tarih)
    # Master üretmek için: 1972-10-09 -> 0+9+1+0+1+9+7+2 = 29 -> 11
    assert numerology.life_path(date(1972, 10, 9)) == 11


def test_expression_uses_all_letters():
    # "AB" -> A=1, B=2 -> 3
    assert numerology.expression("AB") == 3
    # "ABC" -> 1+2+3 = 6
    assert numerology.expression("ABC") == 6


def test_soul_urge_vowels_only_and_personality_consonants():
    # "Ada" -> sesliler a,a = 1+1 = 2 ; sessizler d = 4
    assert numerology.soul_urge("Ada") == 2
    assert numerology.personality("Ada") == 4
    # y sesli sayılmaz: "Yara" sesliler a,a=2 ; sessizler y(7)+r(9)=16 -> 7
    assert numerology.soul_urge("Yara") == 2
    assert numerology.personality("Yara") == 7


def test_turkish_char_normalization():
    # "Çağrı" -> normalize "cagri" ; tüm harfler c(3)+a(1)+g(7)+r(9)+i(9)=29 -> 11
    assert numerology.expression("Çağrı") == 11
    # "Şule" -> "sule": s(1)+u(3)+l(3)+e(5)=12 -> 3
    assert numerology.expression("Şule") == 3
    # Türkçe karakter, ASCII karşılığıyla aynı sonucu vermeli
    assert numerology.expression("İŞIK") == numerology.expression("isik")


def test_birthday_and_personal_year():
    assert numerology.birthday_number(date(1990, 5, 12)) == 3  # 1+2
    assert numerology.birthday_number(date(1990, 5, 22)) == 22  # master korunur
    # personal_year 1990-05-12, ref 2026 -> 1+2+0+5+2+0+2+6 = 18 -> 9
    assert numerology.personal_year(date(1990, 5, 12), date(2026, 1, 1)) == 9


def test_full_profile_structure():
    prof = numerology.full_profile("Çağrı Yıldız", date(1990, 5, 12), date(2026, 1, 1))
    for key in ("life_path", "expression", "soul_urge", "personality",
                "birthday", "personal_year"):
        assert key in prof
        assert "value" in prof[key]
        assert "keywords" in prof[key]
        # her value için anahtar kelime tablosunda karşılık olmalı
        assert prof[key]["keywords"] == NUMBER_KEYWORDS.get(prof[key]["value"], "")

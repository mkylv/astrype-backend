"""Bilinçaltı (Shadow) modülü — test veri modeli + gölge puanlama.

4 adımlı psikolojik test; her cevap bir gölgeye +1 puan yazar. En yüksek puan
"Birincil Gölge" olur. Eşitlikte doğum haritasının Güneş/Ay elementi devreye
girer. Yorum (Jungcu + astroloji) OpenAI/Gemini ile üretilir.
"""
from __future__ import annotations

from typing import Any

# Gölge (shadow) değişkenleri ve görünen adları.
SHADOWS: dict[str, str] = {
    "shadow_control": "Kontrol İllüzyonu ve Kusursuzluk",
    "shadow_abandon": "Terk Edilme ve Mesafe Korkusu",
    "shadow_imposter": "Yetersizlik ve Zirvedeki Boşluk",
    "shadow_avoidance": "Duygusal Duvar Örme ve Kaçınma",
}

# Her gölgenin ana yaşam alanı (rapor 'category' alanı).
SHADOW_CATEGORY: dict[str, str] = {
    "shadow_control": "Kariyer, Üretim ve Yaşam Akışı",
    "shadow_abandon": "Aşk, Bağlanma ve Güven",
    "shadow_imposter": "Başarı, Değer ve Kimlik",
    "shadow_avoidance": "Aşk, İkili İlişkiler ve Yakınlık",
}

# Burç → element (deterministik).
_SIGN_ELEMENT: dict[str, str] = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

# Element → eşitlik bozan gölge (PRD: toprak→control, su→abandon; ateş/hava türetildi).
_ELEMENT_SHADOW: dict[str, str] = {
    "Earth": "shadow_control",
    "Water": "shadow_abandon",
    "Fire": "shadow_imposter",
    "Air": "shadow_avoidance",
}


def sign_element(sign: str | None) -> str | None:
    return _SIGN_ELEMENT.get((sign or "").strip().capitalize())


# 4 adımlı test. Görsel adım için image_url (ileride asset), şimdilik icon/desc.
# NOT: PDF'te 3 adım tam veriliyordu; 4. adım aynı üslupta tamamlandı.
TEST: list[dict[str, Any]] = [
    {
        "step": 1,
        "type": "visual_selection",
        "question": "Şu an zihnindeki sessizliği hangi imge en iyi tanımlıyor?",
        "options": [
            {"id": "1a", "icon": "sphere", "image_url": "/assets/images/golden_sphere.png",
             "description": "Ormanın ortasında kusursuz parlayan altın küre",
             "points_to": "shadow_control"},
            {"id": "1b", "icon": "door", "image_url": "/assets/images/iron_door.png",
             "description": "Ağır, oymalı ve kilitli devasa demir kapı",
             "points_to": "shadow_avoidance"},
            {"id": "1c", "icon": "lake", "image_url": "/assets/images/dark_lake.png",
             "description": "Yüzeyinin altında ne olduğu görünmeyen karanlık göl",
             "points_to": "shadow_abandon"},
            {"id": "1d", "icon": "gears", "image_url": "/assets/images/spinning_gears.png",
             "description": "Düzenli dizilmiş ama sürekli dönen çarklar",
             "points_to": "shadow_imposter"},
        ],
    },
    {
        "step": 2,
        "type": "scenario_career",
        "question": "Aylarca üzerinde çalıştığın sistemin tam lansman günündesin. "
                    "Her şey kusursuz görünürken, birden kritik bir darboğaz oluştu. "
                    "İlk tepkin nedir?",
        "options": [
            {"id": "2a", "text": "Hiçbir şey standardımda yapılamıyor. Her detayı kendim "
             "kontrol etmeliydim.", "points_to": "shadow_control"},
            {"id": "2b", "text": "İnsanlar ne düşünecek? Bütün o prestij ve algı bir anda "
             "yıkıldı.", "points_to": "shadow_imposter"},
            {"id": "2c", "text": "Zaten şansıma hep böyle olur, belki de bırakmalıyım.",
             "points_to": "shadow_avoidance"},
        ],
    },
    {
        "step": 3,
        "type": "scenario_relationship",
        "question": "Sana çok yakın olan kişi aniden aranıza mesafe koydu ve sessizleşti. "
                    "İlk hissettiğin duygu ne olur?",
        "options": [
            {"id": "3a", "text": "Terk edileceğimi düşünüp paniğe kapılır, onu geri "
             "kazanmak için tavizler veririm.", "points_to": "shadow_abandon"},
            {"id": "3b", "text": "İncinmemek için ben de sessizleşir, kendi içimde aşılmaz "
             "bir duvar örerim.", "points_to": "shadow_avoidance"},
            {"id": "3c", "text": "Bunu mantıklı bir düzleme oturtup sorunu hemen "
             "operasyonel bir kriz gibi çözmeye çalışırım.", "points_to": "shadow_control"},
        ],
    },
    {
        "step": 4,
        "type": "scenario_self",
        "question": "Uzun süredir istediğin bir başarıya nihayet ulaştın. Ama beklediğin "
                    "doyum gelmedi, içinde tuhaf bir boşluk var. Bu boşluğu nasıl "
                    "doldurursun?",
        "options": [
            {"id": "4a", "text": "Hemen bir sonraki, daha büyük hedefi koyarım; durursam "
             "değersiz hissederim.", "points_to": "shadow_imposter"},
            {"id": "4b", "text": "Kimseye belli etmem; bu boşluğu kimse görmesin diye "
             "mesafemi korurum.", "points_to": "shadow_avoidance"},
            {"id": "4c", "text": "Daha iyi planlasaydım bu boşluk olmazdı diye kendimi "
             "sıkıştırırım.", "points_to": "shadow_control"},
            {"id": "4d", "text": "Yanımda birileri olsa anlam kazanırdı; yalnız kalmaktan "
             "korkarım.", "points_to": "shadow_abandon"},
        ],
    },
]


def rank_shadows(
    picked: list[str], sun_sign: str | None = None, moon_sign: str | None = None
) -> tuple[list[str], dict[str, int]]:
    """Seçilen gölgeleri puanlayıp sıralar. Eşitliği Güneş/Ay elementi bozar.

    Döner: (sıralı_gölge_anahtarları, ham_puanlar). İlk eleman = Birincil Gölge.
    """
    counts: dict[str, int] = {k: 0 for k in SHADOWS}
    for p in picked:
        if p in counts:
            counts[p] += 1

    # Element tercihleri: Güneş 0.3, Ay 0.15 (kesir < 1 → gerçek puanı asla geçmez).
    prefs: list[str] = []
    for sign in (sun_sign, moon_sign):
        el = sign_element(sign)
        s = _ELEMENT_SHADOW.get(el) if el else None
        if s:
            prefs.append(s)

    order = list(SHADOWS.keys())  # sabit deterministik ikincil sıra

    def key(k: str) -> tuple[float, int]:
        boost = 0.0
        if prefs and prefs[0] == k:
            boost += 0.30
        if len(prefs) > 1 and prefs[1] == k:
            boost += 0.15
        return (counts[k] + boost, -order.index(k))

    ranked = sorted(SHADOWS, key=key, reverse=True)
    return ranked, counts

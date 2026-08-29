"""Astrype faturalama kataloğu — coin ekonomisi ürünlerinin TEK kaynağı.

Bu dosya hem RevenueCat webhook'unun (coin kazandırma) hem de mağaza/dashboard
kurulum dokümanının referansıdır. Store ürün id'leri burada tanımlanır; bunları
App Store Connect + Google Play + RevenueCat dashboard'unda AYNI id ile
oluşturmak gerekir.

Kaynak: design-refs/revisions/coinekonomisivefiyatlandirma.md
"""
from __future__ import annotations

# İlk coin alımında +%50 bonus (dönüşüm kampanyası).
FIRST_PURCHASE_BONUS_RATE = 0.50

# Aktif abonelere coin paketlerinde %20 indirim (mağaza fiyatında; ayrı offering).
SUBSCRIBER_PACK_DISCOUNT_RATE = 0.20

# Kayıt hediyesi (ilk gün "değer gördüm" hissi = dönüşüm kaldıracı).
SIGNUP_BONUS_COINS = 200

# Streak (7 gün üst üste giriş) ödülü + ödüllü reklam (opsiyonel).
STREAK_BONUS_COINS = 20
AD_REWARD_COINS = 5
AD_REWARD_DAILY_CAP = 2

# Lyra sohbet maliyeti (mesaj başı).
LYRA_MSG_COST = 3            # abonelik yoksa
LYRA_MSG_COST_SUBSCRIBER = 2  # abonelik günlük limiti bittikten sonra
LYRA_DAILY_DEFAULT = 50       # abone günlük ücretsiz mesaj (haftalıkta 30)

# ---- Coin paketleri (consumable): store product_id -> coin miktarı, USD fiyat ----
COIN_PACKS: dict[str, dict] = {
    "astrype_coins_100":  {"coins": 100,  "usd": 1.99,  "tag": None},
    "astrype_coins_300":  {"coins": 300,  "usd": 4.99,  "tag": None},
    "astrype_coins_650":  {"coins": 650,  "usd": 9.99,  "tag": "popular"},
    "astrype_coins_1500": {"coins": 1500, "usd": 19.99, "tag": "best_value"},
    "astrype_coins_4200": {"coins": 4200, "usd": 49.99, "tag": None},
    "astrype_coins_9000": {"coins": 9000, "usd": 99.99, "tag": None},
}

# ---- Abonelikler (auto-renewable): product_id -> plan ----
# coin_grant: her yenilemede yatan coin. welcome_bonus: yalnız ilk alımda.
# lyra_daily: günlük ücretsiz Lyra mesajı. entitlement RevenueCat entitlement id'si.
SUBSCRIPTIONS: dict[str, dict] = {
    "astrype_sub_weekly": {
        "period": "weekly",  "entitlement": "premium",
        "coin_grant": 150,  "welcome_bonus": 0,    "lyra_daily": 30, "usd": 4.99,
    },
    "astrype_sub_monthly": {
        "period": "monthly", "entitlement": "premium",
        "coin_grant": 700,  "welcome_bonus": 0,    "lyra_daily": 50, "usd": 9.99,
    },
    "astrype_sub_yearly": {
        "period": "yearly",  "entitlement": "premium",
        "coin_grant": 700,  "welcome_bonus": 1500, "lyra_daily": 50, "usd": 49.99,
        "trial_days": 3,
        # NOT: yıllık planda 400 coin AYLIK damlar; RevenueCat yılda bir RENEWAL
        # atacağı için aylık damlatma ayrı bir zamanlanmış işle (cron) yapılmalı.
        # İlk alımda welcome_bonus + ilk ay (coin_grant) yatar.
    },
}

# RevenueCat entitlement id -> uygulama tier eşlemesi.
# NOT: RevenueCat entitlement lookup_key immutable; mevcut projede "Astrype Premium".
ENTITLEMENT_TIER = {
    "premium": "premium",
    "Astrype Premium": "premium",
    "elite": "elite",
}

# Test Store (prototip) kısa store_identifier alias'ları — üretim App Store'da
# astrype_sub_* kullanılır; test satın almalarının da coin/tier üretmesi için.
for _short, _full in (
    ("weekly", "astrype_sub_weekly"),
    ("monthly", "astrype_sub_monthly"),
    ("yearly", "astrype_sub_yearly"),
):
    SUBSCRIPTIONS[_short] = SUBSCRIPTIONS[_full]


def coin_pack(product_id: str) -> dict | None:
    return COIN_PACKS.get(product_id)


def subscription(product_id: str) -> dict | None:
    return SUBSCRIPTIONS.get(product_id)


def lyra_daily_limit(product_id: str | None) -> int:
    sub = SUBSCRIPTIONS.get(product_id or "")
    return sub["lyra_daily"] if sub else LYRA_DAILY_DEFAULT

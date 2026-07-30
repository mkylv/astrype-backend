# Astrype Coin Ekonomisi — Kurulum & Aktivasyon

Backend "Yıldız Tozu" (coin) altyapısı **hazır ve deploy edilebilir** ama
`COINS_ENABLED=false` olduğu için **uykuda**. Aşağıdaki mağaza/RevenueCat
kurulumu bitince flag açılır ve ekonomi devreye girer.

> Ürün id'leri **birebir** aşağıdaki gibi olmalı — backend bunları
> `app/services/billing_catalog.py` içinde bu id'lerle tanır.

---

## 1. Store ürünleri (App Store Connect + Google Play Console)

### Abonelikler (auto-renewable subscription)
| product_id | Süre | Fiyat (USD) | Not |
|---|---|---|---|
| `astrype_sub_weekly` | Haftalık | $4.99 | 75 coin/hafta, 30 Lyra mesaj/gün |
| `astrype_sub_monthly` | Aylık | $9.99 | 400 coin/ay, 50 Lyra mesaj/gün |
| `astrype_sub_yearly` | Yıllık | $49.99 | 400 coin/ay + 1000 hoş geldin, 50 msg/gün, 3 gün deneme |

Üçü de **aynı abonelik grubunda** (tek "Premium" erişimi, farklı süre/fiyat).
Yıllık için 3 günlük **intro trial** tanımla.

### Coin paketleri (consumable)
| product_id | Coin | Fiyat (USD) | Etiket |
|---|---|---|---|
| `astrype_coins_100` | 100 | $1.99 | — |
| `astrype_coins_300` | 300 | $4.99 | — |
| `astrype_coins_650` | 650 | $9.99 | En popüler |
| `astrype_coins_1500` | 1500 | $19.99 | En avantajlı |
| `astrype_coins_4200` | 4200 | $49.99 | — |
| `astrype_coins_9000` | 9000 | $99.99 | — |

> Bölgesel fiyatlandırma: USD çapa fiyat + store'un otomatik bölge fiyatları.
> TR/AZ gibi pazarlarda fiyatı elle daha da düşürmek dönüşümü artırır (coin
> miktarı sabit kalır, sadece fiyat yerelleşir).

---

## 2. RevenueCat dashboard

1. **Entitlement** oluştur: `premium` (üç aboneliğe de bağla).
2. **Products**: yukarıdaki 9 store ürününü RevenueCat'e ekle (aynı id).
3. **Offering** oluştur (paywall için): abonelik paketleri + coin paketleri.
4. **App user ID = Supabase user id.** Flutter'da `Purchases.logIn(supabaseUserId)`
   çağrılmalı ki webhook `app_user_id` ile doğru kullanıcıya coin yatırsın.
5. **Webhook**: `POST https://astrype-backend.onrender.com/webhooks/revenuecat`
   - Authorization header (Bearer) = `REVENUECAT_WEBHOOK_SECRET` (Render env).

### Backend'in webhook'ta yaptığı (otomatik, idempotent — event id ile)
- Abonelik `INITIAL_PURCHASE`/`RENEWAL` → dönem coini yatar; yıllıkta ilk alımda
  +1000 welcome. `subscriptions` tablosu tier/is_active/product_id ile senkron.
- Coin paketi alımı → paket coini + (ilk alımsa) **%50 ilk-alım bonusu** yatar.
- Aynı webhook tekrar gelse çift yatmaz (event id idempotency).

> ⚠️ **Yıllık aylık damlatma:** yıllık plan 400 coin/ay verir ama RevenueCat
> yılda bir RENEWAL atar. İlk alımda welcome + ilk ay yatar; kalan 11 ayın
> aylık 400'ü **zamanlanmış bir cron** ile yatırılmalı (henüz yok — TODO).

---

## 3. Fiyatlandırma & erişim modeli (backend'de kurulu)

`feature_prices` tablosunda (uzaktan değiştirilebilir):

- **Ücretsiz:** Günlük Burç.
- **Devamlı (abonede sınırsız, değilse coin):** Tarot 40, Kahve 50, Rüya 40,
  Kozmik Uyum 60, Aylık Burç 30, Günlük Harita 10.
- **Tek seferlik (herkes coin öder, abone dahil):** Doğum Haritası 250,
  Yıldızname 300, İnsan Tasarımı 100, El Falı 75, Yüz Falı 75, Bilinçaltı 75,
  Numeroloji 60, Ebced 50.
- **Lyra sohbet:** abone günlük hakkı, sonrası mesaj başı 2 coin; abone değilse 3.

Ödeme kapsamı:
- Kimlik-temelli okumalar (natal, HD, numeroloji, ebced, yıldızname, bilinçaltı)
  **kişi başına bir kez** ödenir; tekrar açmak ücretsiz.
- Foto/girdi-temelli okumalar (el/yüz/kahve/tarot/rüya/uyum) **her seferinde**.
- Aylık burç ayda bir, günlük harita günde bir ödenir (dönem başına).
- Kayıt hediyesi: **100 coin** (ilk `/wallet` çağrısında idempotent yatar).

---

## 4. Aktivasyon

Yukarıdakiler hazır olunca:

1. Render env: `COINS_ENABLED=true` (+ `REVENUECAT_WEBHOOK_SECRET` dolu olmalı).
2. Manuel deploy tetikle.
3. Flutter'da: `purchases_flutter` SDK + `Purchases.logIn(userId)` + paywall/mağaza
   + `/wallet` (bakiye) ve `/wallet/catalog` (fiyatlar) uçlarını bağla + 402
   `INSUFFICIENT_COINS` yanıtında paywall aç.

Flag kapalıyken tüm okuma uçları eskisi gibi ücretsiz çalışır — güvenle deploy edilebilir.

---

## Uç noktalar

- `GET /wallet` → `{balance, first_purchase_done, transactions[]}` (kayıt bonusu burada yatar)
- `GET /wallet/catalog` → fiyat kataloğu + coin paketleri + abonelikler
- Okuma uçları 402 dönerse: `{code:"INSUFFICIENT_COINS", feature, needed, balance}`
- Başarılı okumalar yanıta `charge: {charged, cost, balance}` ekler.

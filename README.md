# Astrype Backend (FastAPI)

Astrype'ın backend'i: astro hesaplama soyutlaması, OpenAI yorum zinciri,
Cosmic Memory (pgvector RAG), görsel fal (foto silme), abonelik webhook'u.

> Build spec: kök dizindeki `claude.md` (Bölüm 1–16).

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # değerleri doldur
```

## Veritabanı (Supabase)

`supabase/migrations/` altındaki SQL'leri sırayla çalıştır:

1. `0001_init.sql` — pgvector + tablolar
2. `0002_rls.sql` — Row Level Security (her tabloda zorunlu)
3. `0003_match_memory.sql` — Cosmic Memory cosine arama RPC'si

Supabase CLI ile: `supabase db push` (veya SQL editöründe sırayla).

## Çalıştırma

```bash
uvicorn app.main:app --reload --port 8000
```

- Sağlık: `GET /health`
- OpenAPI: `http://localhost:8000/docs`

## Test

```bash
pytest -q
```

Birim testleri ağ gerektirmez (tarot çekimi, safety, RevenueCat event eşleme,
context derleme).

## Mimari kararlar

| Konu | Karar |
|---|---|
| Astro sağlayıcı | `AstroProvider` arayüzü; `app/services/astro/__init__.py` fabrikasından tek satır değiştirilerek Swiss Ephemeris / Skyfield'e geçilebilir. |
| AI güvenliği | `services/ai/safety.py` HER OpenAI çağrısına ilk sistem mesajı olarak `openai_client` içinde otomatik eklenir. |
| Maliyet | Günlük yorum `daily_insight_cache` ile gün boyu tek üretim. Embedding yalnızca anlamlı özetler için. |
| Foto gizliliği | Kahve/el falı fotoğrafı diske/Storage'a **hiç yazılmaz**; vision çıkarımından sonra bellekteki bytes bırakılır. Yalnızca sembol + sonuç arşivlenir. |
| Yetki | Tier kontrolü her zaman backend'de (`subscriptions`). RevenueCat webhook imzayla doğrulanır. |
| Anahtarlar | OpenAI/RapidAPI key'leri yalnızca backend'de; Flutter'dan AI çağrısı yapılmaz. |

## Uç noktalar (MVP)

| Endpoint | Method | Auth |
|---|---|---|
| `/profile` | GET/PUT | ✔ |
| `/chart` | POST | ✔ |
| `/chart/svg` | GET | ✔ |
| `/daily-insight` | GET | ✔ (cache'li) |
| `/tarot/pull`, `/tarot/spread` | POST | ✔ |
| `/reading/coffee`, `/reading/palm` | POST | ✔ premium |
| `/relationship` | POST | ✔ |
| `/chat` | POST | ✔ |
| `/readings` | GET | ✔ |
| `/memory` | DELETE | ✔ (KVKK/GDPR) |
| `/webhooks/revenuecat` | POST | secret |

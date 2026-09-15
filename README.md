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
| `/legal/privacy`, `/legal/terms` | GET | — (public HTML) |
| `/legal/source` | GET | — (307 → source repository) |

## Source code

This repository (https://github.com/mkylv/astrype-backend) is the complete
source code of the **Astrype backend service** that the Astrype mobile apps talk
to. As required by AGPL-3.0 §13, users of the network service are offered this
source: the in-app Terms of Use page (`/legal/terms`) links to it, and
`GET /legal/source` redirects to it (a stable link even if the repository moves).

**Secrets are not part of the source.** All credentials (Supabase, OpenAI,
RapidAPI, RevenueCat, …) are read only from environment variables at runtime.
`.env.example` documents every variable; the real `.env` is git-ignored and must
never be committed.

The Flutter mobile app is a separate program that communicates with this service
over HTTP and contains no AGPL code; it is not covered by this license.

## License

Copyright (C) 2026 Astrype.

This program is free software: you can redistribute it and/or modify it under
the terms of the **GNU Affero General Public License, version 3**
(`AGPL-3.0-only`). See [`LICENSE`](LICENSE).

**Why AGPL-3.0:** local astrology calculations use
[Kerykeion](https://github.com/g-battaglia/kerykeion) and
[pyswisseph](https://astrorigin.com/pyswisseph), the Python bindings for the
Swiss Ephemeris by Astrodienst AG, used under its AGPL option. Both are licensed
under AGPL v3, which requires a service built on them that is offered over a
network to publish its Corresponding Source under the same license. They ship
the plain AGPLv3 text without an "or any later version" grant, so this project
uses **-only** to match them.

Third-party components and their licenses: [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).

# Third-Party Licenses

The Astrype backend is licensed under the **GNU Affero General Public License
v3.0 only** (`AGPL-3.0-only`, see `LICENSE`). It includes or depends on the
third-party components listed below. Each component remains under its own
license; all of them are compatible with distribution under AGPL-3.0.

Versions and licenses were taken from the installed package metadata
(`importlib.metadata`) for the versions pinned in `requirements.txt`.

## Astrology calculation (copyleft; the reason this project is AGPL)

### Swiss Ephemeris
- **Copyright:** Astrodienst AG, Zürich, Switzerland (authors: Dieter Koch and
  Alois Treindl).
- **License:** Swiss Ephemeris is dual-licensed: either the GNU Affero General
  Public License v3 (AGPL) or the commercial Swiss Ephemeris Professional
  License. **Astrype uses Swiss Ephemeris under the AGPL option.**
- **Website:** https://www.astro.com/swisseph/
- **Data files:** The ephemeris data files (`*.se1`, e.g. `seas_18.se1`,
  `sefstars.txt`) are **not stored in this repository**. They ship inside
  the `kerykeion` package (`kerykeion/sweph/`) and are installed from PyPI by
  `pip install -r requirements.txt`.

### pyswisseph 2.10.3.2
- Python bindings for Swiss Ephemeris, by Stanislas Marquis.
- **License:** GNU Affero General Public License v3.
- https://astrorigin.com/pyswisseph

### Kerykeion 5.x
- Astrology library (natal charts, synastry, SVG charts), by Giacomo Battaglia.
- **License:** AGPL-3.0.
- https://github.com/g-battaglia/kerykeion

## Other runtime dependencies (permissive)

| Package | Version | License |
|---|---|---|
| fastapi | 0.115.6 | MIT |
| starlette | 0.41.3 | BSD-3-Clause |
| uvicorn[standard] | 0.34.0 | BSD-3-Clause |
| uvloop | 0.22.1 | MIT OR Apache-2.0 |
| httptools | 0.8.0 | MIT |
| watchfiles | 1.2.0 | MIT |
| websockets | 15.0.1 | BSD-3-Clause |
| pydantic / pydantic-core | 2.10.4 / 2.27.2 | MIT |
| pydantic-settings | 2.7.1 | MIT |
| httpx / httpcore | 0.28.1 / 1.0.9 | BSD-3-Clause |
| python-jose[cryptography] | 3.3.0 | MIT |
| cryptography | 49.0.0 | Apache-2.0 OR BSD-3-Clause |
| ecdsa | 0.19.2 | MIT |
| rsa | 4.9.1 | Apache-2.0 |
| pyasn1 | 0.6.3 | BSD-2-Clause |
| supabase (+ gotrue, postgrest, realtime, storage3, supafunc) | 2.11.0 | MIT |
| openai | 1.59.6 | Apache-2.0 |
| python-multipart | 0.0.20 | Apache-2.0 |
| tenacity | 9.0.0 | Apache-2.0 |
| pytz | 2026.2 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| requests-cache | 1.3.2 | BSD-2-Clause |
| scour | 0.38.2 | Apache-2.0 |
| simple-ascii-tables | 1.0.1 | MIT |
| certifi | 2026.5.20 | MPL-2.0 |
| tqdm | 4.68.2 | MPL-2.0 AND MIT |
| typing-extensions | 4.15.0 | PSF-2.0 |
| anyio / sniffio / h11 / jiter / distro | — | MIT / MIT OR Apache-2.0 / MIT / MIT / Apache-2.0 |

Development only (not part of the running service): pytest (MIT), pluggy (MIT),
iniconfig (MIT), Pygments (BSD-2-Clause).

## Compatibility notes

- MIT, BSD, Apache-2.0, PSF-2.0 and MPL-2.0 are all compatible with AGPL-3.0.
- No dependency is proprietary or under a license incompatible with AGPL-3.0.
- Kerykeion and pyswisseph publish the plain AGPLv3 text without an explicit
  "or any later version" grant, so the combined work is distributed as
  `AGPL-3.0-only`.

## External services (not distributed code)

The backend calls network APIs (OpenAI, Google Gemini, Supabase, RevenueCat,
RapidAPI). These are remote services governed by their own terms. No client
code from them is bundled here beyond the open-source SDKs listed above.
API keys are never stored in this repository; see `.env.example`.

"""Halka açık web sitesi — astrype.com ana sayfası + destek sayfası.

App Store listelemesi https://astrype.com adresini hem Support URL hem Marketing
URL olarak bildiriyor; bu modül o iki sayfayı backend'den sunar:

    GET /          -> tanıtım (landing) sayfası
    GET /support   -> destek / iletişim / SSS sayfası

Dil: yalnızca **tr** ve **en**. Çözümleme yasal sayfalarla aynı zincire dayanır
(``routes_legal.resolve_lang``: ?lang= -> Accept-Language -> en); sonuç tr
değilse İngilizce'ye düşer. Site 20 dile çevrilmez — yasal metinler çevrilidir
ve alt bilgideki bağlantılar geçerli dille /legal/... adreslerine gider.

İçerik kuralları (CLAUDE.md §0, §12, §16):
  * Eğlence / kişisel içgörü disclaimer'ı her iki sayfada görünür.
  * Kesin kehanet, tıbbi/hukuki/finansal tavsiye vaadi yok.
  * Kahve/el/yüz falı fotoğrafı analizden hemen sonra sunucudan silinir — açıkça yazılır.
  * Uydurma referans, kullanıcı sayısı, basın logosu veya aciliyet oyunu yok.

Sunum (2026 revizyonu — görsel + hareket katmanı):
  * Şablon motoru yok; her şey düz f-string (Jinja2 kurulu değil).
  * Marka kilidi (ikon + kelime işareti) satır içi SVG olarak çizilir.
  * Hareket üç katmanda: canvas yıldız alanı, CSS ile dönen zodyak çarkı ve
    IntersectionObserver tabanlı scroll-reveal. Üçü de
    ``prefers-reduced-motion`` altında ve JavaScript kapalıyken tamamen devre
    dışı kalır; sayfa hareketsizken de eksiksiz görünür (içerik asla
    opacity:0 ile beklemez — gizleme sınıfı yalnızca JS ekliyse eklenir).

Görseller ``app/static/img`` altında (StaticFiles ile /static'ten sunulur).
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Header, Query
from fastapi.responses import HTMLResponse

from app.api.routes_legal import resolve_lang

router = APIRouter(tags=["site"])

SITE_LANGS = ("en", "tr")
SITE_DEFAULT_LANG = "en"

# Tek kaynak: her iki sayfadaki bütün mailto bağlantıları buradan gelir.
CONTACT_EMAIL = "support@astrype.com"

# --- Mağaza bağlantıları -------------------------------------------------
# Uygulama henüz yayında değil. Yayınlandığında YALNIZCA bu iki satır
# doldurulur; şablon otomatik olarak "yakında" rozetini gerçek bağlantıya
# çevirir (rozet grileşmesi kalkar, <span> yerine <a> gelir). Boş string =
# yayında değil.
APP_STORE_URL = ""
PLAY_STORE_URL = ""

# Abonelik yönetimi — mağazaların kalıcı, uygulamadan bağımsız adresleri.
APPLE_SUBSCRIPTIONS_URL = "https://apps.apple.com/account/subscriptions"
GOOGLE_SUBSCRIPTIONS_URL = "https://play.google.com/store/account/subscriptions"

# Google Play resmî rozeti (play.google.com/intl/en_us/badges/... adresinden
# indirildi, değiştirilmeden sunulur). Apple rozeti Apple'ın pazarlama
# kaynaklarına kayıtlı erişim gerektirdiğinden aşağıda satır içi SVG olarak
# çizilir; yayın öncesi resmî varlıkla değiştirilmelidir.
PLAY_BADGE_IMG = "/static/img/play-badge.png"


# --------------------------------------------------------------------------
# Satır içi SVG — marka kilidi, zodyak çarkı, mağaza rozetleri
# --------------------------------------------------------------------------


def _brand_mark(uid: str, size: int = 34) -> str:
    """Uygulama ikonunun (altın kadran + kuyruklu yıldız) vektör karşılığı.

    32-36 px'te okunur kalması için kadran sadeleştirildi: ince 24 çentik
    yerine 8 belirgin çentik, kalın altın çember ve merkezde küçük güneş."""
    ticks = []
    for i in range(8):
        a = math.radians(i * 45)
        r1, r2 = 15.4, 12.2
        ticks.append(
            '<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="#D6A93A" '
            'stroke-width="1.5" stroke-linecap="round" opacity=".9" />'.format(
                22 + r1 * math.sin(a), 26 - r1 * math.cos(a),
                22 + r2 * math.sin(a), 26 - r2 * math.cos(a),
            )
        )
    return (
        f'<svg class="mark" width="{size}" height="{size}" viewBox="0 0 48 48" '
        'aria-hidden="true" focusable="false">'
        f'<defs><radialGradient id="{uid}g" cx="42%" cy="38%" r="76%">'
        '<stop offset="0" stop-color="#2B2258" /><stop offset="1" stop-color="#0A0813" />'
        "</radialGradient></defs>"
        f'<rect width="48" height="48" rx="12" fill="url(#{uid}g)" />'
        '<rect x="0.6" y="0.6" width="46.8" height="46.8" rx="11.4" fill="none" '
        'stroke="#A77B24" stroke-width="1.2" opacity=".7" />'
        '<circle cx="22" cy="26" r="15.4" fill="none" stroke="#D6A93A" stroke-width="1.5" />'
        + "".join(ticks)
        + '<circle cx="22" cy="26" r="5.2" fill="none" stroke="#F5C96B" stroke-width="1.3" />'
        '<circle cx="22" cy="26" r="2.2" fill="#F5C96B" />'
        '<path d="M29.8 8.6A20 20 0 0 1 42.6 20.4" fill="none" stroke="#F5C96B" '
        'stroke-width="1.5" stroke-linecap="round" opacity=".9" />'
        '<path d="M38.6 9.2 40.1 13.1 44 14.6 40.1 16.1 38.6 20 37.1 16.1 33.2 14.6 37.1 13.1Z" '
        'fill="#F5C96B" />'
        "</svg>"
    )


_ZODIAC = "♈♉♊♋♌♍♎♏♐♑♒♓"


def _zodiac_wheel() -> str:
    """Kahraman bölümünün arkasında yavaşça dönen zodyak çarkı (dekoratif)."""
    cx = cy = 200.0
    parts = [
        '<circle cx="200" cy="200" r="192" fill="none" stroke="#A77B24" stroke-width="0.8" opacity=".35" />',
        '<circle cx="200" cy="200" r="176" fill="none" stroke="#D6A93A" stroke-width="0.7" opacity=".45" />',
        '<circle cx="200" cy="200" r="132" fill="none" stroke="#A77B24" stroke-width="0.7" opacity=".3" />',
    ]
    for i in range(72):
        a = math.radians(i * 5)
        major = i % 6 == 0
        r1, r2 = 176.0, (162.0 if major else 169.0)
        parts.append(
            '<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="#D6A93A" '
            'stroke-width="{}" opacity="{}" />'.format(
                cx + r1 * math.sin(a), cy - r1 * math.cos(a),
                cx + r2 * math.sin(a), cy - r2 * math.cos(a),
                1.1 if major else 0.6, ".7" if major else ".35",
            )
        )
    for i, glyph in enumerate(_ZODIAC):
        a = math.radians(i * 30 + 15)
        x, y = cx + 152 * math.sin(a), cy - 152 * math.cos(a)
        parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="19" fill="#F5C96B" opacity=".8">{glyph}</text>'
        )
    inner = [
        '<circle cx="200" cy="200" r="92" fill="none" stroke="#A77B24" stroke-width="0.7" opacity=".35" />',
        '<circle cx="200" cy="200" r="30" fill="none" stroke="#F5C96B" stroke-width="0.9" opacity=".6" />',
        '<circle cx="200" cy="200" r="4" fill="#F5C96B" opacity=".9" />',
    ]
    for i in range(12):
        a = math.radians(i * 30)
        inner.append(
            '<line x1="{:.2f}" y1="{:.2f}" x2="{:.2f}" y2="{:.2f}" stroke="#A77B24" '
            'stroke-width="0.6" opacity=".4" />'.format(
                cx + 30 * math.sin(a), cy - 30 * math.cos(a),
                cx + 92 * math.sin(a), cy - 92 * math.cos(a),
            )
        )
    return (
        '<svg class="wheel" viewBox="0 0 400 400" aria-hidden="true" focusable="false">'
        '<g class="wheel-outer">' + "".join(parts) + "</g>"
        '<g class="wheel-inner">' + "".join(inner) + "</g>"
        "</svg>"
    )


# Apple logosu — satır içi silüet. Apple Inc.'in tescilli markasıdır; bu rozet
# resmî varlığın yer tutucusudur ve yayından önce Apple'ın kendi rozetiyle
# değiştirilmelidir.
_APPLE_GLYPH = (
    "M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 "
    "20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 "
    "36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 "
    "90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 "
    "24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"
)


def _apple_badge_svg(label: str) -> str:
    return (
        '<svg class="badge-art apple" viewBox="0 0 120 40" role="img" '
        f'aria-label="{label}"><title>{label}</title>'
        '<rect x="0.6" y="0.6" width="118.8" height="38.8" rx="8.6" fill="#000000" '
        'stroke="#A6A6A6" stroke-width="1.1" />'
        f'<g fill="#FFFFFF" transform="translate(10.6,9.6) scale(0.0391)"><path d="{_APPLE_GLYPH}" /></g>'
        '<text x="30.5" y="16.1" fill="#FFFFFF" font-family="Inter,Helvetica Neue,Arial,sans-serif" '
        'font-size="7.6" letter-spacing="0.15">Download on the</text>'
        '<text x="29.8" y="31.4" fill="#FFFFFF" font-family="Inter,Helvetica Neue,Arial,sans-serif" '
        'font-size="16.6" font-weight="600" letter-spacing="-0.2">App Store</text>'
        "</svg>"
    )


# --------------------------------------------------------------------------
# Stil
# --------------------------------------------------------------------------

_STYLE = """
:root{
  color-scheme:dark;
  --bg:#0A0813; --bg2:#120E24; --surface:#1A1433; --surface2:#140F28;
  --line:#2A2150; --gold:#D6A93A; --rich:#F5C96B; --old:#A77B24;
  --ivory:#FAF8F2; --text:#CFC7DE; --muted:#9C92BA;
  --pad:clamp(16px,4vw,28px);
  --ease:cubic-bezier(.2,.8,.2,1);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:88px}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}
svg{display:block}
a{color:var(--rich)}
a:focus-visible,summary:focus-visible,button:focus-visible{
  outline:2px solid var(--rich);outline-offset:3px;border-radius:6px}
.wrap{width:100%;max-width:1120px;margin:0 auto;padding:0 var(--pad)}
.narrow{max-width:800px}
.skip{position:absolute;left:-9999px;top:auto}
.skip:focus{position:fixed;left:14px;top:14px;z-index:99;background:var(--surface);
  color:var(--ivory);padding:10px 16px;border-radius:10px;border:1px solid var(--gold);
  text-decoration:none}

/* ---------- header ---------- */
header.site{position:sticky;top:0;z-index:30;
  background:rgba(10,8,19,.88);
  -webkit-backdrop-filter:saturate(140%) blur(14px);backdrop-filter:saturate(140%) blur(14px);
  border-bottom:1px solid rgba(42,33,80,.9);
  transition:background .35s ease,border-color .35s ease,box-shadow .35s ease}
header.site::after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,transparent,rgba(214,169,58,.45),transparent);opacity:.9}
/* Saydam baslik yalnizca JS varken: JS kapaliyken baslik her zaman
   okunakli, yari opak zeminde kalir (at-top sinifi etkisiz olur). */
html.js-head header.site.at-top{background:transparent;border-bottom-color:transparent;
  -webkit-backdrop-filter:none;backdrop-filter:none}
html.js-head header.site.at-top::after{opacity:0}
html.js-head header.site:not(.at-top){box-shadow:0 18px 40px -30px rgba(0,0,0,.95)}
.bar{display:flex;align-items:center;gap:14px;justify-content:space-between;
  min-height:66px;padding:10px var(--pad)}
.brand{display:inline-flex;align-items:center;gap:11px;text-decoration:none;flex:0 0 auto}
.brand .mark{flex:none;filter:drop-shadow(0 0 12px rgba(214,169,58,.28));
  transition:transform .4s var(--ease)}
.brand:hover .mark{transform:rotate(6deg)}
.brand .wm{font-family:'Cinzel',Georgia,serif;font-weight:600;font-size:19px;
  letter-spacing:.2em;text-transform:uppercase;color:var(--rich);line-height:1}
@supports((-webkit-background-clip:text) or (background-clip:text)){
  .brand .wm{background:linear-gradient(180deg,#FFF3C4 5%,#D6A93A 85%);
    -webkit-background-clip:text;background-clip:text;color:transparent}}
.nav{display:flex;align-items:center;gap:2px}
.nav a{color:var(--muted);text-decoration:none;font-size:14px;padding:9px 12px;
  border-radius:999px;transition:color .22s ease,background .22s ease}
.nav a:hover{color:var(--rich);background:rgba(214,169,58,.09)}
.nav a[aria-current]{color:var(--rich)}
.tools{display:flex;align-items:center;gap:10px;flex:0 0 auto}
.langsw{display:inline-flex;align-items:stretch;border:1px solid var(--line);
  border-radius:999px;overflow:hidden;background:rgba(26,20,51,.55)}
.langsw a{font-size:11.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  padding:7px 11px;color:var(--muted);text-decoration:none;line-height:1.2;
  transition:color .22s ease,background .22s ease}
.langsw a:hover{color:var(--rich)}
.langsw a[aria-current]{color:#17120B;
  background:linear-gradient(180deg,#F5C96B,#D6A93A)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;
  text-decoration:none;font-weight:600;font-size:14px;border-radius:999px;
  padding:11px 20px;white-space:nowrap;
  transition:transform .2s var(--ease),box-shadow .3s ease,background .3s ease}
.btn-gold{background:linear-gradient(180deg,#F5C96B,#D6A93A);color:#17120B;
  box-shadow:0 0 0 rgba(245,201,107,0)}
.btn-gold:hover{transform:translateY(-1px);box-shadow:0 0 24px rgba(245,201,107,.28)}
.btn-ghost{border:1px solid var(--old);color:var(--rich)}
.btn-ghost:hover{background:rgba(214,169,58,.1);transform:translateY(-1px)}
.btn .short{display:none}
@media(max-width:760px){.nav .sec{display:none}}
@media(max-width:560px){
  .bar{gap:8px;min-height:60px}
  .brand .wm{font-size:15px;letter-spacing:.16em}
  .nav{display:none}
  .btn{padding:9px 14px;font-size:13px}
  .btn .full{display:none}.btn .short{display:inline}
  .langsw a{padding:6px 8px;font-size:11px;letter-spacing:.1em}
}

/* ---------- hero ---------- */
.hero{position:relative;overflow:hidden;padding:clamp(56px,9vw,104px) 0 clamp(48px,7vw,80px);
  background:
    radial-gradient(64% 48% at 50% -6%, rgba(214,169,58,.16), transparent 68%),
    radial-gradient(80% 60% at 84% 14%, rgba(66,49,124,.42), transparent 70%),
    radial-gradient(70% 55% at 6% 62%, rgba(40,28,82,.5), transparent 72%),
    linear-gradient(180deg,#0A0813,#0C0A1A 60%,#0A0813);
  border-bottom:1px solid rgba(42,33,80,.7)}
.hero::before{content:'';position:absolute;inset:0;pointer-events:none;opacity:.55;
  background-image:
    radial-gradient(1.4px 1.4px at 12% 18%, rgba(250,248,242,.75), transparent),
    radial-gradient(1.2px 1.2px at 27% 62%, rgba(245,201,107,.7), transparent),
    radial-gradient(1.3px 1.3px at 41% 12%, rgba(250,248,242,.6), transparent),
    radial-gradient(1.1px 1.1px at 58% 78%, rgba(250,248,242,.55), transparent),
    radial-gradient(1.4px 1.4px at 73% 30%, rgba(245,201,107,.6), transparent),
    radial-gradient(1.2px 1.2px at 86% 66%, rgba(250,248,242,.6), transparent),
    radial-gradient(1.1px 1.1px at 94% 22%, rgba(250,248,242,.5), transparent),
    radial-gradient(1.2px 1.2px at 6% 86%, rgba(245,201,107,.5), transparent)}
canvas.stars{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;
  display:block;z-index:0}
.hero .wrap{position:relative;z-index:1}
.hero-grid{display:grid;gap:clamp(36px,5vw,56px);grid-template-columns:1fr;align-items:center}
.hero-grid>*{min-width:0}
@media(min-width:900px){.hero-grid{grid-template-columns:1.04fr .96fr}}
.overline{font-family:'Cinzel',Georgia,serif;font-size:11.5px;letter-spacing:.3em;
  text-transform:uppercase;color:var(--gold);margin:0 0 16px;display:flex;
  align-items:center;gap:12px}
.overline::after{content:'';height:1px;flex:1;max-width:120px;
  background:linear-gradient(90deg,rgba(167,123,36,.75),transparent)}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;
  font-size:clamp(38px,7.4vw,66px);line-height:1.08;color:var(--ivory);
  margin:0 0 20px;letter-spacing:.005em}
h1 em{font-style:normal;color:var(--rich);
  text-shadow:0 0 40px rgba(245,201,107,.22)}
.lede{font-size:clamp(16px,2.2vw,18.5px);color:var(--text);margin:0 0 28px;max-width:35em}
.herolist{display:flex;flex-wrap:wrap;gap:8px 10px;list-style:none;margin:0 0 30px;padding:0}
.herolist li{font-size:12.5px;letter-spacing:.02em;color:var(--text);
  border:1px solid rgba(167,123,36,.4);background:rgba(26,20,51,.5);
  border-radius:999px;padding:6px 13px;line-height:1.4}
.herolist li b{color:var(--rich);font-weight:600}
.hero-art{position:relative;display:grid;place-items:center;min-height:320px}
.wheel{position:absolute;width:min(126%,560px);height:auto;aspect-ratio:1;
  opacity:.42;pointer-events:none;z-index:0}
.wheel-outer{transform-origin:50% 50%;animation:spin 240s linear infinite}
.wheel-inner{transform-origin:50% 50%;animation:spin 150s linear infinite reverse}
@keyframes spin{to{transform:rotate(360deg)}}
.device{position:relative;z-index:1;width:min(84%,290px);border-radius:26px;
  padding:6px;background:linear-gradient(160deg,rgba(245,201,107,.5),rgba(167,123,36,.12) 42%,rgba(42,33,80,.5));
  box-shadow:0 40px 90px -40px rgba(0,0,0,.95),0 0 60px -20px rgba(214,169,58,.28);
  will-change:transform}
.device img{width:100%;border-radius:21px;display:block}
.device::after{content:'';position:absolute;left:12%;right:12%;bottom:-26px;height:36px;
  border-radius:50%;background:radial-gradient(50% 50% at 50% 50%,rgba(214,169,58,.35),transparent 70%);
  filter:blur(6px);pointer-events:none}

/* ---------- store badges ---------- */
.getbox{margin:0}
.soonpill{display:inline-flex;align-items:center;gap:8px;margin:0 0 14px;
  font-family:'Cinzel',Georgia,serif;font-size:11px;letter-spacing:.26em;
  text-transform:uppercase;color:var(--rich);border:1px solid rgba(167,123,36,.55);
  background:rgba(214,169,58,.08);border-radius:999px;padding:6px 14px}
.stores{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 16px;padding:0;list-style:none}
.store{position:relative;display:inline-flex;align-items:center;justify-content:center;
  height:77px;border-radius:16px;text-decoration:none;
  transition:transform .25s var(--ease),filter .3s ease,box-shadow .3s ease}
.store .badge-art{display:block}
/* Play rozetinin kendi kenar boslugu var (646x250 icinde 564x168 gorunur kutu);
   Apple rozetine ayni optik boslugu vererek iki rozet ayni yuksekte hizalanir. */
.store img.badge-art{width:200px;height:77px}
.store--apple{padding:0 12.7px}
.store .apple{width:156px;height:52px}
.store--soon{cursor:default;filter:grayscale(.6) brightness(.68) contrast(.92)}
.store--soon:hover{filter:grayscale(.3) brightness(.86)}
a.store:hover,a.store:focus-visible{transform:translateY(-3px);
  box-shadow:0 18px 38px -20px rgba(245,201,107,.6)}
.storenote{font-size:13.5px;color:var(--muted);margin:0;max-width:40em}

/* ---------- sections ---------- */
main{display:block}
section{padding:clamp(56px,8vw,104px) 0;position:relative}
section+section{border-top:1px solid rgba(42,33,80,.55)}
section.alt{background:
  radial-gradient(60% 50% at 50% 0%, rgba(40,28,82,.35), transparent 70%),
  linear-gradient(180deg,#0B0916,#0A0813)}
.eyebrow{font-family:'Cinzel',Georgia,serif;font-size:11px;letter-spacing:.3em;
  text-transform:uppercase;color:var(--gold);margin:0 0 14px;display:flex;
  align-items:center;gap:12px}
.eyebrow::after{content:'';height:1px;flex:1;max-width:140px;
  background:linear-gradient(90deg,rgba(167,123,36,.7),transparent)}
h2{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;
  font-size:clamp(30px,4.8vw,44px);color:var(--ivory);margin:0 0 14px;line-height:1.14}
h3{font-family:'Inter',sans-serif;font-size:17px;font-weight:600;color:var(--ivory);
  margin:0 0 8px;letter-spacing:.005em}
.sub{color:var(--muted);margin:0 0 40px;max-width:46em;font-size:16.5px}
section p{margin:0 0 16px}
section p:last-child{margin-bottom:0}

.cards{display:grid;gap:16px;grid-template-columns:1fr}
.cards>*{min-width:0}
@media(min-width:620px){.cards{grid-template-columns:repeat(2,1fr)}}
@media(min-width:980px){.cards{grid-template-columns:repeat(3,1fr)}}
.card{position:relative;overflow:hidden;border-radius:18px;padding:24px 22px 26px;
  border:1px solid var(--line);
  background:linear-gradient(170deg,rgba(26,20,51,.85),rgba(19,14,38,.85));
  transition:transform .3s var(--ease),border-color .3s ease,box-shadow .3s ease}
.card::before{content:'';position:absolute;inset:0;pointer-events:none;opacity:0;
  background:radial-gradient(120% 80% at 50% -18%,rgba(245,201,107,.16),transparent 62%);
  transition:opacity .35s ease}
.card:hover{transform:translateY(-5px);border-color:rgba(167,123,36,.7);
  box-shadow:0 26px 50px -30px rgba(0,0,0,.95)}
.card:hover::before{opacity:1}
.card>*{position:relative}
.card .glyph{width:42px;height:42px;display:flex;align-items:center;justify-content:center;
  border-radius:13px;border:1px solid rgba(167,123,36,.55);background:rgba(214,169,58,.08);
  color:var(--rich);font-size:19px;line-height:1;margin-bottom:15px;
  transition:box-shadow .35s ease,background .35s ease}
.card:hover .glyph{background:rgba(214,169,58,.16);box-shadow:0 0 22px rgba(245,201,107,.25)}
.card p{margin:0;font-size:14.8px;color:var(--text)}

.shots{display:grid;gap:16px;grid-template-columns:repeat(2,1fr)}
@media(min-width:840px){.shots{grid-template-columns:repeat(4,1fr)}}
.shots>*{min-width:0}
.shots figure{margin:0;will-change:transform}
.shots .frame{border-radius:18px;padding:5px;
  background:linear-gradient(160deg,rgba(245,201,107,.34),rgba(42,33,80,.5));
  box-shadow:0 26px 50px -34px rgba(0,0,0,.95);
  transition:transform .35s var(--ease),box-shadow .35s ease;will-change:transform}
.shots figure:hover .frame{transform:translateY(-6px);
  box-shadow:0 30px 56px -28px rgba(245,201,107,.35)}
.shots img{width:100%;border-radius:14px}
.shots figcaption{font-size:13px;color:var(--muted);margin-top:10px;line-height:1.5}

.split{display:grid;gap:clamp(30px,4.5vw,56px);grid-template-columns:1fr;align-items:center}
@media(min-width:880px){.split{grid-template-columns:1.02fr .98fr}}
.split>*{min-width:0}
.split .shot{position:relative;display:grid;place-items:center}
.split .device{width:min(78%,268px)}

ul.plain{margin:0;padding:0;list-style:none;display:grid;gap:12px}
ul.plain li{position:relative;padding-left:28px;font-size:15.2px}
ul.plain li::before{content:'\\2726';position:absolute;left:0;top:.05em;color:var(--gold);font-size:13px}
ul.links{display:grid;gap:10px;margin:0;padding:0;list-style:none}

.note{background:linear-gradient(170deg,rgba(26,20,51,.9),rgba(19,14,38,.9));
  border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:14px;padding:18px 20px;color:var(--ivory);font-size:14.6px;line-height:1.65}
.note strong{color:var(--rich)}

.panel{border:1px solid var(--line);border-radius:22px;padding:clamp(26px,4vw,44px);
  background:
    radial-gradient(70% 90% at 12% 0%, rgba(214,169,58,.12), transparent 62%),
    linear-gradient(170deg,rgba(26,20,51,.92),rgba(16,12,32,.92));
  box-shadow:0 30px 60px -40px rgba(0,0,0,.9)}
.panel h2{margin-bottom:10px}

details{background:linear-gradient(170deg,rgba(26,20,51,.75),rgba(19,14,38,.75));
  border:1px solid var(--line);border-radius:14px;padding:0;margin-bottom:10px;
  transition:border-color .25s ease,background .25s ease}
details:hover{border-color:rgba(167,123,36,.6)}
details[open]{border-color:rgba(167,123,36,.7)}
summary{cursor:pointer;padding:15px 20px;color:var(--ivory);font-weight:600;
  font-size:15.5px;list-style:none;display:flex;justify-content:space-between;gap:16px}
summary::-webkit-details-marker{display:none}
summary::after{content:'+';color:var(--gold);font-weight:400;font-size:18px;line-height:1.3}
details[open] summary::after{content:'\\2212'}
details .answer{padding:0 20px 18px;font-size:14.6px}
details .answer p{margin:0 0 10px}
details .answer p:last-child{margin:0}

.contactbox{border:1px solid var(--line);border-radius:18px;padding:26px;
  background:radial-gradient(80% 120% at 10% 0%,rgba(214,169,58,.12),transparent 60%),
    linear-gradient(170deg,rgba(26,20,51,.9),rgba(16,12,32,.9))}
.contactbox .mail{font-family:'Cormorant Garamond',Georgia,serif;
  font-size:clamp(24px,4.4vw,34px);color:var(--rich);text-decoration:none;
  word-break:break-word;line-height:1.2;display:inline-block}
.contactbox .mail:hover{text-shadow:0 0 28px rgba(245,201,107,.4)}

/* ---------- footer ---------- */
footer.site{border-top:1px solid var(--line);padding:clamp(44px,6vw,72px) 0 48px;
  color:var(--muted);font-size:13.8px;
  background:linear-gradient(180deg,#0A0813,#0B0917)}
.footgrid{display:grid;gap:32px;grid-template-columns:1fr;margin-bottom:36px}
@media(min-width:760px){.footgrid{grid-template-columns:1.4fr 1fr 1fr;gap:40px}}
.footbrand .brand{margin-bottom:14px}
.foottag{margin:0;max-width:30em;color:var(--muted)}
.footcol h4{font-family:'Cinzel',Georgia,serif;font-size:11px;letter-spacing:.26em;
  text-transform:uppercase;color:var(--gold);margin:0 0 14px;font-weight:600}
.footcol ul{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.footcol a{color:var(--muted);text-decoration:none;transition:color .2s ease}
.footcol a:hover{color:var(--rich)}
.footbottom{border-top:1px solid rgba(42,33,80,.7);padding-top:22px;display:grid;gap:14px}
.footbottom .langsw{justify-self:start}
.disclaimer{font-size:13px;color:var(--muted);max-width:62em;margin:0}
.copy{margin:0;font-size:12.5px;color:#7d75a0}

/* ---------- hareket ---------- */
html.js-motion .reveal{opacity:0;transform:translateY(20px);
  transition:opacity .7s ease,transform .7s var(--ease)}
html.js-motion .reveal.in{opacity:1;transform:none}
html.js-motion .stagger>*{opacity:0;transform:translateY(18px);
  transition:opacity .6s ease,transform .6s var(--ease)}
html.js-motion .stagger.in>*{opacity:1;transform:none}
STAGGER_DELAYS
@media(prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important;scroll-behavior:auto!important}
  html{scroll-behavior:auto}
  .reveal,.reveal.in,.stagger>*,.stagger.in>*{opacity:1!important;transform:none!important}
  .device,.shots .frame{transform:none!important}
  canvas.stars{display:none}
}
@media print{canvas.stars,.wheel{display:none}}
"""

_STYLE = _STYLE.replace(
    "STAGGER_DELAYS",
    "".join(
        f"html.js-motion .stagger.in>*:nth-child({i}){{transition-delay:{(i - 1) * 55}ms}}"
        for i in range(1, 13)
    ),
)

# Hareket yalnızca JS varsa ve kullanıcı azaltılmış hareket istemiyorsa açılır.
# <head> içinde çalışır: gizleme sınıfı ancak gözlemci kesinlikle çalışacaksa
# eklenir, böylece JS kapalıyken hiçbir bölüm opacity:0'da takılı kalmaz.
_HEAD_SCRIPT = (
    "<script>try{var r=document.documentElement;r.classList.add('js-head');"
    "if('IntersectionObserver' in window&&window.matchMedia&&"
    "!matchMedia('(prefers-reduced-motion: reduce)').matches){"
    "r.classList.add('js-motion')}}catch(e){}</script>"
)

_SCRIPT = """
(function(){
  var d=document, root=d.documentElement, w=window;
  var reduce=false;
  try{reduce=w.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){}

  /* --- header durumu + telefon parallax --- */
  var head=d.querySelector('header.site');
  var para=[].slice.call(d.querySelectorAll('[data-parallax]'));
  var ticking=false;
  function paint(){
    ticking=false;
    var y=w.pageYOffset||root.scrollTop||0;
    if(head){ if(y<8){head.classList.add('at-top');} else {head.classList.remove('at-top');} }
    if(reduce||para.length===0||w.innerWidth<720) return;
    var vh=w.innerHeight||1;
    for(var i=0;i<para.length;i++){
      var el=para[i], r=el.getBoundingClientRect();
      if(r.bottom<-200||r.top>vh+200) continue;
      var p=(r.top+r.height/2-vh/2)/vh;
      if(p>1)p=1; if(p<-1)p=-1;
      var amt=parseFloat(el.getAttribute('data-parallax'))||16;
      el.style.transform='translate3d(0,'+(p*-amt).toFixed(1)+'px,0)';
    }
  }
  function onScroll(){ if(!ticking){ticking=true;requestAnimationFrame(paint);} }
  w.addEventListener('scroll',onScroll,{passive:true});
  w.addEventListener('resize',onScroll);
  paint();

  /* --- bolum acilis animasyonu --- */
  var targets=[].slice.call(d.querySelectorAll('.reveal,.stagger'));
  if(root.classList.contains('js-motion')&&'IntersectionObserver' in w){
    var io=new IntersectionObserver(function(entries){
      for(var i=0;i<entries.length;i++){
        if(entries[i].isIntersecting){entries[i].target.classList.add('in');io.unobserve(entries[i].target);}
      }
    },{rootMargin:'0px 0px -6% 0px',threshold:0.06});
    for(var t=0;t<targets.length;t++){io.observe(targets[t]);}
  }else{
    root.classList.remove('js-motion');
  }

  /* --- yildiz alani (canvas) --- */
  var cv=d.querySelector('canvas.stars');
  if(!cv||reduce||!cv.getContext) return;
  var ctx=cv.getContext('2d');
  var dpr=Math.min(w.devicePixelRatio||1,2);
  var stars=[],W=0,H=0,raf=0,visible=!d.hidden,inView=true;
  function build(){
    var n=Math.round(W*H/11000); if(n<34)n=34; if(n>120)n=120;
    stars=[];
    for(var i=0;i<n;i++){
      stars.push({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.05+0.35,
        a:Math.random()*0.45+0.22,v:Math.random()*0.05+0.015,
        p:Math.random()*6.283,d:Math.random()*0.014+0.004,g:i%7===0});
    }
  }
  function size(){
    var r=cv.getBoundingClientRect(); W=r.width; H=r.height;
    if(W<=0||H<=0) return;
    cv.width=Math.round(W*dpr); cv.height=Math.round(H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0); build();
  }
  function frame(){
    raf=requestAnimationFrame(frame);
    ctx.clearRect(0,0,W,H);
    for(var i=0;i<stars.length;i++){
      var s=stars[i];
      s.p+=s.d; s.y-=s.v;
      if(s.y<-2){s.y=H+2;s.x=Math.random()*W;}
      var a=s.a+Math.sin(s.p)*0.2; if(a<0.05)a=0.05;
      ctx.globalAlpha=a;
      ctx.fillStyle=s.g?'#F5C96B':'#FBF8EF';
      ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,6.2832); ctx.fill();
    }
    ctx.globalAlpha=1;
  }
  function play(){ if(!raf&&visible&&inView){raf=requestAnimationFrame(frame);} }
  function stop(){ if(raf){cancelAnimationFrame(raf);raf=0;} }
  d.addEventListener('visibilitychange',function(){
    visible=!d.hidden; if(visible){play();}else{stop();}
  });
  if('IntersectionObserver' in w){
    new IntersectionObserver(function(e){
      inView=e[0].isIntersecting; if(inView){play();}else{stop();}
    },{threshold:0}).observe(cv);
  }
  var rt=0;
  w.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(size,180);});
  size(); play();
})();
"""

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Cinzel:wght@500;600&family=Cormorant+Garamond:wght@500;600;700&"
    'family=Inter:wght@400;500;600&display=swap">'
)


# --------------------------------------------------------------------------
# İçerik — yalnızca gerçekten var olan özellikler (app_en.arb / app_tr.arb).
# --------------------------------------------------------------------------

TEXTS: dict[str, dict] = {
    "en": {
        "dir": "ltr",
        "native": "English",
        "home_title": "Astrype — your chart, your readings, your guide",
        "home_desc": (
            "Astrype brings your natal chart, daily horoscope, tarot, coffee-cup, "
            "palm and face readings, dreams, numerology, Human Design and "
            "compatibility together with Lyra, an AI guide that remembers your "
            "readings. For entertainment and personal insight."
        ),
        "support_title": "Astrype — Support",
        "support_desc": "Help, contact, account deletion, subscriptions and frequently asked questions.",
        "nav_support": "Support",
        "nav_privacy": "Privacy",
        "nav_terms": "Terms",
        "langs_label": "Language",
        "hero_overline": "A mobile app for iOS and Android",
        "hero_h1_a": "Your sky, read",
        "hero_h1_b": "in your own words",
        "hero_lede": (
            "Astrype draws your birth chart in full, reads today's sky over it, and "
            "keeps every reading in one place. Lyra, your guide inside the app, "
            "remembers what you have already asked — so the next answer starts where "
            "the last one ended."
        ),
        "store_soon_title": "Coming soon",
        "store_soon_apple": "App Store",
        "store_soon_google": "Google Play",
        "store_live_top": "Download on the",
        "store_live_top_g": "Get it on",
        "store_note": (
            "Astrype has not been released yet. The App Store and Google Play links "
            "will appear here the day it goes live."
        ),
        "hero_shot_alt": (
            "Astrype home screen on a phone: 'Tonight's sky', a greeting, a wheel of "
            "zodiac glyphs and a free daily card called Today's Whisper."
        ),
        "f_title": "Everything in one app",
        "f_sub": (
            "Eleven ways to look at the same question. Each one is written for you, "
            "in plain language, and saved to your own archive."
        ),
        "features": [
            ("✺", "Birth Chart", "Your full natal wheel — planets, houses and aspects — with every placement explained in plain language instead of jargon."),
            ("✶", "Daily Horoscope", "Today's sky read over your own chart, not a generic sun-sign column. A short whisper each day, free."),
            ("✦", "Tarot", "A three-card spread read as one story: past, present and what is drawing near."),
            ("✷", "Coffee Reading", "Photograph the inside of your cup. The symbols are read and interpreted — the photo is deleted right after."),
            ("✸", "Palm Reading", "A reading of the lines of your dominant hand, from a single photo that is deleted after analysis."),
            ("◈", "Face Reading", "The old art of physiognomy, read from one front-facing photo that never leaves the analysis."),
            ("✹", "Dream Interpretation", "Tell a dream in your own words and see the symbols and themes inside it."),
            ("✴", "Numerology", "Your numbers — life path, expression and the patterns they repeat."),
            ("⬡", "Human Design", "Your type, strategy, authority and centres, calculated from your birth details."),
            ("❖", "Cosmic Match", "Two charts side by side: where the warmth is easy, where patience is needed, and what to actually talk about."),
            ("✧", "Lyra & Cosmic Memory", "An AI guide that already knows your chart and your past readings, so you never have to explain yourself twice."),
        ],
        "lyra_title": "Lyra remembers every reading",
        "lyra_body": [
            "Most apps hand you a paragraph and forget you. Lyra is different: your "
            "chart and the analyses you have already done are used as context, so a "
            "question about your career can be answered against the same Venus that "
            "came up in last week's tarot.",
            "Lyra speaks carefully on purpose. Nothing is presented as fixed fate, "
            "and Astrype does not give medical, legal, financial or safety advice — "
            "for those, please talk to a professional.",
        ],
        "lyra_alt": (
            "Astrype chat screen: Lyra explains that the chart and past readings are "
            "used as context, then answers a question about the day ahead."
        ),
        "privacy_title": "Your photos are not kept",
        "privacy_body": [
            "Coffee-cup, palm and face readings need a photo. That photo is sent to "
            "the analysis, and deleted from the server as soon as the analysis "
            "finishes. It is never stored, never shown to anyone, and never added to "
            "your archive.",
            "What is kept is the text: the list of symbols that were read and the "
            "interpretation written from them — in your account, visible only to you.",
        ],
        "privacy_points": [
            "Photos are deleted from the server immediately after analysis.",
            "Your birth details are used to calculate your chart and to personalise readings.",
            "You can delete your history and Cosmic Memory, or your whole account, from inside the app.",
            "Sign in with Apple, Google or email — or start as a guest and decide later.",
        ],
        "shots_title": "Inside the app",
        "shots": [
            ("en-1.jpg", "The natal chart screen: a full birth wheel with planets and aspect lines, and a written explanation of the Sun's placement."),
            ("en-4.jpg", "A three-card tarot spread — The Star, The Lovers, The Moon — with an interpretation underneath."),
            ("en-5.jpg", "A compatibility reading showing a match score, strengths, challenging areas and conversation tips."),
            ("en-3.jpg", "The chat screen where Lyra answers using the chart and earlier readings as context."),
        ],
        "plans_title": "Premium and Stardust",
        "plans_body": [
            "Today's Whisper is free every day. Deeper readings are unlocked with "
            "<strong>Stardust</strong>, the in-app credit: a Premium subscription "
            "includes Stardust on a regular cycle along with daily messages to Lyra, "
            "and extra Stardust packs can be bought on their own.",
            "Prices, renewal period and trial length are always shown in the app "
            "before you pay. Subscriptions renew automatically until you cancel them "
            "in your App Store or Google Play settings.",
        ],
        "disclaimer": (
            "Astrype's astrology, tarot and fortune-telling content is for "
            "entertainment and personal insight. It is not a substitute for "
            "professional medical, legal, financial or safety advice, and it does not "
            "predict the future."
        ),
        "foot_support": "Support",
        "foot_privacy": "Privacy Policy",
        "foot_terms": "Terms of Use",
        "foot_source": "Source code",
        "foot_contact": "Contact",
        # --- support page ---
        "sup_overline": "Support",
        "sup_h1_a": "We are here",
        "sup_h1_b": "when you need us",
        "sup_lede": (
            "Questions about a reading, your account, your data or a purchase — write "
            "to us and a person will answer."
        ),
        "sup_contact_title": "Contact us",
        "sup_contact_body": (
            "Email is the fastest way to reach us. We read every message and reply as "
            "soon as we can. If you are writing about a purchase or a technical "
            "problem, telling us your device and app version helps a lot."
        ),
        "sup_what_title": "What Astrype is",
        "sup_what_body": (
            "Astrype is a mobile app that brings your natal birth chart, a daily "
            "personalised horoscope, tarot, coffee-cup, palm and face readings, dream "
            "interpretation, numerology, Human Design and relationship compatibility "
            "together in one place — with Lyra, an AI guide whose Cosmic Memory "
            "remembers the readings you have already done."
        ),
        "sup_delete_title": "Deleting your account and your data",
        "sup_delete_body": "Both are done from inside the app, and neither needs to go through us:",
        "sup_delete_steps": [
            "<strong>Delete history and memory:</strong> Profile &rarr; My data &rarr; "
            "“Delete memory / history”. Your past analyses, chat records and "
            "Cosmic Memory summaries are permanently deleted. Your profile and birth "
            "details stay.",
            "<strong>Delete your account:</strong> Profile &rarr; Account &rarr; "
            "“Permanently delete account”. Your account and all of your data "
            "— profile, birth details, analyses, chats and subscription records "
            "— are irreversibly deleted. This cannot be undone.",
            "Deleting your account does <strong>not</strong> cancel an active App "
            "Store or Google Play subscription. Cancel it in your store's "
            "subscription settings as well.",
        ],
        "sup_subs_title": "Managing your subscription",
        "sup_subs_body": (
            "Purchases are handled by Apple and Google, so a subscription is started, "
            "changed and cancelled in your store account — not by us. Cancelling stops "
            "the next renewal; the current period runs to its end."
        ),
        "sup_subs_apple": "Manage on the App Store",
        "sup_subs_google": "Manage on Google Play",
        "sup_faq_title": "Frequently asked questions",
        "faq": [
            ("What is Stardust?",
             ["Stardust is the credit used inside Astrype to unlock a reading. A "
              "Premium subscription includes Stardust on a regular cycle together "
              "with daily messages to Lyra, and separate Stardust packs can be "
              "bought if you run out.",
              "Today's Whisper, the short daily reading, is free and does not cost "
              "Stardust."]),
            ("Is Astrype entertainment, or real prediction?",
             ["Entertainment and personal insight. Astrype does not predict the "
              "future and never presents anything as fixed fate; readings are meant "
              "as a mirror to think with. They are not a substitute for professional "
              "medical, legal, financial or safety advice."]),
            ("Are my coffee, palm and face photos stored?",
             ["No. The photo is used for the analysis and deleted from the server "
              "immediately afterwards. It is never kept, never shared and never added "
              "to your archive. Only the text result and the list of symbols that "
              "were read are saved to your account."]),
            ("How do I cancel my subscription?",
             ["In your store, not in the app: on iOS open App Store account "
              "&rarr; Subscriptions, on Android open Google Play &rarr; Payments and "
              "subscriptions &rarr; Subscriptions. Cancel at least 24 hours before the "
              "period ends to avoid the next renewal."]),
            ("How do I restore my purchases?",
             ["Open the Premium / Stardust screen in the app and tap "
              "“Restore”. Your purchases are restored to the store account "
              "they were made with, so make sure you are signed in to that same Apple "
              "ID or Google account."]),
            ("Which languages does Astrype speak?",
             ["The app is available in 20 languages, including English, Turkish, "
              "Azerbaijani, German, Spanish, French, Italian, Dutch, Polish, "
              "Portuguese, Russian, Ukrainian, Arabic, Persian, Urdu, Hindi, "
              "Indonesian, Japanese, Korean and Chinese. You can change it any time "
              "from Profile &rarr; Language.",
              "This website is in English and Turkish; the legal pages are available "
              "in all supported languages."]),
            ("Is my birth data private?",
             ["Your birth date, time and place are used to calculate your chart and "
              "to personalise your readings, and they are stored in your own account "
              "where only you can reach them. You can delete them together with your "
              "account at any time. The details are in the Privacy Policy."]),
            ("What if I don't know my exact birth time?",
             ["You can still use Astrype. Where the birth time matters, the app says "
              "so plainly — the rising sign may not be calculated, compatibility "
              "becomes approximate and the Human Design type may shift — but "
              "everything that does not depend on the exact minute still works."]),
        ],
        "sup_back": "Back to the home page",
    },
    "tr": {
        "dir": "ltr",
        "native": "Türkçe",
        "home_title": "Astrype — haritan, yorumların, rehberin",
        "home_desc": (
            "Astrype; doğum haritanı, günlük burcunu, tarotu, kahve, el ve yüz falını, "
            "rüya yorumunu, numerolojiyi, İnsan Tasarımı'nı ve uyum analizini, "
            "okuduklarını hatırlayan yapay zekâ rehberi Lyra ile bir araya getirir. "
            "Eğlence ve kişisel içgörü amaçlıdır."
        ),
        "support_title": "Astrype — Destek",
        "support_desc": "Yardım, iletişim, hesap silme, abonelikler ve sık sorulan sorular.",
        "nav_support": "Destek",
        "nav_privacy": "Gizlilik",
        "nav_terms": "Şartlar",
        "langs_label": "Dil",
        "hero_overline": "iOS ve Android için mobil uygulama",
        "hero_h1_a": "Gökyüzün,",
        "hero_h1_b": "senin dilinle",
        "hero_lede": (
            "Astrype doğum haritanı bütünüyle çizer, bugünün göğünü o haritanın "
            "üzerinden okur ve bütün analizlerini tek yerde tutar. Uygulamanın "
            "içindeki rehberin Lyra, daha önce ne sorduğunu hatırlar — yeni cevap, "
            "bir öncekinin bittiği yerden başlar."
        ),
        "store_soon_title": "Yakında",
        "store_soon_apple": "App Store",
        "store_soon_google": "Google Play",
        "store_live_top": "İndir:",
        "store_live_top_g": "İndir:",
        "store_note": (
            "Astrype henüz yayında değil. App Store ve Google Play bağlantıları "
            "yayına çıktığı gün burada olacak."
        ),
        "hero_shot_alt": (
            "Telefonda Astrype ana ekranı: 'Bu gecenin göğü' başlığı, karşılama, burç "
            "sembollerinden oluşan çember ve ücretsiz günlük kart 'Bugünün Fısıltısı'."
        ),
        "f_title": "Hepsi tek uygulamada",
        "f_sub": (
            "Aynı soruya bakmanın on bir yolu. Her biri sana göre yazılır, sade bir "
            "dille anlatılır ve kendi arşivine kaydedilir."
        ),
        "features": [
            ("✺", "Doğum Haritası", "Gezegenler, evler ve açılarla tam doğum çemberin — her yerleşim jargon yerine sade bir dille açıklanır."),
            ("✶", "Günlük Burç", "Genel burç yazısı değil: bugünün göğü senin haritanın üzerinden okunur. Her gün kısa bir fısıltı, ücretsiz."),
            ("✦", "Tarot", "Üç kartlık açılım tek bir hikâye olarak okunur: geçmiş, şimdi ve yaklaşan."),
            ("✷", "Kahve Falı", "Fincanın içini fotoğrafla. Semboller okunur ve yorumlanır — fotoğraf hemen ardından silinir."),
            ("✸", "El Falı", "Baskın elinin çizgileri tek bir fotoğraftan okunur; fotoğraf analiz biter bitmez silinir."),
            ("◈", "Yüz Falı", "Sima ilminin eski geleneği, analizden öteye geçmeyen tek bir önden fotoğrafla."),
            ("✹", "Rüya Yorumu", "Rüyanı kendi cümlelerinle anlat; içindeki sembolleri ve temaları gör."),
            ("✴", "Numeroloji", "Sayıların — yaşam yolu, ifade sayısı ve tekrar eden örüntüler."),
            ("⬡", "İnsan Tasarımı", "Doğum bilgilerinden hesaplanan tipin, stratejin, otoriten ve merkezlerin."),
            ("❖", "Kozmik Uyum", "İki harita yan yana: neresi kolay ısınıyor, neresi sabır istiyor ve asıl neyi konuşmak gerekiyor."),
            ("✧", "Lyra ve Kozmik Hafıza", "Haritanı ve geçmiş analizlerini zaten bilen bir yapay zekâ rehber — kendini iki kez anlatman gerekmez."),
        ],
        "lyra_title": "Lyra her analizi hatırlar",
        "lyra_body": [
            "Çoğu uygulama sana bir paragraf verir ve seni unutur. Lyra öyle değil: "
            "haritan ve daha önce yaptığın analizler bağlam olarak kullanılır; "
            "kariyer sorusuna, geçen haftaki tarotta çıkan aynı Venüs üzerinden cevap "
            "verilebilir.",
            "Lyra bilerek temkinli konuşur. Hiçbir şey kesin kader gibi sunulmaz; "
            "Astrype tıbbi, hukuki, finansal veya güvenlikle ilgili tavsiye vermez — "
            "bunlar için lütfen bir uzmana danış.",
        ],
        "lyra_alt": (
            "Astrype sohbet ekranı: Lyra, haritanın ve geçmiş analizlerin bağlam "
            "olarak kullanıldığını söyleyip günle ilgili bir soruyu yanıtlıyor."
        ),
        "privacy_title": "Fotoğrafların saklanmaz",
        "privacy_body": [
            "Kahve, el ve yüz falı bir fotoğraf ister. O fotoğraf analize gönderilir "
            "ve analiz biter bitmez sunucudan silinir. Hiçbir zaman saklanmaz, "
            "kimseye gösterilmez ve arşivine eklenmez.",
            "Saklanan şey metindir: okunan sembollerin listesi ve onlardan yazılan "
            "yorum — hesabında, yalnızca senin görebileceğin şekilde.",
        ],
        "privacy_points": [
            "Fotoğraflar analizden hemen sonra sunucudan silinir.",
            "Doğum bilgilerin haritanı hesaplamak ve yorumları kişiselleştirmek için kullanılır.",
            "Geçmişini ve Kozmik Hafızanı ya da hesabının tamamını uygulama içinden silebilirsin.",
            "Apple, Google veya e-posta ile giriş yap — ya da misafir olarak başla, sonra karar ver.",
        ],
        "shots_title": "Uygulamanın içinden",
        "shots": [
            ("tr-1.jpg", "Doğum haritası ekranı: gezegenler ve açı çizgileriyle tam doğum çemberi, altında Güneş yerleşiminin yazılı açıklaması."),
            ("tr-4.jpg", "Üç kartlık tarot açılımı ve altında yorumu."),
            ("tr-5.jpg", "Uyum analizi: uyum puanı, güçlü yanlar, zorlayıcı alanlar ve konuşma önerileri."),
            ("tr-3.jpg", "Sohbet ekranı: Lyra, haritayı ve önceki analizleri bağlam alarak yanıt veriyor."),
        ],
        "plans_title": "Premium ve Yıldız Tozu",
        "plans_body": [
            "Bugünün Fısıltısı her gün ücretsizdir. Derin analizler uygulama içi kredi "
            "olan <strong>Yıldız Tozu</strong> ile açılır: Premium abonelik, Lyra'ya "
            "günlük mesaj hakkıyla birlikte düzenli olarak Yıldız Tozu içerir; "
            "ayrıca tek başına Yıldız Tozu paketleri de alınabilir.",
            "Fiyat, yenilenme dönemi ve deneme süresi ödemeden önce uygulamada her "
            "zaman gösterilir. Abonelikler, App Store veya Google Play ayarlarından "
            "iptal edilmedikçe otomatik yenilenir.",
        ],
        "disclaimer": (
            "Astrype'ın astroloji, tarot ve fal içerikleri eğlence ve kişisel içgörü "
            "amaçlıdır. Profesyonel tıbbi, hukuki, finansal veya güvenlik tavsiyesinin "
            "yerine geçmez ve geleceği önceden bildirmez."
        ),
        "foot_support": "Destek",
        "foot_privacy": "Gizlilik Politikası",
        "foot_terms": "Kullanım Şartları",
        "foot_source": "Kaynak kod",
        "foot_contact": "İletişim",
        # --- destek sayfası ---
        "sup_overline": "Destek",
        "sup_h1_a": "İhtiyacın olduğunda",
        "sup_h1_b": "buradayız",
        "sup_lede": (
            "Bir yorumla, hesabınla, verilerinle ya da satın almanla ilgili soruların "
            "için yaz — cevabı bir insan yazacak."
        ),
        "sup_contact_title": "Bize ulaş",
        "sup_contact_body": (
            "Bize ulaşmanın en hızlı yolu e-posta. Her mesajı okuyor ve "
            "elimizden geldiğince çabuk yanıtlıyoruz. Bir satın alma ya da teknik bir "
            "sorun için yazıyorsan cihazını ve uygulama sürümünü belirtmen çok "
            "yardımcı olur."
        ),
        "sup_what_title": "Astrype nedir?",
        "sup_what_body": (
            "Astrype; doğum haritanı, günlük kişisel burç yorumunu, tarotu, kahve, el "
            "ve yüz falını, rüya yorumunu, numerolojiyi, İnsan Tasarımı'nı ve ilişki "
            "uyumunu tek yerde toplayan bir mobil uygulamadır — yanında, Kozmik "
            "Hafızası sayesinde daha önce yaptığın analizleri hatırlayan yapay zekâ "
            "rehberi Lyra ile."
        ),
        "sup_delete_title": "Hesabını ve verilerini silme",
        "sup_delete_body": "İkisi de uygulama içinden yapılır, bizden geçmesi gerekmez:",
        "sup_delete_steps": [
            "<strong>Geçmişi ve hafızayı sil:</strong> Profil &rarr; Verilerim &rarr; "
            "“Hafızayı / geçmişi sil”. Geçmiş analizlerin, sohbet kayıtların "
            "ve Kozmik Hafıza özetlerin kalıcı olarak silinir. Profilin ve doğum "
            "bilgilerin kalır.",
            "<strong>Hesabını sil:</strong> Profil &rarr; Hesap &rarr; “Hesabı "
            "kalıcı olarak sil”. Hesabın ve tüm verilerin — profil, doğum "
            "bilgileri, analizler, sohbetler ve abonelik kayıtları — geri "
            "alınamaz biçimde silinir.",
            "Hesabını silmek, aktif bir App Store veya Google Play aboneliğini "
            "<strong>iptal etmez</strong>. Aboneliği ayrıca mağazanın abonelik "
            "ayarlarından iptal etmelisin.",
        ],
        "sup_subs_title": "Aboneliğini yönetme",
        "sup_subs_body": (
            "Satın almaları Apple ve Google yürütür; abonelik mağaza hesabından "
            "başlatılır, değiştirilir ve iptal edilir — bizden değil. İptal, bir "
            "sonraki yenilemeyi durdurur; içinde bulunduğun dönem sonuna kadar devam "
            "eder."
        ),
        "sup_subs_apple": "App Store'dan yönet",
        "sup_subs_google": "Google Play'den yönet",
        "sup_faq_title": "Sık sorulan sorular",
        "faq": [
            ("Yıldız Tozu nedir?",
             ["Yıldız Tozu, Astrype içinde bir analizi açmak için kullanılan kredidir. "
              "Premium abonelik, Lyra'ya günlük mesaj hakkıyla birlikte düzenli olarak "
              "Yıldız Tozu içerir; bittiğinde ayrıca Yıldız Tozu paketi alınabilir.",
              "Kısa günlük yorum olan Bugünün Fısıltısı ücretsizdir ve Yıldız Tozu "
              "harcamaz."]),
            ("Astrype eğlence mi, gerçek kehanet mi?",
             ["Eğlence ve kişisel içgörü. Astrype geleceği önceden bildirmez ve hiçbir "
              "şeyi kesin kader gibi sunmaz; yorumlar üzerine düşünülecek bir ayna "
              "olarak yazılır. Profesyonel tıbbi, hukuki, finansal veya güvenlik "
              "tavsiyesinin yerine geçmez."]),
            ("Kahve, el ve yüz falı fotoğraflarım saklanıyor mu?",
             ["Hayır. Fotoğraf yalnızca analiz için kullanılır ve hemen ardından "
              "sunucudan silinir. Saklanmaz, paylaşılmaz ve arşivine eklenmez. "
              "Hesabına yalnızca metin sonucu ve okunan sembollerin listesi kaydedilir."]),
            ("Aboneliğimi nasıl iptal ederim?",
             ["Uygulamadan değil, mağazadan: iOS'ta App Store hesabı &rarr; "
              "Abonelikler, Android'de Google Play &rarr; Ödemeler ve abonelikler "
              "&rarr; Abonelikler. Bir sonraki yenilemeyi önlemek için dönem "
              "bitiminden en az 24 saat önce iptal et."]),
            ("Satın almalarımı nasıl geri yüklerim?",
             ["Uygulamada Premium / Yıldız Tozu ekranını aç ve “Geri "
              "yükle” ye dokun. Satın almalar, yapıldıkları mağaza hesabına geri "
              "yüklenir; aynı Apple ID veya Google hesabıyla giriş yaptığından emin ol."]),
            ("Astrype hangi dilleri konuşuyor?",
             ["Uygulama 20 dilde: Türkçe, İngilizce, Azerbaycanca, Almanca, "
              "İspanyolca, Fransızca, İtalyanca, Felemenkçe, Lehçe, Portekizce, "
              "Rusça, Ukraynaca, Arapça, Farsça, Urduca, Hintçe, Endonezce, Japonca, "
              "Korece ve Çince. Profil &rarr; Dil'den istediğin zaman "
              "değiştirebilirsin.",
              "Bu web sitesi Türkçe ve İngilizce; yasal sayfalar desteklenen tüm "
              "dillerde mevcut."]),
            ("Doğum verilerim gizli mi?",
             ["Doğum tarihin, saatin ve yerin haritanı hesaplamak ve yorumlarını "
              "kişiselleştirmek için kullanılır ve yalnızca senin erişebildiğin kendi "
              "hesabında saklanır. İstediğin zaman hesabınla birlikte silebilirsin. "
              "Ayrıntılar Gizlilik Politikası'nda."]),
            ("Doğum saatimi tam bilmiyorsam ne olur?",
             ["Astrype'ı yine kullanabilirsin. Doğum saatinin önemli olduğu yerlerde "
              "uygulama bunu açıkça söyler — yükselen hesaplanamayabilir, uyum "
              "yaklaşık olur, İnsan Tasarımı tipi değişebilir — ama dakikaya "
              "bağlı olmayan her şey çalışır."]),
        ],
        "sup_back": "Ana sayfaya dön",
    },
}


# --- 2026 sunum revizyonunun ek metinleri (içerik değil, çerçeve) ---------

TEXTS["en"].update({
    "skip": "Skip to content",
    "nav_label": "Main",
    "nav_features": "Features",
    "nav_screens": "Screens",
    "cta": "Get the app",
    "cta_short": "Get app",
    "lang_code": "EN",
    "hero_points": [
        "<b>Free</b> daily whisper",
        "<b>20</b> languages",
        "Photos <b>deleted</b> after analysis",
    ],
    "badge_apple": "Download on the App Store",
    "badge_google": "Get it on Google Play",
    "ey_features": "The modules",
    "ey_lyra": "Cosmic Memory",
    "ey_privacy": "Privacy",
    "ey_shots": "Inside",
    "ey_plans": "Premium",
    "ey_get": "Download",
    "get_title": "Coming to iOS and Android",
    "foot_tagline": "Your chart, your readings and your guide — in one app.",
    "foot_col_product": "Product",
    "foot_col_legal": "Legal",
    "ey_sup_contact": "Contact",
    "ey_sup_about": "About",
    "ey_sup_delete": "Your data",
    "ey_sup_subs": "Billing",
    "ey_sup_faq": "Questions",
})

TEXTS["tr"].update({
    "skip": "İçeriğe geç",
    "nav_label": "Ana menü",
    "nav_features": "Özellikler",
    "nav_screens": "Ekranlar",
    "cta": "Uygulamayı al",
    "cta_short": "İndir",
    "lang_code": "TR",
    "hero_points": [
        "<b>Ücretsiz</b> günlük fısıltı",
        "<b>20</b> dil",
        "Fotoğraflar analizden sonra <b>silinir</b>",
    ],
    "badge_apple": "Download on the App Store",
    "badge_google": "Get it on Google Play",
    "ey_features": "Modüller",
    "ey_lyra": "Kozmik Hafıza",
    "ey_privacy": "Gizlilik",
    "ey_shots": "İçeriden",
    "ey_plans": "Premium",
    "ey_get": "İndir",
    "get_title": "iOS ve Android'e geliyor",
    "foot_tagline": "Haritan, yorumların ve rehberin — tek uygulamada.",
    "foot_col_product": "Uygulama",
    "foot_col_legal": "Yasal",
    "ey_sup_contact": "İletişim",
    "ey_sup_about": "Hakkında",
    "ey_sup_delete": "Verilerin",
    "ey_sup_subs": "Ödeme",
    "ey_sup_faq": "Sorular",
})


# --------------------------------------------------------------------------
# Yapı taşları
# --------------------------------------------------------------------------


def _head(title: str, description: str, lang: str, canonical_path: str) -> str:
    t = TEXTS[lang]
    return f"""<!doctype html><html lang="{lang}" dir="{t["dir"]}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#0A0813">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:image" content="/static/img/icon.png">
<link rel="icon" href="/static/img/icon.png" type="image/png">
<link rel="apple-touch-icon" href="/static/img/icon.png">
<link rel="canonical" href="https://astrype.com{canonical_path}">
<link rel="alternate" hreflang="en" href="https://astrype.com{canonical_path}?lang=en">
<link rel="alternate" hreflang="tr" href="https://astrype.com{canonical_path}?lang=tr">
{_FONTS}
<style>{_STYLE}</style>
{_HEAD_SCRIPT}
</head>
<body>"""


def _header(lang: str, page: str) -> str:
    t = TEXTS[lang]
    other = "tr" if lang == "en" else "en"
    path = "/support" if page == "support" else "/"
    sup_cur = ' aria-current="page"' if page == "support" else ""
    home = f"/?lang={lang}"
    anchor = "" if page == "home" else home
    return f"""<a class="skip" href="#main">{t["skip"]}</a>
<header class="site at-top"><div class="wrap bar">
<a class="brand" href="{home}" aria-label="Astrype">{_brand_mark("hm", 34)}<span class="wm">Astrype</span></a>
<nav class="nav" aria-label="{t["nav_label"]}">
<a class="sec" href="{anchor}#features">{t["nav_features"]}</a>
<a class="sec" href="{anchor}#screens">{t["nav_screens"]}</a>
<a href="/support?lang={lang}"{sup_cur}>{t["nav_support"]}</a>
</nav>
<div class="tools">
<div class="langsw" role="group" aria-label="{t["langs_label"]}">
<a href="{path}?lang={lang}" lang="{lang}" hreflang="{lang}" aria-current="true">{TEXTS[lang]["lang_code"]}</a>
<a href="{path}?lang={other}" lang="{other}" hreflang="{other}">{TEXTS[other]["lang_code"]}</a>
</div>
<a class="btn btn-gold" href="{anchor}#get"><span class="full">{t["cta"]}</span><span class="short">{t["cta_short"]}</span></a>
</div>
</div></header>"""


def _stores(lang: str) -> str:
    """Yayına çıkınca APP_STORE_URL / PLAY_STORE_URL doldurulur; gerisi otomatik:
    rozetler gri "yakında" durumundan çıkıp gerçek bağlantıya dönüşür."""
    t = TEXTS[lang]
    soon = t["store_soon_title"]
    live = bool(APP_STORE_URL and PLAY_STORE_URL)

    def wrap(url: str, art: str, extra: str = "") -> str:
        if url:
            return f'<li><a class="store{extra}" href="{url}" rel="noopener">{art}</a></li>'
        return f'<li><span class="store{extra} store--soon" aria-disabled="true">{art}</span></li>'

    apple_label = t["badge_apple"] if APP_STORE_URL else f'{t["badge_apple"]} — {soon}'
    google_label = t["badge_google"] if PLAY_STORE_URL else f'{t["badge_google"]} — {soon}'
    google_art = (
        f'<img class="badge-art" src="{PLAY_BADGE_IMG}" alt="{google_label}" '
        'width="200" height="77" loading="lazy" decoding="async">'
    )
    pill = (
        ""
        if live
        else f'<p class="soonpill"><span aria-hidden="true">✦</span> {soon}</p>'
    )
    note = "" if live else f'<p class="storenote">{t["store_note"]}</p>'
    return (
        f'<div class="getbox">{pill}<ul class="stores">'
        f'{wrap(APP_STORE_URL, _apple_badge_svg(apple_label), " store--apple")}'
        f'{wrap(PLAY_STORE_URL, google_art)}'
        f"</ul>{note}</div>"
    )


def _footer(lang: str) -> str:
    t = TEXTS[lang]
    other = "tr" if lang == "en" else "en"
    return f"""<footer class="site"><div class="wrap">
<div class="footgrid">
<div class="footbrand">
<a class="brand" href="/?lang={lang}" aria-label="Astrype">{_brand_mark("fm", 32)}<span class="wm">Astrype</span></a>
<p class="foottag">{t["foot_tagline"]}</p>
</div>
<div class="footcol">
<h4>{t["foot_col_product"]}</h4>
<ul>
<li><a href="/?lang={lang}#features">{t["nav_features"]}</a></li>
<li><a href="/?lang={lang}#screens">{t["nav_screens"]}</a></li>
<li><a href="/?lang={lang}#get">{t["cta"]}</a></li>
<li><a href="/support?lang={lang}">{t["foot_support"]}</a></li>
</ul>
</div>
<div class="footcol">
<h4>{t["foot_col_legal"]}</h4>
<ul>
<li><a href="/legal/privacy?lang={lang}">{t["foot_privacy"]}</a></li>
<li><a href="/legal/terms?lang={lang}">{t["foot_terms"]}</a></li>
<li><a href="/legal/source">{t["foot_source"]}</a></li>
<li>{t["foot_contact"]}: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
</ul>
</div>
</div>
<div class="footbottom">
<div class="langsw" role="group" aria-label="{t["langs_label"]}">
<a href="/?lang={lang}" lang="{lang}" hreflang="{lang}" aria-current="true">{TEXTS[lang]["native"]}</a>
<a href="/?lang={other}" lang="{other}" hreflang="{other}">{TEXTS[other]["native"]}</a>
</div>
<p class="disclaimer">{t["disclaimer"]}</p>
<p class="copy">&copy; Astrype</p>
</div>
</div></footer>
<script>{_SCRIPT}</script>
</body></html>"""


# --------------------------------------------------------------------------
# Sayfalar
# --------------------------------------------------------------------------


def render_home(lang: str) -> str:
    t = TEXTS[lang]
    hero_shot = f"{lang}-2.jpg"
    lyra_shot = f"{lang}-3.jpg"

    cards = "\n".join(
        f'<article class="card"><div class="glyph" aria-hidden="true">{glyph}</div>'
        f"<h3>{name}</h3><p>{body}</p></article>"
        for glyph, name, body in t["features"]
    )
    shots = "\n".join(
        f'<figure data-parallax="10"><div class="frame">'
        f'<img src="/static/img/{src}" alt="{alt}" width="600" height="1300" '
        'loading="lazy" decoding="async"></div>'
        f"<figcaption>{alt}</figcaption></figure>"
        for src, alt in t["shots"]
    )
    points = "".join(f"<li>{p}</li>" for p in t["hero_points"])
    lyra = "\n".join(f"<p>{p}</p>" for p in t["lyra_body"])
    priv = "\n".join(f"<p>{p}</p>" for p in t["privacy_body"])
    privpoints = "\n".join(f"<li>{p}</li>" for p in t["privacy_points"])
    plans = "\n".join(f"<p>{p}</p>" for p in t["plans_body"])

    return f"""{_head(t["home_title"], t["home_desc"], lang, "/")}
{_header(lang, "home")}
<main id="main">
<div class="hero">
<canvas class="stars" aria-hidden="true"></canvas>
<div class="wrap"><div class="hero-grid">
<div class="hero-copy">
<p class="overline">{t["hero_overline"]}</p>
<h1>{t["hero_h1_a"]}<br><em>{t["hero_h1_b"]}</em></h1>
<p class="lede">{t["hero_lede"]}</p>
<ul class="herolist">{points}</ul>
{_stores(lang)}
</div>
<div class="hero-art">
{_zodiac_wheel()}
<div class="device" data-parallax="18">
<img src="/static/img/{hero_shot}" alt="{t["hero_shot_alt"]}" width="600" height="1300" fetchpriority="high">
</div>
</div>
</div></div></div>

<section id="features" class="alt"><div class="wrap">
<div class="reveal">
<p class="eyebrow">{t["ey_features"]}</p>
<h2>{t["f_title"]}</h2>
<p class="sub">{t["f_sub"]}</p>
</div>
<div class="cards stagger">
{cards}
</div>
</div></section>

<section id="lyra"><div class="wrap"><div class="split reveal">
<div>
<p class="eyebrow">{t["ey_lyra"]}</p>
<h2>{t["lyra_title"]}</h2>
{lyra}
</div>
<div class="shot">
<div class="device" data-parallax="14">
<img src="/static/img/{lyra_shot}" alt="{t["lyra_alt"]}" width="600" height="1300" loading="lazy" decoding="async">
</div>
</div>
</div></div></section>

<section id="privacy" class="alt"><div class="wrap narrow">
<div class="panel reveal">
<p class="eyebrow">{t["ey_privacy"]}</p>
<h2>{t["privacy_title"]}</h2>
{priv}
<ul class="plain" style="margin-top:22px">
{privpoints}
</ul>
</div>
</div></section>

<section id="screens"><div class="wrap">
<div class="reveal">
<p class="eyebrow">{t["ey_shots"]}</p>
<h2>{t["shots_title"]}</h2>
</div>
<div class="shots stagger">
{shots}
</div>
</div></section>

<section id="plans" class="alt"><div class="wrap narrow">
<div class="reveal">
<p class="eyebrow">{t["ey_plans"]}</p>
<h2>{t["plans_title"]}</h2>
{plans}
<p class="note" style="margin-top:22px">{t["disclaimer"]}</p>
</div>
</div></section>

<section id="get"><div class="wrap narrow">
<div class="panel reveal">
<p class="eyebrow">{t["ey_get"]}</p>
<h2>{t["get_title"]}</h2>
{_stores(lang)}
</div>
</div></section>
</main>
{_footer(lang)}"""


def render_support(lang: str) -> str:
    t = TEXTS[lang]
    steps = "\n".join(f"<li>{s}</li>" for s in t["sup_delete_steps"])
    faq = "\n".join(
        '<details><summary>{q}</summary><div class="answer">{a}</div></details>'.format(
            q=q, a="".join(f"<p>{p}</p>" for p in answers)
        )
        for q, answers in t["faq"]
    )
    return f"""{_head(t["support_title"], t["support_desc"], lang, "/support")}
{_header(lang, "support")}
<main id="main">
<div class="hero">
<canvas class="stars" aria-hidden="true"></canvas>
<div class="wrap narrow">
<p class="overline">{t["sup_overline"]}</p>
<h1>{t["sup_h1_a"]}<br><em>{t["sup_h1_b"]}</em></h1>
<p class="lede">{t["sup_lede"]}</p>
</div></div>

<section id="contact"><div class="wrap narrow">
<div class="reveal">
<p class="eyebrow">{t["ey_sup_contact"]}</p>
<h2>{t["sup_contact_title"]}</h2>
<p>{t["sup_contact_body"]}</p>
<div class="contactbox" style="margin-top:22px">
<a class="mail" href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
</div>
</div>
</div></section>

<section id="about" class="alt"><div class="wrap narrow">
<div class="reveal">
<p class="eyebrow">{t["ey_sup_about"]}</p>
<h2>{t["sup_what_title"]}</h2>
<p>{t["sup_what_body"]}</p>
<p class="note" style="margin-top:22px">{t["disclaimer"]}</p>
</div>
</div></section>

<section id="delete"><div class="wrap narrow">
<div class="reveal">
<p class="eyebrow">{t["ey_sup_delete"]}</p>
<h2>{t["sup_delete_title"]}</h2>
<p>{t["sup_delete_body"]}</p>
<ul class="plain" style="margin-top:20px">
{steps}
</ul>
</div>
</div></section>

<section id="subscriptions" class="alt"><div class="wrap narrow">
<div class="reveal">
<p class="eyebrow">{t["ey_sup_subs"]}</p>
<h2>{t["sup_subs_title"]}</h2>
<p>{t["sup_subs_body"]}</p>
<ul class="plain" style="margin-top:20px">
<li><a href="{APPLE_SUBSCRIPTIONS_URL}" rel="noopener">{t["sup_subs_apple"]}</a></li>
<li><a href="{GOOGLE_SUBSCRIPTIONS_URL}" rel="noopener">{t["sup_subs_google"]}</a></li>
</ul>
</div>
</div></section>

<section id="faq"><div class="wrap narrow">
<div class="reveal">
<p class="eyebrow">{t["ey_sup_faq"]}</p>
<h2>{t["sup_faq_title"]}</h2>
{faq}
<p style="margin-top:28px"><a href="/?lang={lang}">&larr; {t["sup_back"]}</a></p>
</div>
</div></section>
</main>
{_footer(lang)}"""


# İçerik statik — açılışta bir kez üretilir.
_PAGES: dict[tuple[str, str], str] = {
    ("home", code): render_home(code) for code in SITE_LANGS
}
_PAGES.update({("support", code): render_support(code) for code in SITE_LANGS})


def resolve_site_lang(query_lang: str | None, accept_language: str | None) -> str:
    """Yasal sayfalarla aynı çözümleme; site yalnızca tr/en olduğu için
    diğer tüm diller İngilizce'ye düşer."""
    code = resolve_lang(query_lang, accept_language)
    return code if code in SITE_LANGS else SITE_DEFAULT_LANG


def _respond(kind: str, lang: str | None, accept_language: str | None) -> HTMLResponse:
    code = resolve_site_lang(lang, accept_language)
    return HTMLResponse(
        _PAGES[(kind, code)],
        headers={"Content-Language": code, "Vary": "Accept-Language"},
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing(
    lang: str | None = Query(None),
    accept_language: str | None = Header(None),
) -> HTMLResponse:
    return _respond("home", lang, accept_language)


@router.get("/support", response_class=HTMLResponse, include_in_schema=False)
async def support(
    lang: str | None = Query(None),
    accept_language: str | None = Header(None),
) -> HTMLResponse:
    return _respond("support", lang, accept_language)

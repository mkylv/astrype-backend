"""Yasal sayfalar — Gizlilik Politikası + Kullanım Şartları (herkese açık HTML).

App Store / Google Play listeleme için kalıcı, kimlik doğrulaması gerektirmeyen
URL'ler sunar: /legal/privacy, /legal/terms, /legal/source. Uygulama içinden de aynı URL'ler
açılır. İçerik eğlence/kişisel içgörü disclaimer'ını (Bölüm 16) içerir.

Çok dilli: ?lang=xx → Accept-Language → İngilizce. Metinler app/legal_texts/<lang>.py
içindedir; Türkçe (tr.py) kaynak metindir ve çelişki halinde geçerlidir — diğer
diller kolaylık amaçlı çevirilerdir. ar/fa/ur sayfaları dir="rtl" ile sunulur.

AGPL-3.0 §13: Swiss Ephemeris (pyswisseph/Kerykeion) AGPL olduğundan ağ üzerinden
hizmet alan kullanıcılara backend kaynak kodu sunulur — şartlar sayfasındaki
"Açık kaynak" bölümü ve /legal/source yönlendirmesi bu yükümlülüğü karşılar.
"""
from __future__ import annotations

from fastapi import APIRouter, Header, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.legal_texts import DEFAULT_LANG, RTL_LANGS, SOURCE_LANG, SUPPORTED_LANGS, TEXTS

router = APIRouter(tags=["legal"])

# İletişim — yayın öncesi gerçek destek adresiyle doğrulanmalı.
# (Güncelleme tarihi her dil modülünde yerelleştirilmiş olarak tutulur.)
_CONTACT = "destek@astrype.com"

# Backend kaynak kodu (AGPL-3.0 §13). Repo taşınırsa yalnızca burası değişir;
# uygulama ve dış bağlantılar kalıcı /legal/source adresini kullanabilir.
_SOURCE_URL = "https://github.com/mkylv/astrype-backend"
_LICENSE_NAME = "GNU Affero General Public License v3.0 (AGPL-3.0)"

_PLACEHOLDERS = {
    "{contact_link}": f'<a href="mailto:{_CONTACT}">{_CONTACT}</a>',
    "{source_link}": f'<a href="{_SOURCE_URL}">{_SOURCE_URL}</a>',
    "{source_path_link}": '<a href="/legal/source">/legal/source</a>',
    "{license}": _LICENSE_NAME,
}

_STYLE = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0A0813;color:#ECE6F4;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  line-height:1.65;padding:32px 20px 64px}
.wrap{max-width:720px;margin:0 auto}
.langs{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:12px;margin-bottom:24px;
  padding-bottom:12px;border-bottom:1px solid #241c46}
.langs a{color:#9C92BA;text-decoration:none}
.langs a[aria-current]{color:#F5C96B;font-weight:600}
h1{font-family:Georgia,'Times New Roman',serif;color:#F5C96B;font-size:28px;
  letter-spacing:.02em;margin:0 0 4px}
.upd{color:#9C92BA;font-size:13px;margin-bottom:28px}
.tn{color:#9C92BA;font-size:13px;font-style:italic;margin:-16px 0 24px}
h2{color:#E3B864;font-size:18px;margin:28px 0 8px}
p,li{color:#CFC7DE;font-size:15px}
a{color:#F5C96B}
.note{background:#181233;border:1px solid #3A2D6B;border-radius:12px;
  padding:14px 16px;margin:24px 0;color:#ECE6F4;font-size:14px}
footer{color:#6f6790;font-size:12px;margin-top:40px;border-top:1px solid #241c46;padding-top:16px}
"""


def _fill(text: str) -> str:
    for token, value in _PLACEHOLDERS.items():
        text = text.replace(token, value)
    return text


def _lang_switcher(current: str, label: str) -> str:
    links = []
    for code in SUPPORTED_LANGS:
        cur = ' aria-current="true"' if code == current else ""
        links.append(
            f'<a href="?lang={code}" lang="{code}" hreflang="{code}"{cur}>'
            f"<bdi>{TEXTS[code]['native_name']}</bdi></a>"
        )
    return f'<nav class="langs" aria-label="{label}">{"".join(links)}</nav>'


def render_page(kind: str, lang: str) -> str:
    """kind: 'privacy' | 'terms'. Tek şablon, dil verisi app/legal_texts/<lang>.py."""
    t = TEXTS[lang]
    page = t[kind]
    direction = "rtl" if lang in RTL_LANGS else "ltr"
    sections = []
    for i, (heading, paragraphs) in enumerate(page["sections"], start=1):
        body = "\n".join(f"<p>{_fill(p)}</p>" for p in paragraphs)
        sections.append(f"<h2>{i}. {heading}</h2>\n{body}")
    notice = (
        f'<p class="tn">{t["translation_notice"]}</p>'
        if lang != SOURCE_LANG and t["translation_notice"]
        else ""
    )
    return f"""<!doctype html><html lang="{lang}" dir="{direction}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Astrype — {page["title"]}</title><style>{_STYLE}</style></head>
<body><div class="wrap">{_lang_switcher(lang, t["languages_label"])}
<h1>{page["title"]}</h1>
<div class="upd">{t["updated_label"]}: {t["updated"]}</div>
{notice}
<div class="note">{_fill(page["note"])}</div>
{chr(10).join(sections)}
<footer>Astrype · {t["contact_label"]}: {_PLACEHOLDERS["{contact_link}"]}</footer>
</div></body></html>"""


# Tüm dil × sayfa kombinasyonları açılışta bir kez üretilir (statik içerik).
_PAGES: dict[tuple[str, str], str] = {
    (kind, code): render_page(kind, code)
    for kind in ("privacy", "terms")
    for code in SUPPORTED_LANGS
}


def _normalize(tag: str | None) -> str | None:
    """'pt-BR' / 'zh_Hans' / 'EN' -> birincil alt etiket; desteklenmiyorsa None."""
    if not tag:
        return None
    primary = tag.strip().replace("_", "-").split("-")[0].lower()
    return primary if primary in TEXTS else None


def resolve_lang(query_lang: str | None, accept_language: str | None) -> str:
    """Öncelik: ?lang= → Accept-Language (q değerine göre) → İngilizce."""
    if (code := _normalize(query_lang)) is not None:
        return code
    if accept_language:
        candidates: list[tuple[float, int, str]] = []
        for idx, part in enumerate(accept_language.split(",")):
            tag, _, params = part.strip().partition(";")
            q = 1.0
            for param in params.split(";"):
                key, _, val = param.strip().partition("=")
                if key == "q":
                    try:
                        q = float(val)
                    except ValueError:
                        q = 0.0
            if q > 0 and (code := _normalize(tag)) is not None:
                candidates.append((-q, idx, code))
        if candidates:
            return min(candidates)[2]
    return DEFAULT_LANG


def _respond(kind: str, lang: str | None, accept_language: str | None) -> HTMLResponse:
    code = resolve_lang(lang, accept_language)
    return HTMLResponse(
        _PAGES[(kind, code)],
        headers={"Content-Language": code, "Vary": "Accept-Language"},
    )


@router.get("/legal/privacy", response_class=HTMLResponse)
async def privacy_policy(
    lang: str | None = Query(None),
    accept_language: str | None = Header(None),
) -> HTMLResponse:
    return _respond("privacy", lang, accept_language)


@router.get("/legal/terms", response_class=HTMLResponse)
async def terms_of_use(
    lang: str | None = Query(None),
    accept_language: str | None = Header(None),
) -> HTMLResponse:
    return _respond("terms", lang, accept_language)


@router.get("/legal/source", status_code=307, include_in_schema=True)
async def source_code() -> RedirectResponse:
    """AGPL-3.0 §13 — backend Corresponding Source'a kalıcı yönlendirme."""
    return RedirectResponse(_SOURCE_URL, status_code=307)

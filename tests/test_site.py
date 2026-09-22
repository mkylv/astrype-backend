"""Halka açık site: landing (/) + destek (/support) sayfaları.

Kapsam: durum kodları, dil çözümleme (?lang= ve Accept-Language), disclaimer'ın
görünürlüğü, yasal sayfalara alt bilgi bağlantıları, fotoğraf silme ifadesi,
mağaza "yakında" durumu, statik görsellerin sunulması, HTML iyi biçimliliği ve
bilinmeyen yolların hâlâ JSON 404 döndürmesi.
"""
from __future__ import annotations

from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from app.api.routes_site import (
    APP_STORE_URL,
    CONTACT_EMAIL,
    PLAY_BADGE_IMG,
    PLAY_STORE_URL,
    SITE_LANGS,
    _STYLE,
    resolve_site_lang,
)
from app.main import app

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


class _WellFormed(HTMLParser):
    """Kapanmamış / yanlış sırayla kapanmış etiketleri yakalar."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"fazladan kapanış: </{tag}>")
        elif self.stack[-1] != tag:
            self.errors.append(f"</{tag}> beklenirken </{self.stack[-1]}> açıktı")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def _assert_well_formed(html: str) -> None:
    parser = _WellFormed()
    parser.feed(html)
    parser.close()
    assert not parser.errors, parser.errors
    assert not parser.stack, f"kapanmamış etiketler: {parser.stack}"


# --- temel durumlar ------------------------------------------------------


def test_landing_ok_and_has_disclaimer(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    html = r.text
    assert "entertainment and personal insight" in html
    assert "not a substitute for professional" in html
    assert '<html lang="en"' in html


def test_landing_tr_disclaimer(client: TestClient) -> None:
    html = client.get("/?lang=tr").text
    assert "eğlence ve kişisel içgörü" in html
    assert "yerine geçmez" in html


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_support_ok_in_both_languages(client: TestClient, lang: str) -> None:
    r = client.get(f"/support?lang={lang}")
    assert r.status_code == 200
    assert r.headers["content-language"] == lang
    assert f'<html lang="{lang}"' in r.text
    assert f"mailto:{CONTACT_EMAIL}" in r.text


# --- dil çözümleme -------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/support"])
def test_query_lang_wins(client: TestClient, path: str) -> None:
    r = client.get(path + "?lang=tr", headers={"Accept-Language": "en-US,en;q=0.9"})
    assert r.headers["content-language"] == "tr"


@pytest.mark.parametrize("path", ["/", "/support"])
def test_accept_language_used_when_no_query(client: TestClient, path: str) -> None:
    r = client.get(path, headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5"})
    assert r.headers["content-language"] == "tr"
    assert r.headers["vary"] == "Accept-Language"


@pytest.mark.parametrize("tag", ["de", "fr", "ar", "zz", "", None])
def test_unsupported_languages_fall_back_to_english(tag: str | None) -> None:
    assert resolve_site_lang(tag, None) == "en"


def test_accept_language_unsupported_falls_back(client: TestClient) -> None:
    r = client.get("/", headers={"Accept-Language": "de-DE,de;q=0.9"})
    assert r.headers["content-language"] == "en"


def test_q_values_respected() -> None:
    assert resolve_site_lang(None, "en;q=0.2,tr;q=0.9") == "tr"
    assert resolve_site_lang(None, "tr;q=0.1,en;q=0.8") == "en"


# --- alt bilgi / bağlantılar ---------------------------------------------


@pytest.mark.parametrize("path", ["/", "/support"])
@pytest.mark.parametrize("lang", SITE_LANGS)
def test_footer_links_to_legal_pages(client: TestClient, path: str, lang: str) -> None:
    html = client.get(f"{path}?lang={lang}").text
    assert f'href="/legal/privacy?lang={lang}"' in html
    assert f'href="/legal/terms?lang={lang}"' in html
    assert 'href="/legal/source"' in html


def test_pages_link_to_each_other(client: TestClient) -> None:
    assert 'href="/support?lang=en"' in client.get("/").text
    assert 'href="/?lang=en"' in client.get("/support").text


def test_language_switcher_offers_other_language(client: TestClient) -> None:
    assert 'href="/?lang=tr"' in client.get("/?lang=en").text
    assert 'href="/support?lang=en"' in client.get("/support?lang=tr").text


# --- içerik doğruluğu ----------------------------------------------------


def test_photo_deletion_is_stated(client: TestClient) -> None:
    assert "deleted from the server" in client.get("/").text
    assert "sunucudan silinir" in client.get("/?lang=tr").text


def test_support_has_faq_and_account_deletion(client: TestClient) -> None:
    html = client.get("/support?lang=en").text
    assert html.count("<details>") >= 8
    assert "Permanently delete account" in html
    assert "apps.apple.com/account/subscriptions" in html
    assert "play.google.com/store/account/subscriptions" in html


def test_store_links_show_coming_soon_while_unreleased(client: TestClient) -> None:
    html = client.get("/").text
    if not (APP_STORE_URL and PLAY_STORE_URL):
        assert "Coming soon" in html
        assert "has not been released yet" in html
        # Ölü mağaza bağlantısı olmamalı.
        assert 'href="https://apps.apple.com/app' not in html
        assert 'href="https://play.google.com/store/apps' not in html


def test_no_fake_social_proof(client: TestClient) -> None:
    for path in ("/", "/support", "/?lang=tr", "/support?lang=tr"):
        html = client.get(path).text.lower()
        for word in ("testimonial", "users trust", "kullanıcı bize güveniyor", "★★★"):
            assert word not in html


# --- statik varlıklar ----------------------------------------------------


@pytest.mark.parametrize("name", ["en-1.jpg", "tr-1.jpg", "icon.png", "play-badge.png"])
def test_static_assets_served(client: TestClient, name: str) -> None:
    r = client.get(f"/static/img/{name}")
    assert r.status_code == 200
    assert len(r.content) > 1000


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_all_referenced_images_exist(client: TestClient, lang: str) -> None:
    import re

    for path in ("/", "/support"):
        html = client.get(f"{path}?lang={lang}").text
        for src in set(re.findall(r'src="(/static/[^"]+)"', html)):
            assert client.get(src).status_code == 200, src


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_images_have_alt_attributes(client: TestClient, lang: str) -> None:
    import re

    html = client.get(f"/?lang={lang}").text
    imgs = re.findall(r"<img\b[^>]*>", html)
    assert imgs
    for tag in imgs:
        assert 'alt="' in tag, tag


def test_reduced_motion_supported(client: TestClient) -> None:
    assert "prefers-reduced-motion" in client.get("/").text


# --- HTML iyi biçimliliği + 404 davranışı --------------------------------


@pytest.mark.parametrize("path", ["/", "/support"])
@pytest.mark.parametrize("lang", SITE_LANGS)
def test_html_is_well_formed(client: TestClient, path: str, lang: str) -> None:
    _assert_well_formed(client.get(f"{path}?lang={lang}").text)


def test_unknown_path_still_json_404(client: TestClient) -> None:
    r = client.get("/definitely-not-a-page")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["detail"] == "Not Found"


def test_health_endpoint_untouched(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"


# --- mağaza rozetleri ----------------------------------------------------


def test_contact_address_is_the_international_one(client: TestClient) -> None:
    assert CONTACT_EMAIL == "support@astrype.com"
    for path in ("/", "/support", "/?lang=tr", "/support?lang=tr"):
        html = client.get(path).text
        assert f"mailto:{CONTACT_EMAIL}" in html
        assert "destek@astrype.com" not in html


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_both_store_badges_are_rendered(client: TestClient, lang: str) -> None:
    """Hem Apple (satır içi SVG) hem Google Play (resmî PNG) rozeti var."""
    html = client.get(f"/?lang={lang}").text
    assert html.count(PLAY_BADGE_IMG) >= 1
    assert "Download on the" in html and "App Store" in html
    assert "Get it on Google Play" in html
    # Rozetler hem kahraman bölümünde hem de kapanış CTA'sında.
    assert html.count('class="stores"') == 2


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_badges_are_disabled_while_unreleased(client: TestClient, lang: str) -> None:
    html = client.get(f"/?lang={lang}").text
    if APP_STORE_URL and PLAY_STORE_URL:
        pytest.skip("uygulama yayında")
    # Tıklanabilir rozet yok, "yakında" durumu açıkça işaretli.
    assert '<a class="store' not in html
    assert 'class="store store--soon" aria-disabled="true"' in html
    assert 'class="store store--apple store--soon"' in html
    assert "soonpill" in html
    assert ".store--soon" in _STYLE
    soon = "Coming soon" if lang == "en" else "Yakında"
    assert soon in html
    # Rozet metni de "yakında" der (ekran okuyucu için).
    assert f"App Store \u2014 {soon}" in html
    assert f"Google Play \u2014 {soon}" in html


def test_flipping_store_urls_produces_real_links(monkeypatch) -> None:
    """APP_STORE_URL / PLAY_STORE_URL doldurulunca rozetler bağlantıya döner."""
    from app.api import routes_site as rs

    monkeypatch.setattr(rs, "APP_STORE_URL", "https://apps.apple.com/app/id123")
    monkeypatch.setattr(rs, "PLAY_STORE_URL", "https://play.google.com/store/apps/details?id=x")
    html = rs.render_home("en")
    assert '<a class="store store--apple" href="https://apps.apple.com/app/id123"' in html
    assert 'href="https://play.google.com/store/apps/details?id=x"' in html
    assert 'aria-disabled="true"' not in html
    assert 'class="store store--apple store--soon"' not in html
    assert 'class="soonpill"' not in html
    assert "Coming soon" not in html.replace("store--soon", "")
    assert "has not been released yet" not in html


# --- başlık / alt bilgi --------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/support"])
@pytest.mark.parametrize("lang", SITE_LANGS)
def test_header_lockup_and_controls(client: TestClient, path: str, lang: str) -> None:
    html = client.get(f"{path}?lang={lang}").text
    assert '<header class="site at-top">' in html
    assert 'class="brand"' in html and '<svg class="mark"' in html
    assert '<span class="wm">Astrype</span>' in html
    assert 'class="langsw"' in html
    assert 'class="btn btn-gold"' in html        # birincil CTA
    assert 'class="skip" href="#main"' in html   # içeriğe atla
    assert 'id="main"' in html


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_footer_has_columns_and_language_switcher(client: TestClient, lang: str) -> None:
    other = "tr" if lang == "en" else "en"
    html = client.get(f"/support?lang={lang}").text
    foot = html[html.index('<footer class="site">'):]
    for href in (
        f'/support?lang={lang}',
        f'/legal/privacy?lang={lang}',
        f'/legal/terms?lang={lang}',
        "/legal/source",
        f"mailto:{CONTACT_EMAIL}",
        f'/?lang={other}',
    ):
        assert href in foot, href
    assert "footgrid" in foot and "footcol" in foot


# --- hareket katmanı -----------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/support"])
def test_ambient_canvas_and_motion_guards(client: TestClient, path: str) -> None:
    html = client.get(path).text
    assert '<canvas class="stars" aria-hidden="true"></canvas>' in html
    # sekme gizlenince duraklar, azaltılmış harekette hiç başlamaz
    assert "visibilitychange" in html
    assert "prefers-reduced-motion: reduce" in html
    assert "IntersectionObserver" in html


def test_zodiac_wheel_is_decorative(client: TestClient) -> None:
    html = client.get("/").text
    assert '<svg class="wheel"' in html
    wheel = html[html.index('<svg class="wheel"'):]
    assert 'aria-hidden="true"' in wheel[:120]
    assert "@keyframes spin" in html


def test_reduced_motion_disables_every_layer(client: TestClient) -> None:
    css = _STYLE
    block = css[css.index("@media(prefers-reduced-motion:reduce)"):]
    for rule in ("animation:none!important", "transition:none!important",
                 "opacity:1!important", "canvas.stars{display:none}"):
        assert rule in block, rule


def test_content_is_visible_without_javascript(client: TestClient) -> None:
    """Gizleme sınıfı yalnızca html.js-motion altında tanımlı olmalı; JS yoksa
    hiçbir bölüm opacity:0'da takılı kalmaz."""
    css = _STYLE
    assert "html.js-motion .reveal{opacity:0" in css
    assert "html.js-motion .stagger>*{opacity:0" in css
    for bad in (".reveal{opacity:0", ".stagger>*{opacity:0"):
        # yalnızca js-motion önekiyle geçebilir
        idx = 0
        while True:
            idx = css.find(bad, idx)
            if idx == -1:
                break
            assert css[max(0, idx - 15):idx].endswith("html.js-motion "), css[idx - 40:idx + 20]
            idx += 1
    # saydam başlık da JS'e bağlı; JS yoksa başlık opak kalır
    assert "html.js-head header.site.at-top{background:transparent" in css


# --- düzen / performans --------------------------------------------------


def test_no_horizontal_overflow_crutch(client: TestClient) -> None:
    """body{overflow-x:hidden} kaldırıldı — düzen gerçekten taşmıyor."""
    assert "overflow-x:hidden" not in _STYLE


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_below_fold_images_are_lazy_and_sized(client: TestClient, lang: str) -> None:
    import re

    html = client.get(f"/?lang={lang}").text
    imgs = re.findall(r"<img\b[^>]*>", html)
    assert len(imgs) >= 6
    eager = [t for t in imgs if "loading=" not in t]
    # yalnızca kahraman görseli önceliklidir
    assert len(eager) == 1 and 'fetchpriority="high"' in eager[0]
    for tag in imgs:
        assert 'width="' in tag and 'height="' in tag, tag


@pytest.mark.parametrize("lang", SITE_LANGS)
def test_page_weight_is_sane(client: TestClient, lang: str) -> None:
    """İlk yük (HTML + eager görseller) makul sınırda kalmalı."""
    import re

    html = client.get(f"/?lang={lang}").text
    total = len(html.encode())
    for src in set(re.findall(r'src="(/static/[^"]+)"', html)):
        tag = re.search(r'<img\b[^>]*src="%s"[^>]*>' % re.escape(src), html)
        if tag and "loading=" in tag.group(0):
            continue  # tembel yüklenir
        total += len(client.get(src).content)
    assert total < 800_000, total

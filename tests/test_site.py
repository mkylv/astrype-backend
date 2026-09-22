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
    PLAY_STORE_URL,
    SITE_LANGS,
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


@pytest.mark.parametrize("name", ["en-1.jpg", "tr-1.jpg", "icon.png"])
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

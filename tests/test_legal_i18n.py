"""Yasal sayfa yerelleştirmesi: dil çözümleme, RTL, açık kaynak bölümü, yapısal eşitlik."""
from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.api.routes_legal import resolve_lang
from app.legal_texts import RTL_LANGS, SOURCE_LANG, SUPPORTED_LANGS, TEXTS
from app.main import app

REPO = "https://github.com/mkylv/astrype-backend"
TOKENS = ("{contact_link}", "{source_link}", "{source_path_link}", "{license}",
          "<strong>", "<em>", "<code>")


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _count(html: str, tag: str) -> int:
    return len(re.findall(rf"<{tag}[\s>]", html))


def test_terms_en_has_open_source_section(client: TestClient) -> None:
    r = client.get("/legal/terms?lang=en")
    assert r.status_code == 200
    html = r.text
    assert '<html lang="en" dir="ltr">' in html
    assert "Terms of Use" in html
    assert "Open source / Source code" in html
    assert f'href="{REPO}"' in html
    assert 'href="/legal/source"' in html
    assert "AGPL-3.0" in html
    assert "entertainment and personal insight" in html
    assert "the Turkish version prevails" in html
    assert r.headers["content-language"] == "en"


def test_privacy_en_photo_deletion_and_providers(client: TestClient) -> None:
    html = client.get("/legal/privacy?lang=en").text
    assert "deleted immediately after analysis" in html
    assert "OpenAI" in html and "Google Gemini" in html
    assert "Permanently delete account" in html
    assert "mailto:destek@astrype.com" in html


@pytest.mark.parametrize("code", sorted(RTL_LANGS))
def test_rtl_languages(client: TestClient, code: str) -> None:
    html = client.get(f"/legal/terms?lang={code}").text
    assert f'<html lang="{code}" dir="rtl">' in html


def test_ar_is_rtl(client: TestClient) -> None:
    assert 'dir="rtl"' in client.get("/legal/privacy?lang=ar").text


def test_accept_language_de(client: TestClient) -> None:
    r = client.get("/legal/terms", headers={"Accept-Language": "de-DE,de;q=0.9,en;q=0.5"})
    assert r.status_code == 200
    assert '<html lang="de"' in r.text
    assert r.headers["content-language"] == "de"


def test_query_param_beats_header(client: TestClient) -> None:
    r = client.get("/legal/terms?lang=ja", headers={"Accept-Language": "de"})
    assert '<html lang="ja"' in r.text


def test_unknown_lang_falls_back_to_en(client: TestClient) -> None:
    r = client.get("/legal/terms?lang=xx")
    assert '<html lang="en"' in r.text
    r = client.get("/legal/privacy", headers={"Accept-Language": "sw-KE"})
    assert '<html lang="en"' in r.text
    assert '<html lang="en"' in client.get("/legal/privacy").text


def test_turkish_has_no_translation_notice(client: TestClient) -> None:
    html = client.get("/legal/terms?lang=tr").text
    assert '<html lang="tr"' in html
    assert 'class="tn"' not in html
    assert "Açık kaynak / Kaynak kodu" in html


@pytest.mark.parametrize(
    ("q", "header", "expected"),
    [
        ("pt-BR", None, "pt"),
        ("zh_Hans", None, "zh"),
        ("EN", None, "en"),
        (None, "fr-CA;q=0.4, uk;q=0.8", "uk"),
        (None, "xx, ko;q=0.1", "ko"),
        (None, "de;q=0", "en"),
        (None, None, "en"),
    ],
)
def test_resolve_lang(q: str | None, header: str | None, expected: str) -> None:
    assert resolve_lang(q, header) == expected


def test_source_redirect(client: TestClient) -> None:
    r = client.get("/legal/source", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == REPO


def test_all_20_languages_present() -> None:
    assert len(SUPPORTED_LANGS) == 20
    assert set(TEXTS) == set(SUPPORTED_LANGS)


@pytest.mark.parametrize("code", SUPPORTED_LANGS)
def test_data_structure_parity_with_turkish(code: str) -> None:
    src, t = TEXTS[SOURCE_LANG], TEXTS[code]
    for kind in ("privacy", "terms"):
        assert [len(p) for _, p in t[kind]["sections"]] == [
            len(p) for _, p in src[kind]["sections"]
        ], (code, kind)
        a = json.dumps(t[kind], ensure_ascii=False)
        b = json.dumps(src[kind], ensure_ascii=False)
        for tok in TOKENS:
            assert a.count(tok) == b.count(tok), (code, kind, tok)
    if code != SOURCE_LANG:
        assert t["translation_notice"].strip(), code
    assert t["dir"] == ("rtl" if code in RTL_LANGS else "ltr")


@pytest.mark.parametrize("code", SUPPORTED_LANGS)
@pytest.mark.parametrize("kind", ["privacy", "terms"])
def test_every_language_renders_with_section_parity(
    client: TestClient, code: str, kind: str
) -> None:
    tr_html = client.get(f"/legal/{kind}?lang=tr").text
    r = client.get(f"/legal/{kind}?lang={code}")
    assert r.status_code == 200
    html = r.text
    assert f'<html lang="{code}"' in html
    for tag in ("h2", "p"):
        # +1 <p>: çeviri uyarısı (yalnızca Türkçe olmayan sayfalarda)
        extra = 1 if (tag == "p" and code != SOURCE_LANG) else 0
        assert _count(html, tag) == _count(tr_html, tag) + extra, (code, kind, tag)
    assert "{" not in re.sub(r"<style>.*?</style>", "", html, flags=re.S), code
    assert html.count("mailto:destek@astrype.com") == tr_html.count("mailto:destek@astrype.com")
    assert html.count(f'href="{REPO}"') == tr_html.count(f'href="{REPO}"') >= 1
    assert "Astrype" in html
    # Dil seçici: 20 bağlantı
    assert len(re.findall(r'<a href="\?lang=[a-z]{2}"', html)) == 20

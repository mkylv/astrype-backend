"""Yasal sayfa metinleri — dil başına bir veri modülü (app/legal_texts/<lang>.py).

KAYNAK METİN TÜRKÇEDİR (tr.py). Diğer diller kolaylık amacıyla sunulan
çevirilerdir; herhangi bir çelişki veya farklılık halinde Türkçe metin geçerlidir.
(Translations are provided for convenience only; in case of any conflict, the
Turkish version prevails.) Her çeviri sayfasında bu durum tek satırlık bir
uyarıyla (`translation_notice`) gösterilir.

Metin değişikliği akışı: önce tr.py güncellenir, ardından tüm diller aynı yapıda
(bölüm/paragraf sayısı, yer tutucular) güncellenir — tests/test_legal_i18n.py
yapısal eşitliği doğrular.
"""
from __future__ import annotations

import importlib
from typing import Any

SOURCE_LANG = "tr"
DEFAULT_LANG = "en"

# Uygulamanın desteklediği 20 dil (astrype_app/lib/l10n ile aynı).
SUPPORTED_LANGS: tuple[str, ...] = (
    "ar", "az", "de", "en", "es", "fa", "fr", "hi", "id", "it",
    "ja", "ko", "nl", "pl", "pt", "ru", "tr", "uk", "ur", "zh",
)

RTL_LANGS = frozenset({"ar", "fa", "ur"})

TEXTS: dict[str, dict[str, Any]] = {
    code: importlib.import_module(f"{__name__}.{code}").TEXT for code in SUPPORTED_LANGS
}

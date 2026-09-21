"""Polish legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Polski",
    "dir": "ltr",
    "updated_label": "Ostatnia aktualizacja",
    "updated": "14 lipca 2026",
    "contact_label": "Kontakt",
    "languages_label": "Język",
    "translation_notice": (
        "To tłumaczenie udostępniono wyłącznie dla wygody. W razie jakichkolwiek rozbieżności "
        "rozstrzygająca jest wersja turecka."
    ),
    "privacy": {
        "title": "Polityka prywatności",
        "note": (
            "<strong>Podsumowanie:</strong> Używamy Twoich danych wyłącznie do tworzenia dla Ciebie "
            "spersonalizowanych treści astrologicznych i wróżbiarskich. Przesłane przez Ciebie zdjęcia "
            "do wróżenia z fusów kawy, z dłoni lub z twarzy są <strong>usuwane natychmiast po "
            "analizie</strong> i nie są przechowywane. Nie sprzedajemy Twoich danych osobom trzecim. "
            "W dowolnym momencie możesz całkowicie usunąć swoją historię i konto z poziomu aplikacji."
        ),
        "sections": [
            ("Dane, które zbieramy", [
                "Konto: adres e-mail (za pośrednictwem Supabase Auth). Profil: Twoje imię (opcjonalnie), "
                "data/godzina/miejsce urodzenia oraz Twoje preferencje dotyczące języka i zainteresowań. "
                "Treści: tworzone przez Ciebie analizy (horoskop urodzeniowy, tarot, wróżby, zgodność w "
                "związku), historia Twoich rozmów ze sztuczną inteligencją oraz zapisy kontekstu złożone "
                "z krótkich podsumowań tych danych (Cosmic Memory).",
            ]),
            ("Zdjęcia", [
                "Zdjęcia przesłane do wróżenia z fusów kawy, z dłoni lub z twarzy są przetwarzane na "
                "serwerze wyłącznie w czasie analizy i <strong>trwale usuwane zaraz po jej "
                "zakończeniu</strong>. Zdjęcia nie są przechowywane; w archiwum zachowywany jest jedynie "
                "wynik tekstowy i lista symboli.",
            ]),
            ("Jak przetwarzane są Twoje dane", [
                "Obliczenia astrologiczne wykonywane są na naszym serwerze (Swiss Ephemeris). W celu "
                "przygotowania spersonalizowanych interpretacji Twoje treści są przekazywane dostawcom "
                "sztucznej inteligencji (OpenAI i Google Gemini) wyłącznie w celu wygenerowania "
                "interpretacji. Klucze API przechowywane są wyłącznie na serwerze; nie ma ich w aplikacji.",
            ]),
            ("Przechowywanie i usuwanie", [
                "Możesz usunąć swoje dane w dowolnym momencie: za pomocą <em>Profil → Moje dane → Usuń "
                "pamięć / historię</em> usuniesz historię analiz i rozmów; za pomocą <em>Trwale usuń "
                "konto</em> trwale usuniesz wszystkie swoje dane i konto. Po usunięciu konta wszystkie "
                "powiązane z nim zapisy są usuwane nieodwracalnie.",
            ]),
            ("Udostępnianie", [
                "Nie sprzedajemy ani nie wypożyczamy Twoich danych w celach reklamowych. Przetwarzamy je "
                "wyłącznie z dostawcami infrastruktury niezbędnymi do świadczenia usługi "
                "(uwierzytelnianie, baza danych, interpretacje oparte na sztucznej inteligencji, "
                "zarządzanie subskrypcjami).",
            ]),
            ("Korzystanie z Twoich praw (KVKK/GDPR)", [
                "Masz prawo dostępu do swoich danych, ich sprostowania, usunięcia oraz ograniczenia ich "
                "przetwarzania. W sprawie swojego wniosku możesz napisać na adres {contact_link}.",
            ]),
            ("Dzieci", [
                "Astrype nie jest przeznaczona dla użytkowników poniżej 13. roku życia.",
            ]),
            ("Otwarte oprogramowanie", [
                "Kod źródłowy oprogramowania serwerowego Astrype jest publicznie dostępny na licencji "
                "{license}: {source_link}. Kod źródłowy nie zawiera żadnych danych użytkowników ani "
                "tajnych kluczy.",
            ]),
        ],
    },
    "terms": {
        "title": "Warunki użytkowania",
        "note": (
            "<strong>Ważne:</strong> Interpretacje astrologiczne, tarota, wróżenia z fusów kawy, z "
            "dłoni lub z twarzy oraz snów w Astrype służą <strong>wyłącznie rozrywce i osobistej "
            "refleksji</strong>. Nie zastępują profesjonalnego wsparcia przy decyzjach medycznych, "
            "prawnych, finansowych ani krytycznych dla bezpieczeństwa. Twój przewodnik oparty na "
            "sztucznej inteligencji (Lyra) nie składa definitywnych deklaracji dotyczących losu ani "
            "przyszłości."
        ),
        "sections": [
            ("Charakter usługi", [
                "Astrype oferuje horoskop urodzeniowy, interpretacje dzienne/miesięczne, tarota, moduły "
                "wróżb oraz asystenta czatu opartego na sztucznej inteligencji, który zna Twoją historię. "
                "Treści służą osobistej refleksji i wglądowi; nie roszczą sobie prawa do naukowej ani "
                "ostatecznej prawdy.",
            ]),
            ("Wyłączenie odpowiedzialności", [
                "Ponosisz odpowiedzialność za decyzje podejmowane na podstawie interpretacji w aplikacji. "
                "W sytuacjach dotyczących zdrowia, prawa, finansów lub kryzysu zwróć się do właściwego "
                "specjalisty.",
            ]),
            ("Subskrypcja", [
                "Funkcje Premium wymagają subskrypcji. Płatności, odnowienia i anulowanie są obsługiwane "
                "przez Apple App Store lub Google Play. Subskrypcja odnawia się automatycznie, chyba że "
                "anulujesz ją przed końcem okresu rozliczeniowego; możesz ją anulować na swoim koncie w "
                "sklepie. Zakupy można przywrócić za pomocą opcji \"Przywróć zakupy\".",
            ]),
            ("Dopuszczalne korzystanie", [
                "Nie możesz korzystać z usługi w celach niezgodnych z prawem, w sposób naruszający prawa "
                "innych osób ani nadużywając systemu.",
            ]),
            ("Zmiany", [
                "Możemy od czasu do czasu aktualizować niniejsze warunki. O istotnych zmianach "
                "poinformujemy w aplikacji.",
            ]),
            ("Otwarte oprogramowanie / Kod źródłowy", [
                "Oprogramowanie serwerowe (backend) Astrype jest otwartoźródłowe i udostępniane na "
                "licencji <strong>{license}</strong>. Każdy użytkownik, który korzysta z tej usługi za "
                "pośrednictwem sieci, może bezpłatnie uzyskać dostęp do pełnego kodu źródłowego "
                "oprogramowania obsługującego usługę, a także przeglądać go, modyfikować i "
                "rozpowszechniać na warunkach licencji:",
                "{source_link}",
                "Stały link: {source_path_link}. Obliczenia astrologiczne wykorzystują bibliotekę Swiss "
                "Ephemeris firmy Astrodienst AG (w opcji AGPL) oraz Kerykeion; licencje stron trzecich "
                "wymieniono w pliku <code>THIRD_PARTY_LICENSES.md</code> w repozytorium. Licencja "
                "stanowi, że oprogramowanie jest udostępniane \"w stanie, w jakim jest\", bez "
                "jakiejkolwiek gwarancji. Niniejsza sekcja obejmuje wyłącznie kod źródłowy "
                "oprogramowania serwerowego; nazwa i logo Astrype nie stanowią prawa do używania znaku "
                "towarowego udzielonego na mocy tej licencji.",
            ]),
            ("Kontakt", [
                "W razie pytań: {contact_link}",
            ]),
        ],
    },
}

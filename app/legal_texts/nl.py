"""Dutch legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Nederlands",
    "dir": "ltr",
    "updated_label": "Laatst bijgewerkt",
    "updated": "14 juli 2026",
    "contact_label": "Contact",
    "languages_label": "Taal",
    "translation_notice": (
        "Deze vertaling wordt uitsluitend voor het gemak aangeboden. Bij strijdigheid "
        "prevaleert de Turkse versie."
    ),
    "privacy": {
        "title": "Privacybeleid",
        "note": (
            "<strong>Samenvatting:</strong> We gebruiken je gegevens alleen om gepersonaliseerde "
            "astrologie- en waarzeggerij-inhoud voor je te maken. Foto's die je uploadt voor koffiedik-, "
            "hand- of gezichtlezingen worden <strong>direct na de analyse verwijderd</strong> en niet "
            "bewaard. We verkopen je gegevens niet aan derden. Je kunt je geschiedenis en je account op elk "
            "gewenst moment volledig vanuit de app verwijderen."
        ),
        "sections": [
            ("Gegevens die we verzamelen", [
                "Account: e-mailadres (via Supabase Auth). Profiel: je naam (optioneel), geboortedatum/-tijd/"
                "-plaats en je voorkeuren voor taal en interesses. Inhoud: de analyses die je genereert "
                "(geboortehoroscoop, tarot, lezingen, relatiecompatibiliteit), je AI-chatgeschiedenis en "
                "contextgegevens die bestaan uit korte samenvattingen daarvan (Cosmic Memory).",
            ]),
            ("Foto's", [
                "Foto's die je uploadt voor koffiedik-, hand- of gezichtlezingen worden op de server alleen "
                "verwerkt zolang de analyse duurt en worden <strong>permanent verwijderd zodra de analyse "
                "is afgerond</strong>. Foto's worden niet bewaard; in het archief worden alleen het "
                "tekstresultaat en de lijst met symbolen bewaard.",
            ]),
            ("Hoe je gegevens worden verwerkt", [
                "Astrologische berekeningen worden op onze server uitgevoerd (Swiss Ephemeris). Voor "
                "gepersonaliseerde interpretaties wordt je inhoud uitsluitend voor het genereren van "
                "interpretaties doorgestuurd naar AI-aanbieders (OpenAI en Google Gemini). API-sleutels "
                "worden alleen op de server bewaard; ze staan niet in de app.",
            ]),
            ("Bewaring en verwijdering", [
                "Je kunt je gegevens op elk moment verwijderen: met <em>Profiel → Mijn gegevens → Geheugen "
                "/ geschiedenis wissen</em> verwijder je je analyse- en chatgeschiedenis; met <em>Account "
                "permanent verwijderen</em> verwijder je al je gegevens en je account permanent. Wanneer "
                "een account wordt verwijderd, worden alle bijbehorende gegevens onherroepelijk "
                "verwijderd.",
            ]),
            ("Delen", [
                "We verkopen of verhuren je gegevens niet voor advertentiedoeleinden. We verwerken ze "
                "alleen met de infrastructuuraanbieders die nodig zijn om de dienst te leveren "
                "(authenticatie, database, AI-interpretatie, abonnementsbeheer).",
            ]),
            ("Je rechten uitoefenen (KVKK/GDPR)", [
                "Je hebt het recht om je gegevens in te zien, te corrigeren en te verwijderen en om de "
                "verwerking ervan te beperken. Voor je verzoek kun je schrijven naar {contact_link}.",
            ]),
            ("Kinderen", [
                "Astrype is niet bedoeld voor gebruikers jonger dan 13 jaar.",
            ]),
            ("Open source", [
                "De broncode van de Astrype-serversoftware is openbaar beschikbaar onder de "
                "{license}-licentie: {source_link}. De broncode bevat geen gebruikersgegevens of geheime "
                "sleutels.",
            ]),
        ],
    },
    "terms": {
        "title": "Gebruiksvoorwaarden",
        "note": (
            "<strong>Belangrijk:</strong> De astrologie-, tarot-, koffiedik-/hand-/gezichts- en "
            "droominterpretaties in Astrype zijn <strong>uitsluitend bedoeld voor vermaak en persoonlijk "
            "inzicht</strong>. Ze zijn geen vervanging voor professionele ondersteuning bij medische, "
            "juridische, financiële of veiligheidskritieke beslissingen. Je AI-gids (Lyra) doet geen "
            "definitieve uitspraken over het lot of de toekomst."
        ),
        "sections": [
            ("Aard van de dienst", [
                "Astrype biedt een geboortehoroscoop, dagelijkse/maandelijkse interpretaties, tarot, "
                "waarzeggerijmodules en een AI-chatassistent die je geschiedenis kent. De inhoud is bedoeld "
                "voor persoonlijke reflectie en inzicht; er wordt geen aanspraak gemaakt op wetenschappelijke "
                "of definitieve waarheid.",
            ]),
            ("Disclaimer", [
                "Je bent zelf verantwoordelijk voor de beslissingen die je neemt op basis van de "
                "interpretaties in de app. Raadpleeg bij gezondheids-, juridische, financiële of "
                "crisissituaties een deskundige.",
            ]),
            ("Abonnement", [
                "Premiumfuncties vereisen een abonnement. Betaling, verlenging en opzegging worden beheerd "
                "via de Apple App Store of Google Play. Het abonnement wordt automatisch verlengd tenzij je "
                "het vóór het einde van de periode opzegt; je kunt opzeggen via je store-account. Aankopen "
                "kunnen worden hersteld via \"Aankopen herstellen\".",
            ]),
            ("Aanvaardbaar gebruik", [
                "Je mag de dienst niet gebruiken voor illegale doeleinden, op een manier die inbreuk maakt "
                "op de rechten van anderen, of door misbruik te maken van het systeem.",
            ]),
            ("Wijzigingen", [
                "We kunnen deze voorwaarden van tijd tot tijd bijwerken. Belangrijke wijzigingen kondigen "
                "we aan in de app.",
            ]),
            ("Open source / Broncode", [
                "De serversoftware (backend) van Astrype is open source en wordt gepubliceerd onder de "
                "<strong>{license}</strong>-licentie. Elke gebruiker die via een netwerk met deze dienst "
                "communiceert, kan gratis toegang krijgen tot de volledige broncode van de software waarop "
                "de dienst draait, en kan deze inzien, wijzigen en binnen de licentievoorwaarden opnieuw "
                "verspreiden:",
                "{source_link}",
                "Permanente link: {source_path_link}. De astrologische berekeningen maken gebruik van de "
                "Swiss Ephemeris-bibliotheek van Astrodienst AG (onder de AGPL-optie) en Kerykeion; "
                "licenties van derden staan vermeld in het bestand <code>THIRD_PARTY_LICENSES.md</code> in "
                "de repository. De licentie bepaalt dat de software \"as is\" en zonder enige garantie "
                "wordt geleverd. Dit gedeelte heeft alleen betrekking op de broncode van de serversoftware; "
                "de naam en het logo van Astrype vormen geen merkgebruiksrecht dat onder deze licentie "
                "wordt verleend.",
            ]),
            ("Contact", [
                "Voor vragen: {contact_link}",
            ]),
        ],
    },
}

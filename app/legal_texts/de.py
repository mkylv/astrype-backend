"""German legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Deutsch",
    "dir": "ltr",
    "updated_label": "Zuletzt aktualisiert",
    "updated": "14. Juli 2026",
    "contact_label": "Kontakt",
    "languages_label": "Sprache",
    "translation_notice": (
        "Diese Übersetzung dient nur der Orientierung. Im Falle von Widersprüchen ist "
        "die türkische Fassung maßgeblich."
    ),
    "privacy": {
        "title": "Datenschutz",
        "note": (
            "<strong>Zusammenfassung:</strong> Wir verwenden deine Daten ausschließlich, um "
            "personalisierte Astrologie- und Wahrsage-Inhalte für dich zu erstellen. Fotos, die du für "
            "Kaffeesatz-, Hand- oder Gesichtsdeutungen hochlädst, werden <strong>unmittelbar nach der "
            "Analyse gelöscht</strong> und nicht gespeichert. Wir verkaufen deine Daten nicht an Dritte. "
            "Du kannst deinen Verlauf und dein Konto jederzeit vollständig in der App löschen."
        ),
        "sections": [
            ("Welche Daten wir erheben", [
                "Konto: E-Mail-Adresse (über Supabase Auth). Profil: dein Name (optional), "
                "Geburtsdatum/-zeit/-ort sowie deine Sprach- und Interessenpräferenzen. Inhalte: die von dir "
                "erstellten Analysen (Geburtshoroskop, Tarot, Deutungen, Beziehungskompatibilität), dein "
                "KI-Chatverlauf und Kontextdatensätze, die aus kurzen Zusammenfassungen davon bestehen "
                "(Cosmic Memory).",
            ]),
            ("Fotos", [
                "Fotos, die du für Kaffeesatz-, Hand- oder Gesichtsdeutungen hochlädst, werden auf dem "
                "Server nur für die Dauer der Analyse verarbeitet und <strong>sofort nach Abschluss der "
                "Analyse dauerhaft gelöscht</strong>. Fotos werden nicht gespeichert; im Archiv werden nur "
                "das Textergebnis und die Liste der Symbole aufbewahrt.",
            ]),
            ("Wie deine Daten verarbeitet werden", [
                "Astrologische Berechnungen werden auf unserem Server durchgeführt (Swiss Ephemeris). Für "
                "personalisierte Deutungen werden deine Inhalte ausschließlich zum Zweck der Erstellung von "
                "Deutungen an KI-Anbieter (OpenAI und Google Gemini) übermittelt. API-Schlüssel werden nur "
                "auf dem Server aufbewahrt; in der App sind sie nicht enthalten.",
            ]),
            ("Speicherung und Löschung", [
                "Du kannst deine Daten jederzeit löschen: Mit <em>Profil → Meine Daten → Speicher / "
                "Verlauf löschen</em> entfernst du deinen Analyse- und Chatverlauf; mit <em>Konto endgültig "
                "löschen</em> entfernst du alle deine Daten und dein Konto dauerhaft. Wenn ein Konto "
                "gelöscht wird, werden alle zugehörigen Datensätze unwiderruflich gelöscht.",
            ]),
            ("Weitergabe", [
                "Wir verkaufen oder vermieten deine Daten nicht zu Werbezwecken. Wir verarbeiten sie nur "
                "mit den Infrastrukturanbietern, die für die Bereitstellung des Dienstes erforderlich sind "
                "(Authentifizierung, Datenbank, KI-Deutung, Abonnementverwaltung).",
            ]),
            ("Wahrnehmung deiner Rechte (KVKK/GDPR)", [
                "Du hast das Recht auf Auskunft über deine Daten, auf deren Berichtigung und Löschung sowie "
                "auf Einschränkung der Verarbeitung. Für dein Anliegen kannst du an {contact_link} "
                "schreiben.",
            ]),
            ("Kinder", [
                "Astrype richtet sich nicht an Nutzer unter 13 Jahren.",
            ]),
            ("Open Source", [
                "Der Quellcode der Astrype-Serversoftware ist unter der {license}-Lizenz öffentlich "
                "zugänglich: {source_link}. Der Quellcode enthält keine Nutzerdaten und keine geheimen "
                "Schlüssel.",
            ]),
        ],
    },
    "terms": {
        "title": "Nutzungsbedingungen",
        "note": (
            "<strong>Wichtig:</strong> Die Astrologie-, Tarot-, Kaffeesatz-/Hand-/Gesichts- und "
            "Traumdeutungen in Astrype dienen <strong>ausschließlich der Unterhaltung und der "
            "persönlichen Einsicht</strong>. Sie ersetzen keine professionelle Unterstützung bei "
            "medizinischen, rechtlichen, finanziellen oder sicherheitskritischen Entscheidungen. Dein "
            "KI-Guide (Lyra) trifft keine verbindlichen Aussagen über Schicksal oder Zukunft."
        ),
        "sections": [
            ("Art des Dienstes", [
                "Astrype bietet ein Geburtshoroskop, tägliche/monatliche Deutungen, Tarot, "
                "Wahrsage-Module und einen KI-Chatassistenten, der deinen Verlauf kennt. Die Inhalte dienen "
                "der persönlichen Reflexion und Einsicht; sie erheben keinen Anspruch auf wissenschaftliche "
                "oder endgültige Wahrheit.",
            ]),
            ("Haftungsausschluss", [
                "Für Entscheidungen, die du auf Grundlage der Deutungen in der App triffst, bist du selbst "
                "verantwortlich. Wende dich in gesundheitlichen, rechtlichen, finanziellen oder "
                "Krisensituationen bitte an eine entsprechende Fachperson.",
            ]),
            ("Abonnement", [
                "Premium-Funktionen erfordern ein Abonnement. Zahlung, Verlängerung und Kündigung werden "
                "über den Apple App Store oder Google Play verwaltet. Das Abonnement verlängert sich "
                "automatisch, sofern du es nicht vor Ende des Zeitraums kündigst; die Kündigung kannst du "
                "über dein Store-Konto vornehmen. Käufe können über \"Käufe wiederherstellen\" "
                "wiederhergestellt werden.",
            ]),
            ("Zulässige Nutzung", [
                "Du darfst den Dienst nicht für rechtswidrige Zwecke, nicht auf eine Weise, die die Rechte "
                "anderer verletzt, und nicht unter Missbrauch des Systems nutzen.",
            ]),
            ("Änderungen", [
                "Wir können diese Bedingungen von Zeit zu Zeit aktualisieren. Wesentliche Änderungen "
                "kündigen wir in der App an.",
            ]),
            ("Open Source / Quellcode", [
                "Die Server-Software (Backend) von Astrype ist Open Source und wird unter der "
                "<strong>{license}</strong>-Lizenz veröffentlicht. Jeder Nutzer, der über ein Netzwerk mit "
                "diesem Dienst interagiert, kann kostenlos auf den vollständigen Quellcode der Software "
                "zugreifen, die den Dienst betreibt, und ihn im Rahmen der Lizenzbedingungen einsehen, "
                "ändern und weiterverbreiten:",
                "{source_link}",
                "Dauerhafter Link: {source_path_link}. Die astrologischen Berechnungen nutzen die Swiss "
                "Ephemeris-Bibliothek von Astrodienst AG (unter der AGPL-Option) sowie Kerykeion; "
                "Lizenzen von Drittanbietern sind in der Datei <code>THIRD_PARTY_LICENSES.md</code> im "
                "Repository aufgeführt. Die Lizenz legt fest, dass die Software \"wie besehen\" und ohne "
                "jegliche Gewährleistung bereitgestellt wird. Dieser Abschnitt umfasst nur den Quellcode "
                "der Server-Software; der Name und das Logo von Astrype stellen kein unter dieser Lizenz "
                "gewährtes Markennutzungsrecht dar.",
            ]),
            ("Kontakt", [
                "Bei Fragen: {contact_link}",
            ]),
        ],
    },
}

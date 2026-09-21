"""English legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "English",
    "dir": "ltr",
    "updated_label": "Last updated",
    "updated": "July 14, 2026",
    "contact_label": "Contact",
    "languages_label": "Language",
    "translation_notice": (
        "This translation is provided for convenience only. In case of any conflict, "
        "the Turkish version prevails."
    ),
    "privacy": {
        "title": "Privacy Policy",
        "note": (
            "<strong>Summary:</strong> We use your data only to create personalized "
            "astrology/fortune-telling content for you. Coffee/palm/face reading photos you upload "
            "are <strong>deleted immediately after analysis</strong> and are not stored. "
            "We do not sell your data to third parties. You can completely delete your history and "
            "your account from within the app whenever you wish."
        ),
        "sections": [
            ("Data we collect", [
                "Account: email address (via Supabase Auth). Profile: your name (optional), birth "
                "date/time/place, and your language and interest preferences. Content: the analyses you "
                "generate (birth chart, tarot, readings, relationship compatibility), your AI chat history, "
                "and context records made up of short summaries of these (Cosmic Memory).",
            ]),
            ("Photos", [
                "Photos you upload for coffee/palm/face readings are processed on the server only for the "
                "duration of the analysis and are <strong>permanently deleted as soon as the analysis "
                "is complete</strong>. Photos are not stored; only the text result and the list of "
                "symbols are kept in the archive.",
            ]),
            ("How your data is processed", [
                "Astrological calculations are performed on our server (Swiss Ephemeris). For "
                "personalized interpretations, your content is sent to AI providers (OpenAI and Google "
                "Gemini) solely for the purpose of generating interpretations. API keys are kept only on "
                "the server; they are not present in the app.",
            ]),
            ("Retention and deletion", [
                "You can delete your data at any time: with <em>Profile → My Data → Delete memory / "
                "history</em> you can remove your analysis and chat history; with <em>Permanently delete "
                "account</em> you can permanently remove all your data and your account. When an account "
                "is deleted, all associated records are deleted irreversibly.",
            ]),
            ("Sharing", [
                "We do not sell or rent your data for advertising purposes. We process it only with the "
                "infrastructure providers necessary to provide the service (authentication, database, "
                "AI interpretation, subscription management).",
            ]),
            ("Exercising your rights (KVKK/GDPR)", [
                "You have the right to access, correct, and delete your data and to restrict its "
                "processing. For your request, you can write to {contact_link}.",
            ]),
            ("Children", [
                "Astrype is not intended for users under the age of 13.",
            ]),
            ("Open source", [
                "The source code of the Astrype server software is publicly available under the "
                "{license} license: {source_link}. The source code does not contain any user data or "
                "secret keys.",
            ]),
        ],
    },
    "terms": {
        "title": "Terms of Use",
        "note": (
            "<strong>Important:</strong> The astrology, tarot, coffee/palm/face reading and dream "
            "interpretations in Astrype are <strong>for entertainment and personal insight "
            "only</strong>. They are not a substitute for professional support for medical, legal, "
            "financial or safety-critical decisions. Your AI guide (Lyra) does not make definitive "
            "statements about fate or the future."
        ),
        "sections": [
            ("Nature of the service", [
                "Astrype offers a birth chart, daily/monthly interpretations, tarot, fortune-telling "
                "modules and an AI chat assistant that knows your history. The content is for personal "
                "reflection and insight; it makes no claim of scientific or definitive truth.",
            ]),
            ("Disclaimer", [
                "You are responsible for the decisions you make based on the interpretations in the app. "
                "In health, legal, financial or crisis situations, please consult a relevant professional.",
            ]),
            ("Subscription", [
                "Premium features require a subscription. Payment, renewal and cancellation are managed "
                "through the Apple App Store or Google Play. The subscription renews automatically unless "
                "you cancel it before the end of the period; you can cancel from your store account. "
                "Purchases can be restored using \"Restore purchases\".",
            ]),
            ("Acceptable use", [
                "You may not use the service for illegal purposes, in a way that infringes the rights of "
                "others, or by abusing the system.",
            ]),
            ("Changes", [
                "We may update these terms from time to time. We will announce significant changes "
                "within the app.",
            ]),
            ("Open source / Source code", [
                "Astrype's server (backend) software is open source and is published under the "
                "<strong>{license}</strong> license. Every user who interacts with this service over a "
                "network can access, free of charge, the complete source code of the software running "
                "the service, and can inspect it, modify it and redistribute it under the terms of the "
                "license:",
                "{source_link}",
                "Permanent link: {source_path_link}. Astrological calculations use Astrodienst AG's "
                "Swiss Ephemeris library (under the AGPL option) and Kerykeion; third-party licenses are "
                "listed in the <code>THIRD_PARTY_LICENSES.md</code> file in the repository. The license "
                "states that the software is provided \"as is\" and without any warranty. This section "
                "covers only the source code of the server software; the Astrype name and logo are not a "
                "trademark license granted under this license.",
            ]),
            ("Contact", [
                "For questions: {contact_link}",
            ]),
        ],
    },
}

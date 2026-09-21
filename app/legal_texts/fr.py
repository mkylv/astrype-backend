"""French legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Français",
    "dir": "ltr",
    "updated_label": "Dernière mise à jour",
    "updated": "14 juillet 2026",
    "contact_label": "Contact",
    "languages_label": "Langue",
    "translation_notice": (
        "Cette traduction est fournie uniquement à titre indicatif. En cas de divergence, "
        "la version turque prévaut."
    ),
    "privacy": {
        "title": "Politique de confidentialité",
        "note": (
            "<strong>Résumé :</strong> Nous utilisons tes données uniquement pour créer des contenus "
            "d'astrologie et de voyance personnalisés pour toi. Les photos que tu importes pour la lecture "
            "du marc de café, des lignes de la main ou du visage sont <strong>supprimées immédiatement "
            "après l'analyse</strong> et ne sont pas conservées. Nous ne vendons pas tes données à des "
            "tiers. Tu peux supprimer entièrement ton historique et ton compte depuis l'application quand "
            "tu le souhaites."
        ),
        "sections": [
            ("Données que nous collectons", [
                "Compte : adresse e-mail (via Supabase Auth). Profil : ton nom (facultatif), ta date, ton "
                "heure et ton lieu de naissance, ainsi que tes préférences de langue et de centres "
                "d'intérêt. Contenu : les analyses que tu génères (thème natal, tarot, lectures, "
                "compatibilité amoureuse), ton historique de discussion avec l'IA et des enregistrements de "
                "contexte composés de courts résumés de ces éléments (Cosmic Memory).",
            ]),
            ("Photos", [
                "Les photos que tu importes pour la lecture du marc de café, des lignes de la main ou du "
                "visage sont traitées sur le serveur uniquement pendant la durée de l'analyse et sont "
                "<strong>définitivement supprimées dès la fin de l'analyse</strong>. Les photos ne sont pas "
                "conservées ; seuls le résultat textuel et la liste des symboles sont gardés dans "
                "l'archive.",
            ]),
            ("Comment tes données sont traitées", [
                "Les calculs astrologiques sont effectués sur notre serveur (Swiss Ephemeris). Pour les "
                "interprétations personnalisées, ton contenu est transmis à des fournisseurs d'IA (OpenAI "
                "et Google Gemini) dans le seul but de générer des interprétations. Les clés API sont "
                "conservées uniquement sur le serveur ; elles ne se trouvent pas dans l'application.",
            ]),
            ("Conservation et suppression", [
                "Tu peux supprimer tes données à tout moment : avec <em>Profil → Mes données → Effacer "
                "mémoire / historique</em>, tu peux supprimer ton historique d'analyses et de discussions ; "
                "avec <em>Supprimer le compte définitivement</em>, tu peux supprimer définitivement toutes "
                "tes données et ton compte. Lorsqu'un compte est supprimé, tous les enregistrements "
                "associés sont supprimés de manière irréversible.",
            ]),
            ("Partage", [
                "Nous ne vendons ni ne louons tes données à des fins publicitaires. Nous les traitons "
                "uniquement avec les fournisseurs d'infrastructure nécessaires à la fourniture du service "
                "(authentification, base de données, interprétation par IA, gestion des abonnements).",
            ]),
            ("Exercer tes droits (KVKK/GDPR)", [
                "Tu as le droit d'accéder à tes données, de les rectifier, de les supprimer et d'en limiter "
                "le traitement. Pour ta demande, tu peux écrire à {contact_link}.",
            ]),
            ("Enfants", [
                "Astrype n'est pas destiné aux utilisateurs de moins de 13 ans.",
            ]),
            ("Open source", [
                "Le code source du logiciel serveur d'Astrype est accessible publiquement sous licence "
                "{license} : {source_link}. Le code source ne contient aucune donnée utilisateur ni aucune "
                "clé secrète.",
            ]),
        ],
    },
    "terms": {
        "title": "Conditions d'utilisation",
        "note": (
            "<strong>Important :</strong> Les interprétations d'astrologie, de tarot, de lecture du marc "
            "de café, des lignes de la main ou du visage et des rêves proposées dans Astrype sont "
            "<strong>destinées uniquement au divertissement et à l'introspection personnelle</strong>. "
            "Elles ne remplacent pas un accompagnement professionnel pour les décisions médicales, "
            "juridiques, financières ou critiques en matière de sécurité. Ton guide IA (Lyra) ne fait "
            "aucune affirmation catégorique sur le destin ou l'avenir."
        ),
        "sections": [
            ("Nature du service", [
                "Astrype propose un thème natal, des interprétations quotidiennes/mensuelles, le tarot, des "
                "modules de voyance et un assistant de discussion IA qui connaît ton historique. Les "
                "contenus sont destinés à la réflexion et à l'introspection personnelles ; ils ne "
                "prétendent à aucune vérité scientifique ou définitive.",
            ]),
            ("Clause de non-responsabilité", [
                "Tu es responsable des décisions que tu prends sur la base des interprétations de "
                "l'application. En cas de questions de santé, juridiques, financières ou de situation de "
                "crise, consulte un professionnel compétent.",
            ]),
            ("Abonnement", [
                "Les fonctionnalités Premium nécessitent un abonnement. Le paiement, le renouvellement et "
                "la résiliation sont gérés via l'Apple App Store ou Google Play. L'abonnement se renouvelle "
                "automatiquement sauf si tu le résilies avant la fin de la période ; tu peux le résilier "
                "depuis ton compte de la boutique. Les achats peuvent être restaurés via \"Restaurer les "
                "achats\".",
            ]),
            ("Utilisation acceptable", [
                "Tu ne peux pas utiliser le service à des fins illégales, d'une manière qui porte atteinte "
                "aux droits d'autrui, ni en abusant du système.",
            ]),
            ("Modifications", [
                "Nous pouvons mettre à jour ces conditions de temps à autre. Nous annoncerons les "
                "changements importants dans l'application.",
            ]),
            ("Open source / Code source", [
                "Le logiciel serveur (backend) d'Astrype est open source et publié sous licence "
                "<strong>{license}</strong>. Tout utilisateur qui interagit avec ce service via un réseau "
                "peut accéder gratuitement au code source complet du logiciel qui fait fonctionner le "
                "service, l'examiner, le modifier et le redistribuer dans le respect des conditions de la "
                "licence :",
                "{source_link}",
                "Lien permanent : {source_path_link}. Les calculs astrologiques utilisent la bibliothèque "
                "Swiss Ephemeris d'Astrodienst AG (sous l'option AGPL) et Kerykeion ; les licences tierces "
                "sont répertoriées dans le fichier <code>THIRD_PARTY_LICENSES.md</code> du dépôt. La "
                "licence précise que le logiciel est fourni \"en l'état\" et sans aucune garantie. Cette "
                "section couvre uniquement le code source du logiciel serveur ; le nom et le logo "
                "d'Astrype ne constituent pas un droit d'utilisation de marque accordé par cette licence.",
            ]),
            ("Contact", [
                "Pour toute question : {contact_link}",
            ]),
        ],
    },
}

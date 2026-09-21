"""Italian legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Italiano",
    "dir": "ltr",
    "updated_label": "Ultimo aggiornamento",
    "updated": "14 luglio 2026",
    "contact_label": "Contatti",
    "languages_label": "Lingua",
    "translation_notice": (
        "Questa traduzione è fornita solo per comodità. In caso di discrepanze, "
        "prevale la versione turca."
    ),
    "privacy": {
        "title": "Informativa sulla privacy",
        "note": (
            "<strong>In sintesi:</strong> Usiamo i tuoi dati solo per creare per te contenuti "
            "personalizzati di astrologia e divinazione. Le foto che carichi per la lettura dei fondi di "
            "caffè, della mano o del viso vengono <strong>eliminate subito dopo l'analisi</strong> e non "
            "vengono conservate. Non vendiamo i tuoi dati a terzi. Puoi eliminare completamente la tua "
            "cronologia e il tuo account dall'app in qualsiasi momento."
        ),
        "sections": [
            ("Dati che raccogliamo", [
                "Account: indirizzo email (tramite Supabase Auth). Profilo: il tuo nome (facoltativo), "
                "data/ora/luogo di nascita e le tue preferenze di lingua e interessi. Contenuti: le analisi "
                "che generi (tema natale, tarocchi, letture, compatibilità di coppia), la cronologia delle "
                "chat con l'IA e i record di contesto costituiti da brevi riepiloghi di questi elementi "
                "(Cosmic Memory).",
            ]),
            ("Foto", [
                "Le foto che carichi per la lettura dei fondi di caffè, della mano o del viso vengono "
                "elaborate sul server solo per la durata dell'analisi e vengono <strong>eliminate "
                "definitivamente non appena l'analisi è terminata</strong>. Le foto non vengono conservate; "
                "nell'archivio vengono mantenuti solo il risultato testuale e l'elenco dei simboli.",
            ]),
            ("Come vengono trattati i tuoi dati", [
                "I calcoli astrologici vengono eseguiti sul nostro server (Swiss Ephemeris). Per le "
                "interpretazioni personalizzate, i tuoi contenuti vengono inviati a fornitori di IA (OpenAI "
                "e Google Gemini) al solo scopo di generare le interpretazioni. Le chiavi API sono "
                "conservate solo sul server; non sono presenti nell'app.",
            ]),
            ("Conservazione ed eliminazione", [
                "Puoi eliminare i tuoi dati in qualsiasi momento: con <em>Profilo → I miei dati → Elimina "
                "memoria / cronologia</em> puoi rimuovere la cronologia di analisi e chat; con <em>Elimina "
                "l'account definitivamente</em> puoi rimuovere in modo permanente tutti i tuoi dati e il "
                "tuo account. Quando un account viene eliminato, tutti i record associati vengono eliminati "
                "in modo irreversibile.",
            ]),
            ("Condivisione", [
                "Non vendiamo né affittiamo i tuoi dati per scopi pubblicitari. Li trattiamo solo con i "
                "fornitori di infrastruttura necessari per fornire il servizio (autenticazione, database, "
                "interpretazione tramite IA, gestione degli abbonamenti).",
            ]),
            ("Esercitare i tuoi diritti (KVKK/GDPR)", [
                "Hai il diritto di accedere ai tuoi dati, rettificarli, cancellarli e limitarne il "
                "trattamento. Per la tua richiesta puoi scrivere a {contact_link}.",
            ]),
            ("Minori", [
                "Astrype non è destinata a utenti di età inferiore ai 13 anni.",
            ]),
            ("Open source", [
                "Il codice sorgente del software server di Astrype è pubblicamente disponibile con licenza "
                "{license}: {source_link}. Il codice sorgente non contiene dati degli utenti né chiavi "
                "segrete.",
            ]),
        ],
    },
    "terms": {
        "title": "Termini d'uso",
        "note": (
            "<strong>Importante:</strong> Le interpretazioni di astrologia, tarocchi, lettura dei fondi "
            "di caffè, della mano o del viso e dei sogni presenti in Astrype sono <strong>solo a scopo di "
            "intrattenimento e di introspezione personale</strong>. Non sostituiscono il supporto di "
            "professionisti per decisioni mediche, legali, finanziarie o critiche per la sicurezza. La tua "
            "guida IA (Lyra) non fa affermazioni definitive sul destino o sul futuro."
        ),
        "sections": [
            ("Natura del servizio", [
                "Astrype offre il tema natale, interpretazioni giornaliere/mensili, i tarocchi, moduli di "
                "divinazione e un assistente di chat IA che conosce la tua cronologia. I contenuti sono "
                "pensati per la riflessione e l'introspezione personale; non pretendono di esprimere verità "
                "scientifiche o definitive.",
            ]),
            ("Esclusione di responsabilità", [
                "Sei responsabile delle decisioni che prendi sulla base delle interpretazioni dell'app. In "
                "situazioni di salute, legali, finanziarie o di crisi, rivolgiti a un professionista "
                "competente.",
            ]),
            ("Abbonamento", [
                "Le funzionalità Premium richiedono un abbonamento. Pagamento, rinnovo e disdetta sono "
                "gestiti tramite Apple App Store o Google Play. L'abbonamento si rinnova automaticamente a "
                "meno che tu non lo disdica prima della fine del periodo; puoi disdirlo dal tuo account "
                "dello store. Gli acquisti possono essere ripristinati tramite \"Ripristina acquisti\".",
            ]),
            ("Uso consentito", [
                "Non puoi utilizzare il servizio per scopi illegali, in modo da violare i diritti altrui o "
                "abusando del sistema.",
            ]),
            ("Modifiche", [
                "Possiamo aggiornare questi termini di tanto in tanto. Comunicheremo le modifiche "
                "importanti all'interno dell'app.",
            ]),
            ("Open source / Codice sorgente", [
                "Il software server (backend) di Astrype è open source ed è pubblicato con licenza "
                "<strong>{license}</strong>. Ogni utente che interagisce con questo servizio tramite una "
                "rete può accedere gratuitamente al codice sorgente completo del software che fa funzionare "
                "il servizio, esaminarlo, modificarlo e ridistribuirlo nel rispetto dei termini della "
                "licenza:",
                "{source_link}",
                "Link permanente: {source_path_link}. I calcoli astrologici utilizzano la libreria Swiss "
                "Ephemeris di Astrodienst AG (con l'opzione AGPL) e Kerykeion; le licenze di terze parti "
                "sono elencate nel file <code>THIRD_PARTY_LICENSES.md</code> del repository. La licenza "
                "stabilisce che il software è fornito \"così com'è\" e senza alcuna garanzia. Questa "
                "sezione riguarda solo il codice sorgente del software server; il nome e il logo di Astrype "
                "non costituiscono un diritto d'uso del marchio concesso con questa licenza.",
            ]),
            ("Contatti", [
                "Per domande: {contact_link}",
            ]),
        ],
    },
}

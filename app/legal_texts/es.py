"""Spanish legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Español",
    "dir": "ltr",
    "updated_label": "Última actualización",
    "updated": "14 de julio de 2026",
    "contact_label": "Contacto",
    "languages_label": "Idioma",
    "translation_notice": (
        "Esta traducción se ofrece únicamente por comodidad. En caso de conflicto, "
        "prevalece la versión en turco."
    ),
    "privacy": {
        "title": "Política de Privacidad",
        "note": (
            "<strong>Resumen:</strong> Usamos tus datos únicamente para crear contenido "
            "personalizado de astrología y adivinación para ti. Las fotos de lectura del café, "
            "de la mano o del rostro que subes se <strong>eliminan inmediatamente después del "
            "análisis</strong> y no se guardan. No vendemos tus datos a terceros. Puedes eliminar "
            "por completo tu historial y tu cuenta desde la aplicación cuando quieras."
        ),
        "sections": [
            ("Datos que recopilamos", [
                "Cuenta: dirección de correo electrónico (mediante Supabase Auth). Perfil: tu nombre "
                "(opcional), fecha/hora/lugar de nacimiento y tus preferencias de idioma e intereses. "
                "Contenido: los análisis que generas (carta natal, tarot, lecturas, compatibilidad de "
                "pareja), tu historial de chat con la inteligencia artificial y los registros de contexto "
                "compuestos por breves resúmenes de estos (Cosmic Memory).",
            ]),
            ("Fotos", [
                "Las fotos que subes para la lectura del café, de la mano o del rostro se procesan en el "
                "servidor solo durante el análisis y se <strong>eliminan de forma permanente en cuanto "
                "termina el análisis</strong>. Las fotos no se guardan; en el archivo solo se conservan "
                "el resultado en texto y la lista de símbolos.",
            ]),
            ("Cómo se tratan tus datos", [
                "Los cálculos astrológicos se realizan en nuestro servidor (Swiss Ephemeris). Para las "
                "interpretaciones personalizadas, tu contenido se envía a proveedores de inteligencia "
                "artificial (OpenAI y Google Gemini) únicamente con el fin de generar interpretaciones. "
                "Las claves de API se guardan solo en el servidor; no están en la aplicación.",
            ]),
            ("Conservación y eliminación", [
                "Puedes eliminar tus datos en cualquier momento: con <em>Perfil → Mis datos → Borrar "
                "memoria / historial</em> puedes eliminar tu historial de análisis y de chat; con "
                "<em>Eliminar la cuenta permanentemente</em> puedes eliminar de forma permanente todos "
                "tus datos y tu cuenta. Cuando se elimina una cuenta, todos los registros asociados se "
                "eliminan de forma irreversible.",
            ]),
            ("Compartición", [
                "No vendemos ni alquilamos tus datos con fines publicitarios. Solo los tratamos con los "
                "proveedores de infraestructura necesarios para prestar el servicio (autenticación, base "
                "de datos, interpretación por inteligencia artificial, gestión de suscripciones).",
            ]),
            ("Ejercicio de tus derechos (KVKK/GDPR)", [
                "Tienes derecho a acceder a tus datos, rectificarlos, eliminarlos y limitar su "
                "tratamiento. Para tu solicitud, puedes escribir a {contact_link}.",
            ]),
            ("Menores", [
                "Astrype no está dirigida a usuarios menores de 13 años.",
            ]),
            ("Código abierto", [
                "El código fuente del software de servidor de Astrype está disponible públicamente bajo "
                "la licencia {license}: {source_link}. El código fuente no contiene ningún dato de "
                "usuario ni claves secretas.",
            ]),
        ],
    },
    "terms": {
        "title": "Términos de Uso",
        "note": (
            "<strong>Importante:</strong> Las interpretaciones de astrología, tarot, lectura del café, "
            "de la mano o del rostro y de sueños en Astrype tienen <strong>únicamente fines de "
            "entretenimiento y reflexión personal</strong>. No sustituyen el apoyo profesional en "
            "decisiones médicas, legales, financieras o críticas para la seguridad. Tu guía de "
            "inteligencia artificial (Lyra) no hace afirmaciones definitivas sobre el destino o el futuro."
        ),
        "sections": [
            ("Naturaleza del servicio", [
                "Astrype ofrece carta natal, interpretaciones diarias/mensuales, tarot, módulos de "
                "adivinación y un asistente de chat con inteligencia artificial que conoce tu historial. "
                "El contenido es para la reflexión y el conocimiento personal; no pretende ser una verdad "
                "científica ni definitiva.",
            ]),
            ("Exención de responsabilidad", [
                "Eres responsable de las decisiones que tomes basándote en las interpretaciones de la "
                "aplicación. En situaciones de salud, legales, financieras o de crisis, consulta a un "
                "profesional adecuado.",
            ]),
            ("Suscripción", [
                "Las funciones Premium requieren una suscripción. El pago, la renovación y la cancelación "
                "se gestionan a través de Apple App Store o Google Play. La suscripción se renueva "
                "automáticamente a menos que la canceles antes del final del período; puedes cancelarla "
                "desde tu cuenta de la tienda. Las compras pueden restaurarse con \"Restaurar compras\".",
            ]),
            ("Uso aceptable", [
                "No puedes usar el servicio con fines ilegales, de forma que vulnere los derechos de "
                "otras personas ni abusando del sistema.",
            ]),
            ("Cambios", [
                "Podemos actualizar estos términos de vez en cuando. Anunciaremos los cambios importantes "
                "dentro de la aplicación.",
            ]),
            ("Código abierto / Código fuente", [
                "El software de servidor (backend) de Astrype es de código abierto y se publica bajo la "
                "licencia <strong>{license}</strong>. Todo usuario que interactúe con este servicio a "
                "través de una red puede acceder de forma gratuita al código fuente completo del software "
                "que ejecuta el servicio, examinarlo, modificarlo y redistribuirlo conforme a los términos "
                "de la licencia:",
                "{source_link}",
                "Enlace permanente: {source_path_link}. Los cálculos astrológicos utilizan la biblioteca "
                "Swiss Ephemeris de Astrodienst AG (con la opción AGPL) y Kerykeion; las licencias de "
                "terceros se enumeran en el archivo <code>THIRD_PARTY_LICENSES.md</code> del repositorio. "
                "La licencia establece que el software se proporciona \"tal cual\" y sin garantía de "
                "ningún tipo. Esta sección abarca únicamente el código fuente del software de servidor; "
                "el nombre y el logotipo de Astrype no constituyen un derecho de uso de marca otorgado "
                "mediante esta licencia.",
            ]),
            ("Contacto", [
                "Para preguntas: {contact_link}",
            ]),
        ],
    },
}

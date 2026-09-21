"""Azerbaijani legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Azərbaycanca",
    "dir": "ltr",
    "updated_label": "Son yenilənmə",
    "updated": "14 iyul 2026",
    "contact_label": "Əlaqə",
    "languages_label": "Dil",
    "translation_notice": (
        "Bu tərcümə yalnız rahatlıq üçün təqdim olunur. Hər hansı ziddiyyət olduqda "
        "türkcə versiya üstünlük təşkil edir."
    ),
    "privacy": {
        "title": "Məxfilik Siyasəti",
        "note": (
            "<strong>Qısaca:</strong> Məlumatlarından yalnız sənin üçün fərdiləşdirilmiş "
            "astrologiya/fal məzmunu yaratmaq üçün istifadə edirik. Yüklədiyin qəhvə/əl/üz falı "
            "fotoşəkilləri <strong>təhlildən dərhal sonra silinir</strong>, saxlanılmır. "
            "Məlumatlarını üçüncü tərəflərə satmırıq. İstədiyin vaxt tarixçəni və hesabını tətbiqin "
            "içindən tamamilə silə bilərsən."
        ),
        "sections": [
            ("Topladığımız məlumatlar", [
                "Hesab: e-poçt ünvanı (Supabase Auth vasitəsilə). Profil: adın (istəyə bağlı), doğum "
                "tarixi/saatı/yeri, dil və maraq sahəsi seçimlərin. Məzmun: yaratdığın təhlillər "
                "(natal xəritə, tarot, fal, münasibət uyğunluğu), süni intellekt söhbət tarixçən və "
                "bunların qısa xülasələrindən ibarət kontekst qeydləri (Cosmic Memory).",
            ]),
            ("Fotoşəkillər", [
                "Qəhvə/əl/üz falı üçün yüklədiyin fotoşəkillər serverdə yalnız təhlil müddətində "
                "emal olunur və <strong>təhlil bitən kimi həmişəlik silinir</strong>. Fotoşəkil "
                "saxlanılmır; arxivdə yalnız mətn nəticəsi və simvol siyahısı saxlanılır.",
            ]),
            ("Məlumatların necə emal olunur", [
                "Astroloji hesablamalar serverimizdə (Swiss Ephemeris) aparılır. Fərdiləşdirilmiş "
                "yozumlar üçün məzmunun süni intellekt provayderlərinə (OpenAI və Google Gemini) "
                "yalnız yozum yaratmaq məqsədilə ötürülür. API açarları yalnız serverdə saxlanılır; "
                "tətbiqdə yoxdur.",
            ]),
            ("Saxlama və silmə", [
                "Məlumatlarını istədiyin an silə bilərsən: <em>Profil → Məlumatlarım → Yaddaşı / "
                "tarixçəni sil</em> ilə təhlil və söhbət tarixçəni; <em>Hesabı həmişəlik sil</em> ilə "
                "bütün məlumatlarını və hesabını həmişəlik silə bilərsən. Hesab silindikdə əlaqəli "
                "bütün qeydlər geri qaytarılmaz şəkildə silinir.",
            ]),
            ("Paylaşım", [
                "Məlumatlarını reklam məqsədilə satmırıq və ya icarəyə vermirik. Onları yalnız "
                "xidməti təmin etmək üçün zəruri olan infrastruktur provayderləri ilə (kimlik "
                "doğrulama, verilənlər bazası, süni intellektlə yozum, abunə idarəetməsi) emal edirik.",
            ]),
            ("Hüquqlarından istifadə (KVKK/GDPR)", [
                "Məlumatlarına çıxış, onları düzəltmək, silmək və emalını məhdudlaşdırmaq hüquqların "
                "var. Sorğun üçün {contact_link} ünvanına yaza bilərsən.",
            ]),
            ("Uşaqlar", [
                "Astrype 13 yaşdan kiçik istifadəçilər üçün nəzərdə tutulmayıb.",
            ]),
            ("Açıq mənbə", [
                "Astrype server proqram təminatının mənbə kodu {license} lisenziyası ilə hamıya "
                "açıqdır: {source_link}. Mənbə kodu heç bir istifadəçi məlumatı və ya gizli açar "
                "ehtiva etmir.",
            ]),
        ],
    },
    "terms": {
        "title": "İstifadə Şərtləri",
        "note": (
            "<strong>Vacib:</strong> Astrype-dakı astrologiya, tarot, qəhvə/əl/üz falı və yuxu "
            "yozumları <strong>yalnız əyləncə və şəxsi dərketmə</strong> məqsədi daşıyır. Tibbi, "
            "hüquqi, maliyyə və ya təhlükəsizlik baxımından kritik qərarlar üçün peşəkar dəstəyi "
            "əvəz etmir. Süni intellekt bələdçin (Lyra) qəti tale/gələcək bəyanatı vermir."
        ),
        "sections": [
            ("Xidmətin mahiyyəti", [
                "Astrype natal xəritə, gündəlik/aylıq yozum, tarot, fal modulları və tarixçəni bilən "
                "süni intellekt söhbət köməkçisi təqdim edir. Məzmun şəxsi düşüncə və dərketmə "
                "üçündür; elmi/qəti həqiqət iddiası daşımır.",
            ]),
            ("Məsuliyyətdən imtina", [
                "Tətbiqdəki yozumlara əsaslanaraq qəbul etdiyin qərarlara görə məsuliyyət sənin "
                "üzərindədir. Sağlamlıq, hüquq, maliyyə və ya böhran vəziyyətlərində lütfən müvafiq "
                "mütəxəssisə müraciət et.",
            ]),
            ("Abunəlik", [
                "Premium funksiyalar abunəlik tələb edir. Ödəniş, yenilənmə və ləğv əməliyyatları "
                "Apple App Store və ya Google Play vasitəsilə idarə olunur. Abunəlik dövrün sonunda "
                "ləğv etmədiyin təqdirdə avtomatik yenilənir; ləğvi mağaza hesabından edə bilərsən. "
                "Alışlar \"Alışları bərpa et\" funksiyası ilə bərpa oluna bilər.",
            ]),
            ("Qəbul edilən istifadə", [
                "Xidmətdən qanunsuz məqsədlərlə, başqalarının hüquqlarını pozacaq şəkildə və ya "
                "sistemdən sui-istifadə edərək istifadə edə bilməzsən.",
            ]),
            ("Dəyişikliklər", [
                "Bu şərtləri vaxtaşırı yeniləyə bilərik. Əhəmiyyətli dəyişiklikləri tətbiqin "
                "içindən elan edəcəyik.",
            ]),
            ("Açıq mənbə / Mənbə kodu", [
                "Astrype-ın server (backend) proqram təminatı açıq mənbəlidir və "
                "<strong>{license}</strong> lisenziyası altında yayımlanır. Bu xidmətlə şəbəkə "
                "üzərindən qarşılıqlı əlaqədə olan hər bir istifadəçi xidməti işlədən proqram "
                "təminatının tam mənbə koduna pulsuz çıxış əldə edə, onu nəzərdən keçirə, dəyişdirə "
                "və lisenziya şərtləri çərçivəsində yenidən yaya bilər:",
                "{source_link}",
                "Daimi keçid: {source_path_link}. Astroloji hesablamalar Astrodienst AG-nin Swiss "
                "Ephemeris kitabxanasından (AGPL seçimi ilə) və Kerykeion-dan istifadə edir; üçüncü "
                "tərəf lisenziyaları repozitoriyadakı <code>THIRD_PARTY_LICENSES.md</code> faylında "
                "sadalanır. Lisenziya proqram təminatının \"olduğu kimi\" və heç bir zəmanət olmadan "
                "təqdim edildiyini bildirir. Bu bölmə yalnız server proqram təminatının mənbə kodunu "
                "əhatə edir; Astrype adı və loqosu bu lisenziya ilə verilmiş əmtəə nişanından istifadə "
                "hüququ deyil.",
            ]),
            ("Əlaqə", [
                "Suallar üçün: {contact_link}",
            ]),
        ],
    },
}

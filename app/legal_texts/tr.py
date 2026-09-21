"""Türkçe yasal metinler — KAYNAK METİN (source of truth).

Diğer dillerdeki dosyalar bu metnin çevirisidir. Bu dosyada yapılan her anlam
değişikliği tüm dillere yansıtılmalıdır (bölüm/paragraf sayıları testle
karşılaştırılır: tests/test_legal_i18n.py).

Yer tutucular (şablon tarafından doldurulur, çevirilerde aynen korunmalı):
  {contact_link}      -> mailto destek bağlantısı
  {source_link}       -> backend kaynak kodu (GitHub) bağlantısı
  {source_path_link}  -> kalıcı /legal/source bağlantısı
  {license}           -> lisans adı (AGPL-3.0)
Metinlerde güvenilir, sınırlı HTML kullanılır (<strong>, <em>, <code>).
"""

TEXT = {
    "native_name": "Türkçe",
    "dir": "ltr",
    "updated_label": "Son güncelleme",
    "updated": "14 Temmuz 2026",
    "contact_label": "İletişim",
    "languages_label": "Dil",
    # Türkçe kaynak metin olduğu için çeviri uyarısı gösterilmez.
    "translation_notice": "",
    "privacy": {
        "title": "Gizlilik Politikası",
        "note": (
            "<strong>Özet:</strong> Verini yalnızca sana kişiselleştirilmiş "
            "astroloji/fal içeriği üretmek için kullanırız. Yüklediğin kahve/el/yüz falı "
            "fotoğrafları <strong>analizden hemen sonra silinir</strong>, saklanmaz. "
            "Verini üçüncü taraflara satmayız. Dilediğinde geçmişini ve hesabını uygulama "
            "içinden tamamen silebilirsin."
        ),
        "sections": [
            ("Topladığımız veriler", [
                "Hesap: e-posta adresi (Supabase Auth ile). Profil: adın (opsiyonel), doğum "
                "tarihi/saati/yeri, dil ve ilgi alanı tercihlerin. İçerik: ürettiğin analizler "
                "(doğum haritası, tarot, fal, ilişki uyumu), yapay zekâ sohbet geçmişin ve bunların "
                "kısa özetlerinden oluşan bağlam kayıtları (Cosmic Memory).",
            ]),
            ("Fotoğraflar", [
                "Kahve/el/yüz falı için yüklediğin fotoğraflar sunucuda yalnızca analiz süresince "
                "işlenir ve <strong>analiz biter bitmez kalıcı olarak silinir</strong>. Fotoğraf "
                "saklanmaz; arşivde yalnızca metin sonucu ve sembol listesi tutulur.",
            ]),
            ("Verilerin nasıl işlenir", [
                "Astrolojik hesaplamalar sunucumuzda (Swiss Ephemeris) yapılır. Kişiselleştirilmiş "
                "yorumlar için içeriğin, yapay zekâ sağlayıcılarına (OpenAI ve Google Gemini) yalnızca "
                "yorum üretimi amacıyla iletilir. API anahtarları yalnızca sunucuda tutulur; uygulamada "
                "bulunmaz.",
            ]),
            ("Saklama ve silme", [
                "Verilerini istediğin an silebilirsin: <em>Profil → Verilerim → Hafızayı/geçmişi sil</em> "
                "ile analiz ve sohbet geçmişini; <em>Hesabı sil</em> ile tüm verini ve hesabını kalıcı "
                "olarak kaldırabilirsin. Hesap silindiğinde ilişkili tüm kayıtlar geri döndürülemez "
                "şekilde silinir.",
            ]),
            ("Paylaşım", [
                "Verini reklam amacıyla satmayız veya kiralamayız. Yalnızca hizmeti sağlamak için "
                "gerekli altyapı sağlayıcılarıyla (kimlik doğrulama, veritabanı, yapay zekâ yorumlama, "
                "abonelik yönetimi) işleriz.",
            ]),
            ("Haklarını kullanma (KVKK/GDPR)", [
                "Verine erişme, düzeltme, silme ve işlemeyi sınırlama haklarına sahipsin. Talebin "
                "için {contact_link} adresine yazabilirsin.",
            ]),
            ("Çocuklar", [
                "Astrype 13 yaşın altındaki kullanıcılara yönelik değildir.",
            ]),
            ("Açık kaynak", [
                "Astrype sunucu yazılımının kaynak kodu {license} lisansıyla herkese açıktır: "
                "{source_link}. Kaynak kodu hiçbir kullanıcı verisi veya gizli anahtar içermez.",
            ]),
        ],
    },
    "terms": {
        "title": "Kullanım Şartları",
        "note": (
            "<strong>Önemli:</strong> Astrype'taki astroloji, tarot, kahve/el/yüz "
            "falı ve rüya yorumları <strong>yalnızca eğlence ve kişisel içgörü</strong> amaçlıdır. "
            "Tıbbi, hukuki, finansal veya güvenlik açısından kritik kararlar için profesyonel "
            "destek yerine geçmez. Yapay zekâ rehberin (Lyra) kesin kader/gelecek beyanı vermez."
        ),
        "sections": [
            ("Hizmetin niteliği", [
                "Astrype; doğum haritası, günlük/aylık yorum, tarot, fal modülleri ve geçmişini bilen "
                "bir yapay zekâ sohbet asistanı sunar. İçerikler kişisel düşünce ve içgörü içindir; "
                "bilimsel/kesin gerçeklik iddiası taşımaz.",
            ]),
            ("Sorumluluk reddi", [
                "Uygulamadaki yorumlara dayanarak aldığın kararlardan sen sorumlusun. Sağlık, hukuk, "
                "finans veya kriz durumlarında lütfen ilgili uzmana başvur.",
            ]),
            ("Abonelik", [
                "Premium özellikler abonelik gerektirir. Ödeme, yenileme ve iptal işlemleri Apple "
                "App Store veya Google Play üzerinden yönetilir. Abonelik, dönem sonunda iptal etmediğin "
                "sürece otomatik yenilenir; iptali mağaza hesabından yapabilirsin. Satın alımlar "
                "\"Satın alımları geri yükle\" ile geri yüklenebilir.",
            ]),
            ("Kabul edilebilir kullanım", [
                "Hizmeti yasa dışı amaçlarla, başkalarının haklarını ihlal edecek şekilde veya "
                "sistemi kötüye kullanarak kullanamazsın.",
            ]),
            ("Değişiklikler", [
                "Bu şartları zaman zaman güncelleyebiliriz. Önemli değişiklikleri uygulama içinden "
                "duyururuz.",
            ]),
            ("Açık kaynak / Kaynak kodu", [
                "Astrype'ın sunucu (backend) yazılımı açık kaynaktır ve "
                "<strong>{license}</strong> lisansı altında yayınlanır. Bu hizmetle ağ üzerinden "
                "etkileşime giren her kullanıcı, hizmeti çalıştıran yazılımın tam kaynak koduna "
                "ücretsiz olarak erişebilir, onu inceleyebilir, değiştirebilir ve lisans koşulları "
                "çerçevesinde yeniden dağıtabilir:",
                "{source_link}",
                "Kalıcı bağlantı: {source_path_link}. Astroloji hesaplamaları, "
                "Astrodienst AG'nin Swiss Ephemeris kütüphanesini (AGPL seçeneğiyle) ve Kerykeion'u "
                "kullanır; üçüncü taraf lisansları depodaki <code>THIRD_PARTY_LICENSES.md</code> "
                "dosyasında listelenir. Lisans, yazılımın \"olduğu gibi\" ve herhangi bir garanti "
                "olmaksızın sunulduğunu belirtir. Bu bölüm yalnızca sunucu yazılımının kaynak kodunu "
                "kapsar; Astrype adı ve logosu bu lisansla verilmiş bir marka kullanım hakkı değildir.",
            ]),
            ("İletişim", [
                "Sorular için: {contact_link}",
            ]),
        ],
    },
}

"""Indonesian legal texts — translation of tr.py (the Turkish source of truth).

Translations are provided for convenience; in case of any conflict or
discrepancy, the Turkish version prevails. Keep section/paragraph structure
and {placeholders} identical to tr.py.
"""

TEXT = {
    "native_name": "Bahasa Indonesia",
    "dir": "ltr",
    "updated_label": "Terakhir diperbarui",
    "updated": "14 Juli 2026",
    "contact_label": "Kontak",
    "languages_label": "Bahasa",
    "translation_notice": (
        "Terjemahan ini disediakan hanya untuk kemudahan. Jika terjadi pertentangan, "
        "versi bahasa Turki yang berlaku."
    ),
    "privacy": {
        "title": "Kebijakan Privasi",
        "note": (
            "<strong>Ringkasan:</strong> Kami menggunakan datamu hanya untuk membuat konten "
            "astrologi/ramalan yang dipersonalisasi untukmu. Foto ramalan ampas kopi/telapak "
            "tangan/wajah yang kamu unggah <strong>langsung dihapus setelah analisis</strong> dan "
            "tidak disimpan. Kami tidak menjual datamu kepada pihak ketiga. Kamu dapat menghapus "
            "riwayat dan akunmu sepenuhnya dari dalam aplikasi kapan pun kamu mau."
        ),
        "sections": [
            ("Data yang kami kumpulkan", [
                "Akun: alamat email (melalui Supabase Auth). Profil: namamu (opsional), tanggal/jam/tempat "
                "lahir, serta preferensi bahasa dan minatmu. Konten: analisis yang kamu buat (peta "
                "kelahiran, tarot, ramalan, kecocokan hubungan), riwayat obrolanmu dengan AI, dan catatan "
                "konteks yang berisi ringkasan singkat dari semua itu (Cosmic Memory).",
            ]),
            ("Foto", [
                "Foto yang kamu unggah untuk ramalan ampas kopi/telapak tangan/wajah diproses di server "
                "hanya selama analisis berlangsung dan <strong>dihapus secara permanen begitu analisis "
                "selesai</strong>. Foto tidak disimpan; di arsip hanya disimpan hasil teks dan daftar "
                "simbol.",
            ]),
            ("Cara datamu diproses", [
                "Perhitungan astrologi dilakukan di server kami (Swiss Ephemeris). Untuk interpretasi yang "
                "dipersonalisasi, kontenmu dikirim ke penyedia AI (OpenAI dan Google Gemini) semata-mata "
                "untuk menghasilkan interpretasi. Kunci API hanya disimpan di server; kunci tersebut tidak "
                "ada di dalam aplikasi.",
            ]),
            ("Penyimpanan dan penghapusan", [
                "Kamu dapat menghapus datamu kapan saja: melalui <em>Profil → Data saya → Hapus memori / "
                "riwayat</em> kamu dapat menghapus riwayat analisis dan obrolan; melalui <em>Hapus akun "
                "secara permanen</em> kamu dapat menghapus seluruh data dan akunmu secara permanen. Saat "
                "akun dihapus, semua catatan terkait dihapus dan tidak dapat dipulihkan.",
            ]),
            ("Berbagi data", [
                "Kami tidak menjual atau menyewakan datamu untuk tujuan iklan. Kami hanya memprosesnya "
                "bersama penyedia infrastruktur yang diperlukan untuk menyediakan layanan (autentikasi, "
                "basis data, interpretasi AI, pengelolaan langganan).",
            ]),
            ("Menggunakan hakmu (KVKK/GDPR)", [
                "Kamu berhak mengakses, memperbaiki, dan menghapus datamu serta membatasi pemrosesannya. "
                "Untuk permintaanmu, kamu dapat menulis ke {contact_link}.",
            ]),
            ("Anak-anak", [
                "Astrype tidak ditujukan untuk pengguna berusia di bawah 13 tahun.",
            ]),
            ("Sumber terbuka", [
                "Kode sumber perangkat lunak server Astrype tersedia untuk umum di bawah lisensi "
                "{license}: {source_link}. Kode sumber tidak berisi data pengguna maupun kunci rahasia "
                "apa pun.",
            ]),
        ],
    },
    "terms": {
        "title": "Ketentuan Penggunaan",
        "note": (
            "<strong>Penting:</strong> Interpretasi astrologi, tarot, ramalan ampas kopi/telapak "
            "tangan/wajah, dan tafsir mimpi di Astrype <strong>hanya untuk hiburan dan wawasan "
            "pribadi</strong>. Semua itu tidak menggantikan dukungan profesional untuk keputusan medis, "
            "hukum, keuangan, atau yang terkait keselamatan. Pemandu AI-mu (Lyra) tidak memberikan "
            "pernyataan pasti tentang takdir atau masa depan."
        ),
        "sections": [
            ("Sifat layanan", [
                "Astrype menyediakan peta kelahiran, interpretasi harian/bulanan, tarot, modul ramalan, "
                "dan asisten obrolan AI yang mengetahui riwayatmu. Konten ditujukan untuk refleksi dan "
                "wawasan pribadi; konten tersebut tidak mengklaim kebenaran ilmiah atau kebenaran yang pasti.",
            ]),
            ("Penafian", [
                "Kamu bertanggung jawab atas keputusan yang kamu ambil berdasarkan interpretasi di "
                "aplikasi. Dalam situasi terkait kesehatan, hukum, keuangan, atau krisis, silakan "
                "berkonsultasi dengan ahli yang relevan.",
            ]),
            ("Langganan", [
                "Fitur Premium memerlukan langganan. Pembayaran, perpanjangan, dan pembatalan dikelola "
                "melalui Apple App Store atau Google Play. Langganan diperpanjang secara otomatis kecuali "
                "kamu membatalkannya sebelum akhir periode; kamu dapat membatalkannya melalui akun toko "
                "aplikasimu. Pembelian dapat dipulihkan dengan \"Pulihkan pembelian\".",
            ]),
            ("Penggunaan yang dapat diterima", [
                "Kamu tidak boleh menggunakan layanan untuk tujuan ilegal, dengan cara yang melanggar hak "
                "orang lain, atau dengan menyalahgunakan sistem.",
            ]),
            ("Perubahan", [
                "Kami dapat memperbarui ketentuan ini dari waktu ke waktu. Perubahan penting akan kami "
                "umumkan di dalam aplikasi.",
            ]),
            ("Sumber terbuka / Kode sumber", [
                "Perangkat lunak server (backend) Astrype bersifat sumber terbuka dan diterbitkan di bawah "
                "lisensi <strong>{license}</strong>. Setiap pengguna yang berinteraksi dengan layanan ini "
                "melalui jaringan dapat mengakses secara gratis kode sumber lengkap dari perangkat lunak "
                "yang menjalankan layanan, serta memeriksa, mengubah, dan mendistribusikannya kembali "
                "sesuai ketentuan lisensi:",
                "{source_link}",
                "Tautan permanen: {source_path_link}. Perhitungan astrologi menggunakan pustaka Swiss "
                "Ephemeris milik Astrodienst AG (dengan opsi AGPL) dan Kerykeion; lisensi pihak ketiga "
                "tercantum dalam file <code>THIRD_PARTY_LICENSES.md</code> di repositori. Lisensi "
                "tersebut menyatakan bahwa perangkat lunak disediakan \"sebagaimana adanya\" tanpa "
                "jaminan apa pun. Bagian ini hanya mencakup kode sumber perangkat lunak server; nama dan "
                "logo Astrype bukan merupakan hak penggunaan merek yang diberikan melalui lisensi ini.",
            ]),
            ("Kontak", [
                "Untuk pertanyaan: {contact_link}",
            ]),
        ],
    },
}

"""Yasal sayfalar — Gizlilik Politikası + Kullanım Şartları (herkese açık HTML).

App Store / Google Play listeleme için kalıcı, kimlik doğrulaması gerektirmeyen
URL'ler sunar: /legal/privacy, /legal/terms, /legal/source. Uygulama içinden de aynı URL'ler
açılır. İçerik eğlence/kişisel içgörü disclaimer'ını (Bölüm 16) içerir.

AGPL-3.0 §13: Swiss Ephemeris (pyswisseph/Kerykeion) AGPL olduğundan ağ üzerinden
hizmet alan kullanıcılara backend kaynak kodu sunulur — şartlar sayfasındaki
"Açık kaynak" bölümü ve /legal/source yönlendirmesi bu yükümlülüğü karşılar.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["legal"])

# Güncelleme tarihi ve iletişim — yayın öncesi gerçek destek adresiyle doğrulanmalı.
_UPDATED = "14 Temmuz 2026"
_CONTACT = "destek@astrype.com"

# Backend kaynak kodu (AGPL-3.0 §13). Repo taşınırsa yalnızca burası değişir;
# uygulama ve dış bağlantılar kalıcı /legal/source adresini kullanabilir.
_SOURCE_URL = "https://github.com/mkylv/astrype-backend"
_LICENSE_NAME = "GNU Affero General Public License v3.0 (AGPL-3.0)"

_STYLE = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0A0813;color:#ECE6F4;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  line-height:1.65;padding:32px 20px 64px}
.wrap{max-width:720px;margin:0 auto}
h1{font-family:Georgia,'Times New Roman',serif;color:#F5C96B;font-size:28px;
  letter-spacing:.02em;margin:0 0 4px}
.upd{color:#9C92BA;font-size:13px;margin-bottom:28px}
h2{color:#E3B864;font-size:18px;margin:28px 0 8px}
p,li{color:#CFC7DE;font-size:15px}
a{color:#F5C96B}
.note{background:#181233;border:1px solid #3A2D6B;border-radius:12px;
  padding:14px 16px;margin:24px 0;color:#ECE6F4;font-size:14px}
footer{color:#6f6790;font-size:12px;margin-top:40px;border-top:1px solid #241c46;padding-top:16px}
"""


def _page(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="tr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Astrype — {title}</title><style>{_STYLE}</style></head>
<body><div class="wrap"><h1>{title}</h1>
<div class="upd">Son güncelleme: {_UPDATED}</div>
{body}
<footer>Astrype · İletişim: <a href="mailto:{_CONTACT}">{_CONTACT}</a></footer>
</div></body></html>"""


_PRIVACY = _page(
    "Gizlilik Politikası",
    f"""
<div class="note"><strong>Özet:</strong> Verini yalnızca sana kişiselleştirilmiş
astroloji/fal içeriği üretmek için kullanırız. Yüklediğin kahve/el/yüz falı
fotoğrafları <strong>analizden hemen sonra silinir</strong>, saklanmaz.
Verini üçüncü taraflara satmayız. Dilediğinde geçmişini ve hesabını uygulama
içinden tamamen silebilirsin.</div>

<h2>1. Topladığımız veriler</h2>
<p>Hesap: e-posta adresi (Supabase Auth ile). Profil: adın (opsiyonel), doğum
tarihi/saati/yeri, dil ve ilgi alanı tercihlerin. İçerik: ürettiğin analizler
(doğum haritası, tarot, fal, ilişki uyumu), yapay zekâ sohbet geçmişin ve bunların
kısa özetlerinden oluşan bağlam kayıtları (Cosmic Memory).</p>

<h2>2. Fotoğraflar</h2>
<p>Kahve/el/yüz falı için yüklediğin fotoğraflar sunucuda yalnızca analiz süresince
işlenir ve <strong>analiz biter bitmez kalıcı olarak silinir</strong>. Fotoğraf
saklanmaz; arşivde yalnızca metin sonucu ve sembol listesi tutulur.</p>

<h2>3. Verilerin nasıl işlenir</h2>
<p>Astrolojik hesaplamalar sunucumuzda (Swiss Ephemeris) yapılır. Kişiselleştirilmiş
yorumlar için içeriğin, yapay zekâ sağlayıcılarına (OpenAI ve Google Gemini) yalnızca
yorum üretimi amacıyla iletilir. API anahtarları yalnızca sunucuda tutulur; uygulamada
bulunmaz.</p>

<h2>4. Saklama ve silme</h2>
<p>Verilerini istediğin an silebilirsin: <em>Profil → Verilerim → Hafızayı/geçmişi sil</em>
ile analiz ve sohbet geçmişini; <em>Hesabı sil</em> ile tüm verini ve hesabını kalıcı
olarak kaldırabilirsin. Hesap silindiğinde ilişkili tüm kayıtlar geri döndürülemez şekilde silinir.</p>

<h2>5. Paylaşım</h2>
<p>Verini reklam amacıyla satmayız veya kiralamayız. Yalnızca hizmeti sağlamak için
gerekli altyapı sağlayıcılarıyla (kimlik doğrulama, veritabanı, yapay zekâ yorumlama,
abonelik yönetimi) işleriz.</p>

<h2>6. Haklarını kullanma (KVKK/GDPR)</h2>
<p>Verine erişme, düzeltme, silme ve işlemeyi sınırlama haklarına sahipsin. Talebin
için <a href="mailto:{_CONTACT}">{_CONTACT}</a> adresine yazabilirsin.</p>

<h2>7. Çocuklar</h2>
<p>Astrype 13 yaşın altındaki kullanıcılara yönelik değildir.</p>

<h2>8. Açık kaynak</h2>
<p>Astrype sunucu yazılımının kaynak kodu {_LICENSE_NAME} lisansıyla herkese açıktır:
<a href="{_SOURCE_URL}">{_SOURCE_URL}</a>. Kaynak kodu hiçbir kullanıcı verisi veya
gizli anahtar içermez.</p>
""",
)

_TERMS = _page(
    "Kullanım Şartları",
    f"""
<div class="note"><strong>Önemli:</strong> Astrype'taki astroloji, tarot, kahve/el/yüz
falı ve rüya yorumları <strong>yalnızca eğlence ve kişisel içgörü</strong> amaçlıdır.
Tıbbi, hukuki, finansal veya güvenlik açısından kritik kararlar için profesyonel
destek yerine geçmez. Yapay zekâ rehberin (Lyra) kesin kader/gelecek beyanı vermez.</div>

<h2>1. Hizmetin niteliği</h2>
<p>Astrype; doğum haritası, günlük/aylık yorum, tarot, fal modülleri ve geçmişini bilen
bir yapay zekâ sohbet asistanı sunar. İçerikler kişisel düşünce ve içgörü içindir;
bilimsel/kesin gerçeklik iddiası taşımaz.</p>

<h2>2. Sorumluluk reddi</h2>
<p>Uygulamadaki yorumlara dayanarak aldığın kararlardan sen sorumlusun. Sağlık, hukuk,
finans veya kriz durumlarında lütfen ilgili uzmana başvur.</p>

<h2>3. Abonelik</h2>
<p>Premium özellikler abonelik gerektirir. Ödeme, yenileme ve iptal işlemleri Apple
App Store veya Google Play üzerinden yönetilir. Abonelik, dönem sonunda iptal etmediğin
sürece otomatik yenilenir; iptali mağaza hesabından yapabilirsin. Satın alımlar
"Satın alımları geri yükle" ile geri yüklenebilir.</p>

<h2>4. Kabul edilebilir kullanım</h2>
<p>Hizmeti yasa dışı amaçlarla, başkalarının haklarını ihlal edecek şekilde veya
sistemi kötüye kullanarak kullanamazsın.</p>

<h2>5. Değişiklikler</h2>
<p>Bu şartları zaman zaman güncelleyebiliriz. Önemli değişiklikleri uygulama içinden
duyururuz.</p>

<h2>6. Açık kaynak / Kaynak kodu</h2>
<p>Astrype'ın sunucu (backend) yazılımı açık kaynaktır ve
<strong>{_LICENSE_NAME}</strong> lisansı altında yayınlanır. Bu hizmetle ağ üzerinden
etkileşime giren her kullanıcı, hizmeti çalıştıran yazılımın tam kaynak koduna
ücretsiz olarak erişebilir, onu inceleyebilir, değiştirebilir ve lisans koşulları
çerçevesinde yeniden dağıtabilir:</p>
<p><a href="{_SOURCE_URL}">{_SOURCE_URL}</a></p>
<p>Kalıcı bağlantı: <a href="/legal/source">/legal/source</a>. Astroloji hesaplamaları,
Astrodienst AG'nin Swiss Ephemeris kütüphanesini (AGPL seçeneğiyle) ve Kerykeion'u
kullanır; üçüncü taraf lisansları depodaki <code>THIRD_PARTY_LICENSES.md</code>
dosyasında listelenir. Lisans, yazılımın "olduğu gibi" ve herhangi bir garanti
olmaksızın sunulduğunu belirtir. Bu bölüm yalnızca sunucu yazılımının kaynak kodunu
kapsar; Astrype adı ve logosu bu lisansla verilmiş bir marka kullanım hakkı değildir.</p>

<h2>7. İletişim</h2>
<p>Sorular için: <a href="mailto:{_CONTACT}">{_CONTACT}</a></p>
""",
)


@router.get("/legal/privacy", response_class=HTMLResponse)
async def privacy_policy() -> str:
    return _PRIVACY


@router.get("/legal/terms", response_class=HTMLResponse)
async def terms_of_use() -> str:
    return _TERMS


@router.get("/legal/source", status_code=307, include_in_schema=True)
async def source_code() -> RedirectResponse:
    """AGPL-3.0 §13 — backend Corresponding Source'a kalıcı yönlendirme."""
    return RedirectResponse(_SOURCE_URL, status_code=307)

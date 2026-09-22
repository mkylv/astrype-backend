"""Halka açık web sitesi — astrype.com ana sayfası + destek sayfası.

App Store listelemesi https://astrype.com adresini hem Support URL hem Marketing
URL olarak bildiriyor; bu modül o iki sayfayı backend'den sunar:

    GET /          -> tanıtım (landing) sayfası
    GET /support   -> destek / iletişim / SSS sayfası

Dil: yalnızca **tr** ve **en**. Çözümleme yasal sayfalarla aynı zincire dayanır
(``routes_legal.resolve_lang``: ?lang= -> Accept-Language -> en); sonuç tr
değilse İngilizce'ye düşer. Site 20 dile çevrilmez — yasal metinler çevrilidir
ve alt bilgideki bağlantılar geçerli dille /legal/... adreslerine gider.

İçerik kuralları (CLAUDE.md §0, §12, §16):
  * Eğlence / kişisel içgörü disclaimer'ı her iki sayfada görünür.
  * Kesin kehanet, tıbbi/hukuki/finansal tavsiye vaadi yok.
  * Kahve/el/yüz falı fotoğrafı analizden hemen sonra sunucudan silinir — açıkça yazılır.
  * Uydurma referans, kullanıcı sayısı, basın logosu veya aciliyet oyunu yok.

Görseller ``app/static/img`` altında (StaticFiles ile /static'ten sunulur).
"""
from __future__ import annotations

from fastapi import APIRouter, Header, Query
from fastapi.responses import HTMLResponse

from app.api.routes_legal import resolve_lang

router = APIRouter(tags=["site"])

SITE_LANGS = ("en", "tr")
SITE_DEFAULT_LANG = "en"

CONTACT_EMAIL = "destek@astrype.com"

# --- Mağaza bağlantıları -------------------------------------------------
# Uygulama henüz yayında değil. Yayınlandığında YALNIZCA bu iki satır
# doldurulur; şablon otomatik olarak "yakında" rozetini gerçek bağlantıya
# çevirir. Boş string = yayında değil.
APP_STORE_URL = ""
PLAY_STORE_URL = ""

# Abonelik yönetimi — mağazaların kalıcı, uygulamadan bağımsız adresleri.
APPLE_SUBSCRIPTIONS_URL = "https://apps.apple.com/account/subscriptions"
GOOGLE_SUBSCRIPTIONS_URL = "https://play.google.com/store/account/subscriptions"

_STYLE = """
:root{
  color-scheme:dark;
  --bg:#0A0813; --bg2:#120E24; --surface:#1A1433; --surface2:#140F28;
  --line:#2A2150; --gold:#D6A93A; --rich:#F5C96B; --ivory:#FAF8F2;
  --text:#CFC7DE; --muted:#9C92BA;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:16px;line-height:1.7;overflow-x:hidden}
img{max-width:100%;height:auto;display:block}
a{color:var(--rich)}
a:focus-visible,summary:focus-visible,button:focus-visible{
  outline:2px solid var(--rich);outline-offset:3px;border-radius:4px}
.wrap{width:100%;max-width:1040px;margin:0 auto;padding:0 20px}
.narrow{max-width:760px}

/* header */
header.site{position:sticky;top:0;z-index:10;background:rgba(10,8,19,.92);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  padding:12px 0;justify-content:space-between}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ivory)}
.brand img{width:32px;height:32px;border-radius:8px}
.brand span{font-family:'Cinzel',Georgia,serif;font-size:19px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--rich)}
.navlinks{display:flex;align-items:center;gap:8px 16px;flex-wrap:wrap;font-size:14px}
.navlinks a{color:var(--muted);text-decoration:none}
.navlinks a:hover{color:var(--rich)}
.navlinks a[aria-current]{color:var(--rich);font-weight:600}
.sep{color:var(--line)}

/* hero */
.hero{position:relative;padding:64px 0 48px;
  background:
    radial-gradient(60% 46% at 50% 0%, rgba(214,169,58,.16), transparent 70%),
    radial-gradient(90% 60% at 80% 20%, rgba(58,45,107,.45), transparent 70%),
    var(--bg)}
.hero-grid{display:grid;gap:40px;grid-template-columns:1fr;align-items:center}
.hero-grid>*{min-width:0}
@media(min-width:860px){.hero-grid{grid-template-columns:1.05fr .95fr;gap:48px}}
.overline{font-size:12px;letter-spacing:.24em;text-transform:uppercase;
  color:var(--gold);margin:0 0 14px}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;
  font-size:clamp(34px,7.2vw,56px);line-height:1.12;color:var(--ivory);
  margin:0 0 18px;letter-spacing:.01em}
h1 em{font-style:normal;color:var(--rich)}
.lede{font-size:clamp(16px,2.4vw,18px);color:var(--text);margin:0 0 28px;max-width:34em}
.hero-shot{margin:0 auto;max-width:300px;
  filter:drop-shadow(0 24px 60px rgba(0,0,0,.65))}
.hero-shot img{width:100%;border-radius:22px;border:1px solid var(--line)}

/* store badges */
.stores{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 14px;padding:0;list-style:none}
.badge{display:inline-flex;flex-direction:column;justify-content:center;
  min-height:52px;padding:8px 20px;border-radius:999px;border:1px solid var(--line);
  background:var(--surface2);text-decoration:none;color:var(--muted)}
.badge b{display:block;color:var(--ivory);font-size:15px;font-weight:600;line-height:1.3}
.badge small{font-size:11px;letter-spacing:.14em;text-transform:uppercase}
a.badge{border-color:var(--gold);color:var(--rich)}
a.badge b{color:var(--rich)}
.storenote{font-size:13px;color:var(--muted);margin:0}

/* sections */
section{padding:56px 0;border-top:1px solid var(--line)}
h2{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;
  font-size:clamp(26px,4.6vw,36px);color:var(--ivory);margin:0 0 12px;line-height:1.2}
h3{font-family:'Inter',sans-serif;font-size:17px;color:var(--ivory);margin:0 0 6px}
.sub{color:var(--muted);margin:0 0 32px;max-width:44em}

.cards{display:grid;gap:14px;grid-template-columns:1fr}
.cards>*{min-width:0}
@media(min-width:560px){.cards{grid-template-columns:repeat(2,1fr)}}
@media(min-width:880px){.cards{grid-template-columns:repeat(3,1fr)}}
.card{background:var(--surface2);border:1px solid var(--line);border-radius:16px;
  padding:20px}
.card p{margin:0;font-size:14.5px;color:var(--text)}
.card .glyph{font-size:20px;color:var(--gold);line-height:1;margin-bottom:10px}

.shots{display:grid;gap:14px;grid-template-columns:repeat(2,1fr)}
@media(min-width:720px){.shots{grid-template-columns:repeat(4,1fr)}}
.shots>*{min-width:0}
.shots figure{margin:0}
.shots img{width:100%;border-radius:14px;border:1px solid var(--line)}
.shots figcaption{font-size:13px;color:var(--muted);margin-top:8px}

.split{display:grid;gap:32px;grid-template-columns:1fr;align-items:center}
@media(min-width:820px){.split{grid-template-columns:1fr 1fr;gap:48px}}
.split>*{min-width:0}
.split .shot{max-width:260px;margin:0 auto}
.split .shot img{width:100%;border-radius:20px;border:1px solid var(--line)}

ul.plain{margin:0;padding-left:20px}
ul.plain li{margin-bottom:8px;font-size:15px}

.note{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:12px;padding:16px 18px;color:var(--ivory);font-size:14.5px}
.note strong{color:var(--rich)}

details{background:var(--surface2);border:1px solid var(--line);border-radius:12px;
  padding:0;margin-bottom:10px}
summary{cursor:pointer;padding:14px 18px;color:var(--ivory);font-weight:600;
  font-size:15.5px;list-style:none}
summary::-webkit-details-marker{display:none}
summary::after{content:'+';float:right;color:var(--gold);font-weight:400}
details[open] summary::after{content:'\\2212'}
details .answer{padding:0 18px 16px;font-size:14.5px}
details .answer p{margin:0 0 10px}
details .answer p:last-child{margin:0}

.contactbox{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:24px}
.contactbox .mail{font-family:'Cormorant Garamond',Georgia,serif;
  font-size:clamp(22px,4.4vw,30px);color:var(--rich);text-decoration:none;
  word-break:break-word}

footer.site{border-top:1px solid var(--line);padding:36px 0 48px;
  color:var(--muted);font-size:13.5px}
.footlinks{display:flex;flex-wrap:wrap;gap:8px 18px;margin:0 0 16px;padding:0;list-style:none}
.footlinks a{color:var(--muted);text-decoration:none}
.footlinks a:hover{color:var(--rich)}
.disclaimer{font-size:13px;color:var(--muted);max-width:60em}

@media(prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important;scroll-behavior:auto!important}
}
@media(max-width:380px){.wrap{padding:0 14px}}
"""

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Cinzel:wght@500;600&family=Cormorant+Garamond:wght@500;600&"
    'family=Inter:wght@400;500;600&display=swap">'
)

# --------------------------------------------------------------------------
# İçerik — yalnızca gerçekten var olan özellikler (app_en.arb / app_tr.arb).
# --------------------------------------------------------------------------

TEXTS: dict[str, dict] = {
    "en": {
        "dir": "ltr",
        "native": "English",
        "home_title": "Astrype — your chart, your readings, your guide",
        "home_desc": (
            "Astrype brings your natal chart, daily horoscope, tarot, coffee-cup, "
            "palm and face readings, dreams, numerology, Human Design and "
            "compatibility together with Lyra, an AI guide that remembers your "
            "readings. For entertainment and personal insight."
        ),
        "support_title": "Astrype — Support",
        "support_desc": "Help, contact, account deletion, subscriptions and frequently asked questions.",
        "nav_support": "Support",
        "nav_privacy": "Privacy",
        "nav_terms": "Terms",
        "langs_label": "Language",
        "hero_overline": "A mobile app for iOS and Android",
        "hero_h1_a": "Your sky, read",
        "hero_h1_b": "in your own words",
        "hero_lede": (
            "Astrype draws your birth chart in full, reads today's sky over it, and "
            "keeps every reading in one place. Lyra, your guide inside the app, "
            "remembers what you have already asked — so the next answer starts where "
            "the last one ended."
        ),
        "store_soon_title": "Coming soon",
        "store_soon_apple": "App Store",
        "store_soon_google": "Google Play",
        "store_live_top": "Download on the",
        "store_live_top_g": "Get it on",
        "store_note": (
            "Astrype has not been released yet. The App Store and Google Play links "
            "will appear here the day it goes live."
        ),
        "hero_shot_alt": (
            "Astrype home screen on a phone: 'Tonight's sky', a greeting, a wheel of "
            "zodiac glyphs and a free daily card called Today's Whisper."
        ),
        "f_title": "Everything in one app",
        "f_sub": (
            "Eleven ways to look at the same question. Each one is written for you, "
            "in plain language, and saved to your own archive."
        ),
        "features": [
            ("✺", "Birth Chart", "Your full natal wheel — planets, houses and aspects — with every placement explained in plain language instead of jargon."),
            ("✶", "Daily Horoscope", "Today's sky read over your own chart, not a generic sun-sign column. A short whisper each day, free."),
            ("✦", "Tarot", "A three-card spread read as one story: past, present and what is drawing near."),
            ("✷", "Coffee Reading", "Photograph the inside of your cup. The symbols are read and interpreted — the photo is deleted right after."),
            ("✸", "Palm Reading", "A reading of the lines of your dominant hand, from a single photo that is deleted after analysis."),
            ("◈", "Face Reading", "The old art of physiognomy, read from one front-facing photo that never leaves the analysis."),
            ("✹", "Dream Interpretation", "Tell a dream in your own words and see the symbols and themes inside it."),
            ("✴", "Numerology", "Your numbers — life path, expression and the patterns they repeat."),
            ("⬡", "Human Design", "Your type, strategy, authority and centres, calculated from your birth details."),
            ("❖", "Cosmic Match", "Two charts side by side: where the warmth is easy, where patience is needed, and what to actually talk about."),
            ("✧", "Lyra & Cosmic Memory", "An AI guide that already knows your chart and your past readings, so you never have to explain yourself twice."),
        ],
        "lyra_title": "Lyra remembers every reading",
        "lyra_body": [
            "Most apps hand you a paragraph and forget you. Lyra is different: your "
            "chart and the analyses you have already done are used as context, so a "
            "question about your career can be answered against the same Venus that "
            "came up in last week's tarot.",
            "Lyra speaks carefully on purpose. Nothing is presented as fixed fate, "
            "and Astrype does not give medical, legal, financial or safety advice — "
            "for those, please talk to a professional.",
        ],
        "lyra_alt": (
            "Astrype chat screen: Lyra explains that the chart and past readings are "
            "used as context, then answers a question about the day ahead."
        ),
        "privacy_title": "Your photos are not kept",
        "privacy_body": [
            "Coffee-cup, palm and face readings need a photo. That photo is sent to "
            "the analysis, and deleted from the server as soon as the analysis "
            "finishes. It is never stored, never shown to anyone, and never added to "
            "your archive.",
            "What is kept is the text: the list of symbols that were read and the "
            "interpretation written from them — in your account, visible only to you.",
        ],
        "privacy_points": [
            "Photos are deleted from the server immediately after analysis.",
            "Your birth details are used to calculate your chart and to personalise readings.",
            "You can delete your history and Cosmic Memory, or your whole account, from inside the app.",
            "Sign in with Apple, Google or email — or start as a guest and decide later.",
        ],
        "shots_title": "Inside the app",
        "shots": [
            ("en-1.jpg", "The natal chart screen: a full birth wheel with planets and aspect lines, and a written explanation of the Sun's placement."),
            ("en-4.jpg", "A three-card tarot spread — The Star, The Lovers, The Moon — with an interpretation underneath."),
            ("en-5.jpg", "A compatibility reading showing a match score, strengths, challenging areas and conversation tips."),
            ("en-3.jpg", "The chat screen where Lyra answers using the chart and earlier readings as context."),
        ],
        "plans_title": "Premium and Stardust",
        "plans_body": [
            "Today's Whisper is free every day. Deeper readings are unlocked with "
            "<strong>Stardust</strong>, the in-app credit: a Premium subscription "
            "includes Stardust on a regular cycle along with daily messages to Lyra, "
            "and extra Stardust packs can be bought on their own.",
            "Prices, renewal period and trial length are always shown in the app "
            "before you pay. Subscriptions renew automatically until you cancel them "
            "in your App Store or Google Play settings.",
        ],
        "disclaimer": (
            "Astrype's astrology, tarot and fortune-telling content is for "
            "entertainment and personal insight. It is not a substitute for "
            "professional medical, legal, financial or safety advice, and it does not "
            "predict the future."
        ),
        "foot_support": "Support",
        "foot_privacy": "Privacy Policy",
        "foot_terms": "Terms of Use",
        "foot_source": "Source code",
        "foot_contact": "Contact",
        # --- support page ---
        "sup_overline": "Support",
        "sup_h1_a": "We are here",
        "sup_h1_b": "when you need us",
        "sup_lede": (
            "Questions about a reading, your account, your data or a purchase — write "
            "to us and a person will answer."
        ),
        "sup_contact_title": "Contact us",
        "sup_contact_body": (
            "Email is the fastest way to reach us. We read every message and reply as "
            "soon as we can. If you are writing about a purchase or a technical "
            "problem, telling us your device and app version helps a lot."
        ),
        "sup_what_title": "What Astrype is",
        "sup_what_body": (
            "Astrype is a mobile app that brings your natal birth chart, a daily "
            "personalised horoscope, tarot, coffee-cup, palm and face readings, dream "
            "interpretation, numerology, Human Design and relationship compatibility "
            "together in one place — with Lyra, an AI guide whose Cosmic Memory "
            "remembers the readings you have already done."
        ),
        "sup_delete_title": "Deleting your account and your data",
        "sup_delete_body": "Both are done from inside the app, and neither needs to go through us:",
        "sup_delete_steps": [
            "<strong>Delete history and memory:</strong> Profile &rarr; My data &rarr; "
            "“Delete memory / history”. Your past analyses, chat records and "
            "Cosmic Memory summaries are permanently deleted. Your profile and birth "
            "details stay.",
            "<strong>Delete your account:</strong> Profile &rarr; Account &rarr; "
            "“Permanently delete account”. Your account and all of your data "
            "— profile, birth details, analyses, chats and subscription records "
            "— are irreversibly deleted. This cannot be undone.",
            "Deleting your account does <strong>not</strong> cancel an active App "
            "Store or Google Play subscription. Cancel it in your store's "
            "subscription settings as well.",
        ],
        "sup_subs_title": "Managing your subscription",
        "sup_subs_body": (
            "Purchases are handled by Apple and Google, so a subscription is started, "
            "changed and cancelled in your store account — not by us. Cancelling stops "
            "the next renewal; the current period runs to its end."
        ),
        "sup_subs_apple": "Manage on the App Store",
        "sup_subs_google": "Manage on Google Play",
        "sup_faq_title": "Frequently asked questions",
        "faq": [
            ("What is Stardust?",
             ["Stardust is the credit used inside Astrype to unlock a reading. A "
              "Premium subscription includes Stardust on a regular cycle together "
              "with daily messages to Lyra, and separate Stardust packs can be "
              "bought if you run out.",
              "Today's Whisper, the short daily reading, is free and does not cost "
              "Stardust."]),
            ("Is Astrype entertainment, or real prediction?",
             ["Entertainment and personal insight. Astrype does not predict the "
              "future and never presents anything as fixed fate; readings are meant "
              "as a mirror to think with. They are not a substitute for professional "
              "medical, legal, financial or safety advice."]),
            ("Are my coffee, palm and face photos stored?",
             ["No. The photo is used for the analysis and deleted from the server "
              "immediately afterwards. It is never kept, never shared and never added "
              "to your archive. Only the text result and the list of symbols that "
              "were read are saved to your account."]),
            ("How do I cancel my subscription?",
             ["In your store, not in the app: on iOS open App Store account "
              "&rarr; Subscriptions, on Android open Google Play &rarr; Payments and "
              "subscriptions &rarr; Subscriptions. Cancel at least 24 hours before the "
              "period ends to avoid the next renewal."]),
            ("How do I restore my purchases?",
             ["Open the Premium / Stardust screen in the app and tap "
              "“Restore”. Your purchases are restored to the store account "
              "they were made with, so make sure you are signed in to that same Apple "
              "ID or Google account."]),
            ("Which languages does Astrype speak?",
             ["The app is available in 20 languages, including English, Turkish, "
              "Azerbaijani, German, Spanish, French, Italian, Dutch, Polish, "
              "Portuguese, Russian, Ukrainian, Arabic, Persian, Urdu, Hindi, "
              "Indonesian, Japanese, Korean and Chinese. You can change it any time "
              "from Profile &rarr; Language.",
              "This website is in English and Turkish; the legal pages are available "
              "in all supported languages."]),
            ("Is my birth data private?",
             ["Your birth date, time and place are used to calculate your chart and "
              "to personalise your readings, and they are stored in your own account "
              "where only you can reach them. You can delete them together with your "
              "account at any time. The details are in the Privacy Policy."]),
            ("What if I don't know my exact birth time?",
             ["You can still use Astrype. Where the birth time matters, the app says "
              "so plainly — the rising sign may not be calculated, compatibility "
              "becomes approximate and the Human Design type may shift — but "
              "everything that does not depend on the exact minute still works."]),
        ],
        "sup_back": "Back to the home page",
    },
    "tr": {
        "dir": "ltr",
        "native": "Türkçe",
        "home_title": "Astrype — haritan, yorumların, rehberin",
        "home_desc": (
            "Astrype; doğum haritanı, günlük burcunu, tarotu, kahve, el ve yüz falını, "
            "rüya yorumunu, numerolojiyi, İnsan Tasarımı'nı ve uyum analizini, "
            "okuduklarını hatırlayan yapay zekâ rehberi Lyra ile bir araya getirir. "
            "Eğlence ve kişisel içgörü amaçlıdır."
        ),
        "support_title": "Astrype — Destek",
        "support_desc": "Yardım, iletişim, hesap silme, abonelikler ve sık sorulan sorular.",
        "nav_support": "Destek",
        "nav_privacy": "Gizlilik",
        "nav_terms": "Şartlar",
        "langs_label": "Dil",
        "hero_overline": "iOS ve Android için mobil uygulama",
        "hero_h1_a": "Gökyüzün,",
        "hero_h1_b": "senin dilinle",
        "hero_lede": (
            "Astrype doğum haritanı bütünüyle çizer, bugünün göğünü o haritanın "
            "üzerinden okur ve bütün analizlerini tek yerde tutar. Uygulamanın "
            "içindeki rehberin Lyra, daha önce ne sorduğunu hatırlar — yeni cevap, "
            "bir öncekinin bittiği yerden başlar."
        ),
        "store_soon_title": "Yakında",
        "store_soon_apple": "App Store",
        "store_soon_google": "Google Play",
        "store_live_top": "İndir:",
        "store_live_top_g": "İndir:",
        "store_note": (
            "Astrype henüz yayında değil. App Store ve Google Play bağlantıları "
            "yayına çıktığı gün burada olacak."
        ),
        "hero_shot_alt": (
            "Telefonda Astrype ana ekranı: 'Bu gecenin göğü' başlığı, karşılama, burç "
            "sembollerinden oluşan çember ve ücretsiz günlük kart 'Bugünün Fısıltısı'."
        ),
        "f_title": "Hepsi tek uygulamada",
        "f_sub": (
            "Aynı soruya bakmanın on bir yolu. Her biri sana göre yazılır, sade bir "
            "dille anlatılır ve kendi arşivine kaydedilir."
        ),
        "features": [
            ("✺", "Doğum Haritası", "Gezegenler, evler ve açılarla tam doğum çemberin — her yerleşim jargon yerine sade bir dille açıklanır."),
            ("✶", "Günlük Burç", "Genel burç yazısı değil: bugünün göğü senin haritanın üzerinden okunur. Her gün kısa bir fısıltı, ücretsiz."),
            ("✦", "Tarot", "Üç kartlık açılım tek bir hikâye olarak okunur: geçmiş, şimdi ve yaklaşan."),
            ("✷", "Kahve Falı", "Fincanın içini fotoğrafla. Semboller okunur ve yorumlanır — fotoğraf hemen ardından silinir."),
            ("✸", "El Falı", "Baskın elinin çizgileri tek bir fotoğraftan okunur; fotoğraf analiz biter bitmez silinir."),
            ("◈", "Yüz Falı", "Sima ilminin eski geleneği, analizden öteye geçmeyen tek bir önden fotoğrafla."),
            ("✹", "Rüya Yorumu", "Rüyanı kendi cümlelerinle anlat; içindeki sembolleri ve temaları gör."),
            ("✴", "Numeroloji", "Sayıların — yaşam yolu, ifade sayısı ve tekrar eden örüntüler."),
            ("⬡", "İnsan Tasarımı", "Doğum bilgilerinden hesaplanan tipin, stratejin, otoriten ve merkezlerin."),
            ("❖", "Kozmik Uyum", "İki harita yan yana: neresi kolay ısınıyor, neresi sabır istiyor ve asıl neyi konuşmak gerekiyor."),
            ("✧", "Lyra ve Kozmik Hafıza", "Haritanı ve geçmiş analizlerini zaten bilen bir yapay zekâ rehber — kendini iki kez anlatman gerekmez."),
        ],
        "lyra_title": "Lyra her analizi hatırlar",
        "lyra_body": [
            "Çoğu uygulama sana bir paragraf verir ve seni unutur. Lyra öyle değil: "
            "haritan ve daha önce yaptığın analizler bağlam olarak kullanılır; "
            "kariyer sorusuna, geçen haftaki tarotta çıkan aynı Venüs üzerinden cevap "
            "verilebilir.",
            "Lyra bilerek temkinli konuşur. Hiçbir şey kesin kader gibi sunulmaz; "
            "Astrype tıbbi, hukuki, finansal veya güvenlikle ilgili tavsiye vermez — "
            "bunlar için lütfen bir uzmana danış.",
        ],
        "lyra_alt": (
            "Astrype sohbet ekranı: Lyra, haritanın ve geçmiş analizlerin bağlam "
            "olarak kullanıldığını söyleyip günle ilgili bir soruyu yanıtlıyor."
        ),
        "privacy_title": "Fotoğrafların saklanmaz",
        "privacy_body": [
            "Kahve, el ve yüz falı bir fotoğraf ister. O fotoğraf analize gönderilir "
            "ve analiz biter bitmez sunucudan silinir. Hiçbir zaman saklanmaz, "
            "kimseye gösterilmez ve arşivine eklenmez.",
            "Saklanan şey metindir: okunan sembollerin listesi ve onlardan yazılan "
            "yorum — hesabında, yalnızca senin görebileceğin şekilde.",
        ],
        "privacy_points": [
            "Fotoğraflar analizden hemen sonra sunucudan silinir.",
            "Doğum bilgilerin haritanı hesaplamak ve yorumları kişiselleştirmek için kullanılır.",
            "Geçmişini ve Kozmik Hafızanı ya da hesabının tamamını uygulama içinden silebilirsin.",
            "Apple, Google veya e-posta ile giriş yap — ya da misafir olarak başla, sonra karar ver.",
        ],
        "shots_title": "Uygulamanın içinden",
        "shots": [
            ("tr-1.jpg", "Doğum haritası ekranı: gezegenler ve açı çizgileriyle tam doğum çemberi, altında Güneş yerleşiminin yazılı açıklaması."),
            ("tr-4.jpg", "Üç kartlık tarot açılımı ve altında yorumu."),
            ("tr-5.jpg", "Uyum analizi: uyum puanı, güçlü yanlar, zorlayıcı alanlar ve konuşma önerileri."),
            ("tr-3.jpg", "Sohbet ekranı: Lyra, haritayı ve önceki analizleri bağlam alarak yanıt veriyor."),
        ],
        "plans_title": "Premium ve Yıldız Tozu",
        "plans_body": [
            "Bugünün Fısıltısı her gün ücretsizdir. Derin analizler uygulama içi kredi "
            "olan <strong>Yıldız Tozu</strong> ile açılır: Premium abonelik, Lyra'ya "
            "günlük mesaj hakkıyla birlikte düzenli olarak Yıldız Tozu içerir; "
            "ayrıca tek başına Yıldız Tozu paketleri de alınabilir.",
            "Fiyat, yenilenme dönemi ve deneme süresi ödemeden önce uygulamada her "
            "zaman gösterilir. Abonelikler, App Store veya Google Play ayarlarından "
            "iptal edilmedikçe otomatik yenilenir.",
        ],
        "disclaimer": (
            "Astrype'ın astroloji, tarot ve fal içerikleri eğlence ve kişisel içgörü "
            "amaçlıdır. Profesyonel tıbbi, hukuki, finansal veya güvenlik tavsiyesinin "
            "yerine geçmez ve geleceği önceden bildirmez."
        ),
        "foot_support": "Destek",
        "foot_privacy": "Gizlilik Politikası",
        "foot_terms": "Kullanım Şartları",
        "foot_source": "Kaynak kod",
        "foot_contact": "İletişim",
        # --- destek sayfası ---
        "sup_overline": "Destek",
        "sup_h1_a": "İhtiyacın olduğunda",
        "sup_h1_b": "buradayız",
        "sup_lede": (
            "Bir yorumla, hesabınla, verilerinle ya da satın almanla ilgili soruların "
            "için yaz — cevabı bir insan yazacak."
        ),
        "sup_contact_title": "Bize ulaş",
        "sup_contact_body": (
            "Bize ulaşmanın en hızlı yolu e-posta. Her mesajı okuyor ve "
            "elimizden geldiğince çabuk yanıtlıyoruz. Bir satın alma ya da teknik bir "
            "sorun için yazıyorsan cihazını ve uygulama sürümünü belirtmen çok "
            "yardımcı olur."
        ),
        "sup_what_title": "Astrype nedir?",
        "sup_what_body": (
            "Astrype; doğum haritanı, günlük kişisel burç yorumunu, tarotu, kahve, el "
            "ve yüz falını, rüya yorumunu, numerolojiyi, İnsan Tasarımı'nı ve ilişki "
            "uyumunu tek yerde toplayan bir mobil uygulamadır — yanında, Kozmik "
            "Hafızası sayesinde daha önce yaptığın analizleri hatırlayan yapay zekâ "
            "rehberi Lyra ile."
        ),
        "sup_delete_title": "Hesabını ve verilerini silme",
        "sup_delete_body": "İkisi de uygulama içinden yapılır, bizden geçmesi gerekmez:",
        "sup_delete_steps": [
            "<strong>Geçmişi ve hafızayı sil:</strong> Profil &rarr; Verilerim &rarr; "
            "“Hafızayı / geçmişi sil”. Geçmiş analizlerin, sohbet kayıtların "
            "ve Kozmik Hafıza özetlerin kalıcı olarak silinir. Profilin ve doğum "
            "bilgilerin kalır.",
            "<strong>Hesabını sil:</strong> Profil &rarr; Hesap &rarr; “Hesabı "
            "kalıcı olarak sil”. Hesabın ve tüm verilerin — profil, doğum "
            "bilgileri, analizler, sohbetler ve abonelik kayıtları — geri "
            "alınamaz biçimde silinir.",
            "Hesabını silmek, aktif bir App Store veya Google Play aboneliğini "
            "<strong>iptal etmez</strong>. Aboneliği ayrıca mağazanın abonelik "
            "ayarlarından iptal etmelisin.",
        ],
        "sup_subs_title": "Aboneliğini yönetme",
        "sup_subs_body": (
            "Satın almaları Apple ve Google yürütür; abonelik mağaza hesabından "
            "başlatılır, değiştirilir ve iptal edilir — bizden değil. İptal, bir "
            "sonraki yenilemeyi durdurur; içinde bulunduğun dönem sonuna kadar devam "
            "eder."
        ),
        "sup_subs_apple": "App Store'dan yönet",
        "sup_subs_google": "Google Play'den yönet",
        "sup_faq_title": "Sık sorulan sorular",
        "faq": [
            ("Yıldız Tozu nedir?",
             ["Yıldız Tozu, Astrype içinde bir analizi açmak için kullanılan kredidir. "
              "Premium abonelik, Lyra'ya günlük mesaj hakkıyla birlikte düzenli olarak "
              "Yıldız Tozu içerir; bittiğinde ayrıca Yıldız Tozu paketi alınabilir.",
              "Kısa günlük yorum olan Bugünün Fısıltısı ücretsizdir ve Yıldız Tozu "
              "harcamaz."]),
            ("Astrype eğlence mi, gerçek kehanet mi?",
             ["Eğlence ve kişisel içgörü. Astrype geleceği önceden bildirmez ve hiçbir "
              "şeyi kesin kader gibi sunmaz; yorumlar üzerine düşünülecek bir ayna "
              "olarak yazılır. Profesyonel tıbbi, hukuki, finansal veya güvenlik "
              "tavsiyesinin yerine geçmez."]),
            ("Kahve, el ve yüz falı fotoğraflarım saklanıyor mu?",
             ["Hayır. Fotoğraf yalnızca analiz için kullanılır ve hemen ardından "
              "sunucudan silinir. Saklanmaz, paylaşılmaz ve arşivine eklenmez. "
              "Hesabına yalnızca metin sonucu ve okunan sembollerin listesi kaydedilir."]),
            ("Aboneliğimi nasıl iptal ederim?",
             ["Uygulamadan değil, mağazadan: iOS'ta App Store hesabı &rarr; "
              "Abonelikler, Android'de Google Play &rarr; Ödemeler ve abonelikler "
              "&rarr; Abonelikler. Bir sonraki yenilemeyi önlemek için dönem "
              "bitiminden en az 24 saat önce iptal et."]),
            ("Satın almalarımı nasıl geri yüklerim?",
             ["Uygulamada Premium / Yıldız Tozu ekranını aç ve “Geri "
              "yükle” ye dokun. Satın almalar, yapıldıkları mağaza hesabına geri "
              "yüklenir; aynı Apple ID veya Google hesabıyla giriş yaptığından emin ol."]),
            ("Astrype hangi dilleri konuşuyor?",
             ["Uygulama 20 dilde: Türkçe, İngilizce, Azerbaycanca, Almanca, "
              "İspanyolca, Fransızca, İtalyanca, Felemenkçe, Lehçe, Portekizce, "
              "Rusça, Ukraynaca, Arapça, Farsça, Urduca, Hintçe, Endonezce, Japonca, "
              "Korece ve Çince. Profil &rarr; Dil'den istediğin zaman "
              "değiştirebilirsin.",
              "Bu web sitesi Türkçe ve İngilizce; yasal sayfalar desteklenen tüm "
              "dillerde mevcut."]),
            ("Doğum verilerim gizli mi?",
             ["Doğum tarihin, saatin ve yerin haritanı hesaplamak ve yorumlarını "
              "kişiselleştirmek için kullanılır ve yalnızca senin erişebildiğin kendi "
              "hesabında saklanır. İstediğin zaman hesabınla birlikte silebilirsin. "
              "Ayrıntılar Gizlilik Politikası'nda."]),
            ("Doğum saatimi tam bilmiyorsam ne olur?",
             ["Astrype'ı yine kullanabilirsin. Doğum saatinin önemli olduğu yerlerde "
              "uygulama bunu açıkça söyler — yükselen hesaplanamayabilir, uyum "
              "yaklaşık olur, İnsan Tasarımı tipi değişebilir — ama dakikaya "
              "bağlı olmayan her şey çalışır."]),
        ],
        "sup_back": "Ana sayfaya dön",
    },
}


# --------------------------------------------------------------------------
# Yapı taşları
# --------------------------------------------------------------------------


def _head(title: str, description: str, lang: str, canonical_path: str) -> str:
    t = TEXTS[lang]
    return f"""<!doctype html><html lang="{lang}" dir="{t["dir"]}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:image" content="/static/img/icon.png">
<link rel="icon" href="/static/img/icon.png" type="image/png">
<link rel="apple-touch-icon" href="/static/img/icon.png">
<link rel="canonical" href="https://astrype.com{canonical_path}">
<link rel="alternate" hreflang="en" href="https://astrype.com{canonical_path}?lang=en">
<link rel="alternate" hreflang="tr" href="https://astrype.com{canonical_path}?lang=tr">
{_FONTS}
<style>{_STYLE}</style>
</head>
<body>"""


def _header(lang: str, page: str) -> str:
    t = TEXTS[lang]
    other = "tr" if lang == "en" else "en"
    path = "/support" if page == "support" else "/"
    sup_cur = ' aria-current="page"' if page == "support" else ""
    return f"""<header class="site"><div class="wrap"><div class="bar">
<a class="brand" href="/?lang={lang}">
<img src="/static/img/icon.png" alt="" width="32" height="32">
<span>Astrype</span></a>
<nav class="navlinks" aria-label="{t["langs_label"]}">
<a href="/support?lang={lang}"{sup_cur}>{t["nav_support"]}</a>
<a href="/legal/privacy?lang={lang}">{t["nav_privacy"]}</a>
<a href="/legal/terms?lang={lang}">{t["nav_terms"]}</a>
<span class="sep" aria-hidden="true">|</span>
<a href="{path}?lang={lang}" lang="{lang}" hreflang="{lang}" aria-current="true">{TEXTS[lang]["native"]}</a>
<a href="{path}?lang={other}" lang="{other}" hreflang="{other}">{TEXTS[other]["native"]}</a>
</nav></div></div></header>"""


def _stores(lang: str) -> str:
    """Yayına çıkınca APP_STORE_URL / PLAY_STORE_URL doldurulur; gerisi otomatik."""
    t = TEXTS[lang]
    items = []
    for url, name, top in (
        (APP_STORE_URL, t["store_soon_apple"], t["store_live_top"]),
        (PLAY_STORE_URL, t["store_soon_google"], t["store_live_top_g"]),
    ):
        if url:
            items.append(
                f'<li><a class="badge" href="{url}" rel="noopener">'
                f"<small>{top}</small><b>{name}</b></a></li>"
            )
        else:
            items.append(
                f'<li><span class="badge"><small>{t["store_soon_title"]}</small>'
                f"<b>{name}</b></span></li>"
            )
    note = "" if (APP_STORE_URL and PLAY_STORE_URL) else f'<p class="storenote">{t["store_note"]}</p>'
    return f'<ul class="stores">{"".join(items)}</ul>{note}'


def _footer(lang: str) -> str:
    t = TEXTS[lang]
    return f"""<footer class="site"><div class="wrap">
<ul class="footlinks">
<li><a href="/support?lang={lang}">{t["foot_support"]}</a></li>
<li><a href="/legal/privacy?lang={lang}">{t["foot_privacy"]}</a></li>
<li><a href="/legal/terms?lang={lang}">{t["foot_terms"]}</a></li>
<li><a href="/legal/source">{t["foot_source"]}</a></li>
<li>{t["foot_contact"]}: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
</ul>
<p class="disclaimer">{t["disclaimer"]}</p>
<p class="disclaimer">&copy; Astrype</p>
</div></footer>
</body></html>"""


# --------------------------------------------------------------------------
# Sayfalar
# --------------------------------------------------------------------------


def render_home(lang: str) -> str:
    t = TEXTS[lang]
    hero_shot = f"{lang}-2.jpg"
    lyra_shot = f"{lang}-3.jpg"

    cards = "\n".join(
        f'<article class="card"><div class="glyph" aria-hidden="true">{glyph}</div>'
        f"<h3>{name}</h3><p>{body}</p></article>"
        for glyph, name, body in t["features"]
    )
    shots = "\n".join(
        f'<figure><img src="/static/img/{src}" alt="{alt}" width="600" height="1300" loading="lazy"></figure>'
        for src, alt in t["shots"]
    )
    lyra = "\n".join(f"<p>{p}</p>" for p in t["lyra_body"])
    priv = "\n".join(f"<p>{p}</p>" for p in t["privacy_body"])
    points = "\n".join(f"<li>{p}</li>" for p in t["privacy_points"])
    plans = "\n".join(f"<p>{p}</p>" for p in t["plans_body"])

    return f"""{_head(t["home_title"], t["home_desc"], lang, "/")}
{_header(lang, "home")}
<main>
<div class="hero"><div class="wrap"><div class="hero-grid">
<div>
<p class="overline">{t["hero_overline"]}</p>
<h1>{t["hero_h1_a"]}<br><em>{t["hero_h1_b"]}</em></h1>
<p class="lede">{t["hero_lede"]}</p>
{_stores(lang)}
</div>
<div class="hero-shot"><img src="/static/img/{hero_shot}" alt="{t["hero_shot_alt"]}" width="600" height="1300"></div>
</div></div></div>

<section id="features"><div class="wrap">
<h2>{t["f_title"]}</h2>
<p class="sub">{t["f_sub"]}</p>
<div class="cards">
{cards}
</div>
</div></section>

<section id="lyra"><div class="wrap"><div class="split">
<div>
<h2>{t["lyra_title"]}</h2>
{lyra}
</div>
<div class="shot"><img src="/static/img/{lyra_shot}" alt="{t["lyra_alt"]}" width="600" height="1300" loading="lazy"></div>
</div></div></section>

<section id="privacy"><div class="wrap narrow">
<h2>{t["privacy_title"]}</h2>
{priv}
<ul class="plain">
{points}
</ul>
</div></section>

<section id="screens"><div class="wrap">
<h2>{t["shots_title"]}</h2>
<div class="shots">
{shots}
</div>
</div></section>

<section id="plans"><div class="wrap narrow">
<h2>{t["plans_title"]}</h2>
{plans}
<p class="note">{t["disclaimer"]}</p>
</div></section>
</main>
{_footer(lang)}"""


def render_support(lang: str) -> str:
    t = TEXTS[lang]
    steps = "\n".join(f"<li>{s}</li>" for s in t["sup_delete_steps"])
    faq = "\n".join(
        "<details><summary>{q}</summary><div class=\"answer\">{a}</div></details>".format(
            q=q, a="".join(f"<p>{p}</p>" for p in answers)
        )
        for q, answers in t["faq"]
    )
    return f"""{_head(t["support_title"], t["support_desc"], lang, "/support")}
{_header(lang, "support")}
<main>
<div class="hero"><div class="wrap narrow">
<p class="overline">{t["sup_overline"]}</p>
<h1>{t["sup_h1_a"]}<br><em>{t["sup_h1_b"]}</em></h1>
<p class="lede">{t["sup_lede"]}</p>
</div></div>

<section id="contact"><div class="wrap narrow">
<h2>{t["sup_contact_title"]}</h2>
<p>{t["sup_contact_body"]}</p>
<div class="contactbox">
<a class="mail" href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
</div>
</div></section>

<section id="about"><div class="wrap narrow">
<h2>{t["sup_what_title"]}</h2>
<p>{t["sup_what_body"]}</p>
<p class="note">{t["disclaimer"]}</p>
</div></section>

<section id="delete"><div class="wrap narrow">
<h2>{t["sup_delete_title"]}</h2>
<p>{t["sup_delete_body"]}</p>
<ul class="plain">
{steps}
</ul>
</div></section>

<section id="subscriptions"><div class="wrap narrow">
<h2>{t["sup_subs_title"]}</h2>
<p>{t["sup_subs_body"]}</p>
<ul class="plain">
<li><a href="{APPLE_SUBSCRIPTIONS_URL}" rel="noopener">{t["sup_subs_apple"]}</a></li>
<li><a href="{GOOGLE_SUBSCRIPTIONS_URL}" rel="noopener">{t["sup_subs_google"]}</a></li>
</ul>
</div></section>

<section id="faq"><div class="wrap narrow">
<h2>{t["sup_faq_title"]}</h2>
{faq}
<p style="margin-top:28px"><a href="/?lang={lang}">&larr; {t["sup_back"]}</a></p>
</div></section>
</main>
{_footer(lang)}"""


# İçerik statik — açılışta bir kez üretilir.
_PAGES: dict[tuple[str, str], str] = {
    ("home", code): render_home(code) for code in SITE_LANGS
}
_PAGES.update({("support", code): render_support(code) for code in SITE_LANGS})


def resolve_site_lang(query_lang: str | None, accept_language: str | None) -> str:
    """Yasal sayfalarla aynı çözümleme; site yalnızca tr/en olduğu için
    diğer tüm diller İngilizce'ye düşer."""
    code = resolve_lang(query_lang, accept_language)
    return code if code in SITE_LANGS else SITE_DEFAULT_LANG


def _respond(kind: str, lang: str | None, accept_language: str | None) -> HTMLResponse:
    code = resolve_site_lang(lang, accept_language)
    return HTMLResponse(
        _PAGES[(kind, code)],
        headers={"Content-Language": code, "Vary": "Accept-Language"},
    )


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing(
    lang: str | None = Query(None),
    accept_language: str | None = Header(None),
) -> HTMLResponse:
    return _respond("home", lang, accept_language)


@router.get("/support", response_class=HTMLResponse, include_in_schema=False)
async def support(
    lang: str | None = Query(None),
    accept_language: str | None = Header(None),
) -> HTMLResponse:
    return _respond("support", lang, accept_language)

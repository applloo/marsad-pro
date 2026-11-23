# -*- coding: utf-8 -*-
"""قوائم المصادر: (الاسم، الدومين — يمكن فصل أكثر من دومين بـ |، اللغة he/en/both)"""
import re

ISRAEL = {
    "📰 الصحف والمواقع": [
        ("هآرتس (عبري)", "haaretz.co.il", "he"),
        ("هآرتس (إنجليزي)", "haaretz.com", "en"),
        ("يديعوت أحرونوت / Ynet (عبري)", "ynet.co.il", "he"),
        ("Ynetnews (إنجليزي)", "ynetnews.com", "en"),
        ("معاريف", "maariv.co.il", "he"),
        ("إسرائيل هيوم (عبري)", "israelhayom.co.il", "he"),
        ("Israel Hayom (إنجليزي)", "israelhayom.com", "en"),
        ("جيروزاليم بوست", "jpost.com", "en"),
        ("تايمز أوف إسرائيل", "timesofisrael.com", "en"),
        ("ماكور ريشون", "makorrishon.co.il", "he"),
        ("واللا", "walla.co.il", "he"),
        ("غلوبس", "globes.co.il", "he"),
        ("كالكاليست", "calcalist.co.il", "he"),
        ("نتسيف (נציב)", "nziv.net", "he"),
    ],
    "🛡️ أمن ودفاع واستخبارات": [
        ("MEMRI (ترجمات الإعلام العبري والعربي)", "memri.org", "en"),
        ("JNS (Jewish News Syndicate)", "jns.org", "en"),
        ("Israel Defense (عبري)", "israeldefense.co.il", "he"),
        ("Israel Defense (إنجليزي)", "israeldefense.com", "en"),
        ("DEBKAfile", "debka.com", "en"),
    ],
    "📺 القنوات والإذاعة": [
        ("كان 11 – هيئة البث", "kan.org.il", "both"),
        ("القناة 12 – مكو", "mako.co.il", "he"),
        ("القناة 13", "13tv.co.il", "he"),
        ("القناة 14", "now14.co.il", "he"),
        ("i24NEWS", "i24news.tv", "both"),
        ("القناة 7 – عروتس شيفع (عبري)", "inn.co.il", "he"),
        ("Arutz Sheva (إنجليزي)", "israelnationalnews.com", "en"),
    ],
}

USA = {
    "🇺🇸 إعلام أمريكي مهتم بالشرق الأوسط": [
        ("Axios", "axios.com", "en"),
        ("Al-Monitor", "al-monitor.com", "en"),
        ("Foreign Policy", "foreignpolicy.com", "en"),
        ("Politico", "politico.com", "en"),
        ("The New York Times", "nytimes.com", "en"),
        ("The Washington Post", "washingtonpost.com", "en"),
        ("The Wall Street Journal", "wsj.com", "en"),
        ("CNN", "cnn.com", "en"),
        ("Fox News", "foxnews.com", "en"),
        ("The Hill", "thehill.com", "en"),
        ("NPR", "npr.org", "en"),
        ("AP News", "apnews.com", "en"),
        ("Jewish Insider", "jewishinsider.com", "en"),
        ("The Intercept", "theintercept.com", "en"),
        ("Bloomberg", "bloomberg.com", "en"),
        ("Reuters", "reuters.com", "en"),
        ("MSNBC", "msnbc.com", "en"),
    ],
    "🏛️ مراكز أبحاث ومجلات متخصصة": [
        ("Foreign Affairs", "foreignaffairs.com", "en"),
        ("Washington Institute", "washingtoninstitute.org", "en"),
        ("Middle East Institute", "mei.edu", "en"),
        ("Atlantic Council", "atlanticcouncil.org", "en"),
        ("Council on Foreign Relations", "cfr.org", "en"),
        ("Brookings", "brookings.edu", "en"),
        ("Defense One", "defenseone.com", "en"),
        ("Quincy Institute", "quincyinst.org", "en"),
        ("CSIS", "csis.org", "en"),
        ("Baker Institute (Rice)", "bakerinstitute.org", "en"),
    ],
    "🛰️ دفاع وأمن وتحقيقات مفتوحة": [
        ("Defense News", "defensenews.com", "en"),
        ("Breaking Defense", "breakingdefense.com", "en"),
        ("The War Zone", "twz.com", "en"),
        ("War on the Rocks", "warontherocks.com", "en"),
        ("Institute for the Study of War", "understandingwar.org", "en"),
        ("Bellingcat", "bellingcat.com", "en"),
        ("Lawfare", "lawfaremedia.org", "en"),
        ("Just Security", "justsecurity.org", "en"),
        ("Semafor", "semafor.com", "en"),
    ],
    "🌍 صحافة دولية ناطقة بالإنجليزية": [
        ("The National", "thenationalnews.com", "en"),
        ("Arab News", "arabnews.com", "en"),
        ("Al Jazeera English", "aljazeera.com", "en"),
        ("The New Humanitarian", "thenewhumanitarian.org", "en"),
        ("Deutsche Welle (DW)", "dw.com", "en"),
        ("France 24", "france24.com", "en"),
        ("Euronews", "euronews.com", "en"),
        ("Agence France-Presse (AFP)", "afp.com", "en"),
    ],
}

UK = {
    "🇬🇧 صحف وقنوات بريطانية": [
        ("BBC", "bbc.com|bbc.co.uk", "en"),
        ("The Guardian", "theguardian.com", "en"),
        ("Financial Times", "ft.com", "en"),
        ("The Telegraph", "telegraph.co.uk", "en"),
        ("The Times", "thetimes.co.uk|thetimes.com", "en"),
        ("The Independent", "independent.co.uk", "en"),
        ("Sky News", "news.sky.com", "en"),
        ("Reuters", "reuters.com", "en"),
        ("The Economist", "economist.com", "en"),
    ],
    "🌍 مصادر بريطانية متخصصة بالشرق الأوسط": [
        ("Middle East Eye", "middleeasteye.net", "en"),
        ("The New Arab", "newarab.com", "en"),
        ("Middle East Monitor", "middleeastmonitor.com", "en"),
        ("Chatham House", "chathamhouse.org", "en"),
        ("Jewish Chronicle", "thejc.com", "en"),
        ("RUSI", "rusi.org", "en"),
        ("openDemocracy", "opendemocracy.net", "en"),
        ("France 24 (إنجليزي)", "france24.com", "en"),
        ("IISS – المعهد الدولي للدراسات الاستراتيجية", "iiss.org", "en"),
        ("The Africa Report", "theafricareport.com", "en"),
    ],
}

# أقسام جاهزة للتصفح: الدومين ← [(اسم القسم، الرابط، نوع المحتوى الغالب: رأي/تحليل/None)]
SECTIONS = {
    "haaretz.com": [("الرأي", "https://www.haaretz.com/opinion", "رأي"), ("أخبار إسرائيل", "https://www.haaretz.com/israel-news", None),
                    ("الشرق الأوسط", "https://www.haaretz.com/middle-east-news", None)],
    "haaretz.co.il": [("الرأي", "https://www.haaretz.co.il/opinions", "رأي"), ("الأخبار", "https://www.haaretz.co.il/news", None)],
    "timesofisrael.com": [("الرأي", "https://www.timesofisrael.com/opinions/", "رأي"), ("البث المباشر", "https://www.timesofisrael.com/liveblog/", None)],
    "jpost.com": [("الرأي", "https://www.jpost.com/opinion", "رأي"), ("الشرق الأوسط", "https://www.jpost.com/middle-east", None),
                  ("الأمن والدفاع", "https://www.jpost.com/israel-news/defense-news", None)],
    "ynetnews.com": [("الصفحة الرئيسية", "https://www.ynetnews.com/", None)],
    "nytimes.com": [("الرأي", "https://www.nytimes.com/section/opinion", "رأي"), ("الشرق الأوسط", "https://www.nytimes.com/section/world/middleeast", None)],
    "washingtonpost.com": [("الرأي", "https://www.washingtonpost.com/opinions/", "رأي"), ("الشرق الأوسط", "https://www.washingtonpost.com/world/middle-east/", None)],
    "theguardian.com": [("الرأي", "https://www.theguardian.com/commentisfree", "رأي"), ("الشرق الأوسط", "https://www.theguardian.com/world/middleeast", None)],
    "bbc.com": [("الشرق الأوسط", "https://www.bbc.com/news/world/middle_east", None)],
    "axios.com": [("العالم", "https://www.axios.com/world", None)],
    "foreignpolicy.com": [("تحليلات", "https://foreignpolicy.com/category/analysis/", "تحليل")],
    "ft.com": [("الرأي", "https://www.ft.com/opinion", "رأي"), ("الشرق الأوسط", "https://www.ft.com/middle-east-north-africa", None)],
    "economist.com": [("الشرق الأوسط وأفريقيا", "https://www.economist.com/middle-east-and-africa", None)],
    "telegraph.co.uk": [("الرأي", "https://www.telegraph.co.uk/opinion/", "رأي"), ("الشرق الأوسط", "https://www.telegraph.co.uk/news/world/middle-east/", None)],
    "middleeasteye.net": [("الرأي", "https://www.middleeasteye.net/opinion", "رأي")],
    "cnn.com": [("الشرق الأوسط", "https://edition.cnn.com/world/middle-east", None)],
    "apnews.com": [("الشرق الأوسط", "https://apnews.com/hub/middle-east", None)],
    "reuters.com": [("الشرق الأوسط", "https://www.reuters.com/world/middle-east/", None)],
    "al-monitor.com": [("الصفحة الرئيسية", "https://www.al-monitor.com/", None)],
}

# ───────── مصادر إضافية: جهات رسمية، دفاع، استخبارات مفتوحة، وآسيا وأوروبا ─────────
ISRAEL["🏛️ جهات رسمية ومراكز أبحاث إضافية"] = [
    ("الجيش الإسرائيلي IDF", "idf.il", "both"), ("وزارة الدفاع الإسرائيلية", "mod.gov.il", "en"),
    ("بوابة الحكومة الإسرائيلية (الأمن القومي والخارجية)", "gov.il", "en"),
    ("معهد الديمقراطية الإسرائيلي", "idi.org.il", "he,en"), ("منتدى السياسة الإسرائيلية", "israelpolicyforum.org", "en"),
]
USA["🏛️ الحكومة والكونجرس والأمن القومي"] = [
    ("وزارة الدفاع الأمريكية Pentagon", "defense.gov", "en"), ("وزارة الخارجية الأمريكية", "state.gov", "en"),
    ("البيت الأبيض", "whitehouse.gov", "en"), ("مكتب مدير الاستخبارات الوطنية ODNI", "odni.gov", "en"),
    ("بوابة مجتمع الاستخبارات الأمريكي", "intelligence.gov", "en"), ("وكالة الأمن القومي NSA", "nsa.gov", "en"),
    ("وكالة الاستخبارات الجغرافية المكانية NGA", "nga.mil", "en"),
    ("وكالة الاستخبارات المركزية CIA", "cia.gov", "en"), ("وكالة استخبارات الدفاع DIA", "dia.mil", "en"),
    ("البحرية الأمريكية USNI News", "news.usni.org", "en"), ("مؤسسة جيمستاون", "jamestown.org", "en"),
    ("معهد هدسون", "hudson.org", "en"), ("مؤسسة كارنيجي للسلام الدولي", "carnegieendowment.org", "en"),
    ("معهد نيو لاينز", "newlinesinstitute.org", "en"), ("DefenseScoop", "defensescoop.com", "en"),
    ("C4ISRNET", "c4isrnet.com", "en"), ("Air & Space Forces Magazine", "airandspaceforces.com", "en"),
    ("Army Times", "armytimes.com", "en"), ("Stars and Stripes", "stripes.com", "en"),
]
UK["🏛️ الحكومة والدفاع والبرلمان"] = [
    ("الحكومة البريطانية (وزارة الدفاع والخارجية FCDO)", "gov.uk", "en"),
    ("المركز الوطني للأمن السيبراني NCSC", "ncsc.gov.uk", "en"),
    ("جهاز الاستخبارات الخارجية البريطاني SIS / MI6", "sis.gov.uk", "en"),
    ("جهاز الأمن الداخلي البريطاني MI5", "mi5.gov.uk", "en"),
    ("مقر الاتصالات الحكومية GCHQ", "gchq.gov.uk", "en"),
    ("مكتبة مجلس العموم البريطاني", "commonslibrary.parliament.uk", "en"),
    ("UK Defence Journal", "ukdefencejournal.org.uk", "en"), ("Forces News", "forcesnews.com", "en"),
    ("Jane's Defence", "janes.com", "en"),
]
INTERNATIONAL = {
    "🇪🇺 أوروبا": [("دير شبيجل", "spiegel.de", "en"), ("لوموند", "lemonde.fr", "en"),
                  ("Politico Europe", "politico.eu", "en"), ("فرانس 24", "france24.com", "both")],
    "🇨🇳 الصين وشرق آسيا": [("شينخوا", "xinhuanet.com", "en"), ("جلوبال تايمز", "globaltimes.cn", "en"),
                         ("CGTN", "cgtn.com", "en"), ("تشاينا ديلي", "chinadaily.com.cn", "en"),
                         ("ساوث تشاينا مورنينج بوست", "scmp.com", "en"), ("نيكاي آسيا", "asia.nikkei.com", "en"),
                         ("NHK World", "nhk.or.jp", "en"), ("يونهاب", "yna.co.kr", "en")],
    "🇷🇺 روسيا وأوراسيا": [("تاس TASS", "tass.com", "en"), ("إنترفاكس", "interfax.com", "en"),
                         ("ميدوزا", "meduza.io", "en"), ("آر بي سي", "rbc.ru", "en")],
    "🌍 أفريقيا والقرن الأفريقي": [("أفريكا كونفيدينشال", "africa-confidential.com", "en"),
                                  ("أفريكا إنتليجنس", "africaintelligence.com", "en"),
                                  ("Daily Maverick", "dailymaverick.co.za", "en"),
                                  ("The EastAfrican", "theeastafrican.co.ke", "en")],
    "🌐 مؤسسات دولية وبيانات": [("الأمم المتحدة أخبار", "news.un.org", "en,ar"),
                              ("الوكالة الدولية للطاقة الذرية IAEA", "iaea.org", "en"),
                              ("المنظمة البحرية الدولية IMO", "imo.org", "en"),
                              ("منظمة حظر الأسلحة الكيميائية OPCW", "opcw.org", "en"),
                              ("مفوضية الأمم المتحدة لحقوق الإنسان OHCHR", "ohchr.org", "en")],
}

# صحف عربية (للمقارنة داخل مكتب الاستخبارات): (الاسم، الدومين، "ar")
ARABIC = {
    "🇪🇬 صحف مصرية": [
        ("الأهرام", "ahram.org.eg", "ar"),
        ("المصري اليوم", "almasryalyoum.com", "ar"),
        ("اليوم السابع", "youm7.com", "ar"),
        ("الشروق", "shorouknews.com", "ar"),
        ("الوطن", "elwatannews.com", "ar"),
        ("مدى مصر", "madamasr.com", "ar"),
    ],
    "🌍 صحف وقنوات عربية": [
        ("الشرق الأوسط", "aawsat.com", "ar"),
        ("العربية", "alarabiya.net", "ar"),
        ("الجزيرة", "aljazeera.net", "ar"),
        ("القدس العربي", "alquds.co.uk", "ar"),
        ("العربي الجديد", "alaraby.co.uk", "ar"),
        ("الأخبار اللبنانية", "al-akhbar.com", "ar"),
        ("الميادين", "almayadeen.net", "ar"),
        ("إندبندنت عربية", "independentarabia.com", "ar"),
        ("سكاي نيوز عربية", "skynewsarabia.com", "ar"),
        ("الاتحاد الإماراتية", "alittihad.ae", "ar"),
        ("الخليج", "alkhaleej.ae", "ar"),
        ("عكاظ", "okaz.com.sa", "ar"),
        ("الشرق", "asharq.com", "ar"),
    ],
}
# ───────── الشأن المصري: مصادر مصرية فقط (حوادث ومجتمع واقتصاد وقوانين وحدود) ─────────
EGYPT = {
    "📰 صحف ومواقع إخبارية مصرية": [
        ("القاهرة 24", "cairo24.com", "ar"),
        ("اليوم السابع", "youm7.com", "ar"),
        ("المصري اليوم", "almasryalyoum.com", "ar"),
        ("الأهرام", "ahram.org.eg", "ar"),
        ("الشروق", "shorouknews.com", "ar"),
        ("الوطن", "elwatannews.com", "ar"),
        ("مصراوي", "masrawy.com", "ar"),
        ("صدى البلد", "elbalad.news", "ar"),
        ("الدستور", "dostor.org", "ar"),
        ("الفجر", "elfagr.org", "ar"),
        ("البوابة نيوز", "albawabhnews.com", "ar"),
        ("أخبار اليوم", "akhbarelyom.com", "ar"),
        ("الجمهورية", "gomhuriaonline.com", "ar"),
        ("الوفد", "alwafd.news", "ar"),
        ("المنصة", "almanassa.com", "ar"),
        ("مدى مصر", "madamasr.com", "ar"),
        ("تليجراف مصر", "egypttelegraph.com", "ar"),
    ],
    "💰 اقتصاد وأعمال": [
        ("أموال الغد", "amwalalghad.com", "ar"),
        ("البورصة", "alborsaanews.com", "ar"),
        ("المال", "almalnews.com", "ar"),
    ],
    "🏛️ رسمي وحكومي": [
        ("رئاسة الجمهورية", "presidency.eg", "ar"),
        ("الهيئة العامة للاستعلامات", "sis.gov.eg", "ar"),
    ],
    "🌍 القنوات العربية — تغطيتها لمصر بس": [
        ("العربية مصر", "alarabiya.net", "ar"),
        ("الحدث مصر", "alhadath.net", "ar"),
        ("الجزيرة مصر", "aljazeera.net", "ar"),
        ("العربي الجديد مصر", "alaraby.co.uk", "ar"),
        ("سكاي نيوز عربية مصر", "skynewsarabia.com", "ar"),
    ],
}
ARAB_EG_GROUP = "🌍 القنوات العربية — تغطيتها لمصر بس"
ARAB_EG_DOMAINS = {d for _l, d, _lg in EGYPT[ARAB_EG_GROUP]}
EG_WORDS = re.compile(r"مصر|المصري|المصرية|مصريين|القاهر|الجيزة|الإسكندرية|الاسكندرية|السيسي|سيناء|رفح|egypt|cairo|/egypt|from_egypt", re.I)


def egypt_only(items):
    """أخبار القنوات العربية بتيجي كل أخبارها، فبنسيب بس اللي عن مصر (من العنوان أو الرابط). باقي المصادر زي ما هي"""
    out = []
    for a in items:
        d = (a.get("domain") or "").lower().replace("www.", "")
        if any(d == x or d.endswith("." + x) for x in ARAB_EG_DOMAINS):
            blob = f"{a.get('title', '')} {a.get('title_ar', '')} {a.get('url', '')}"
            if not EG_WORDS.search(blob):
                continue
        out.append(a)
    return out
EGYPT_ARABIC = {"ahram.org.eg", "almasryalyoum.com", "youm7.com", "shorouknews.com", "elwatannews.com", "madamasr.com"} | {
    d for _k, g in EGYPT.items() if _k != ARAB_EG_GROUP for _l, d, _lg in g}

# ───────── القرن الأفريقي وتركيا وإيران (لغات: am أمهري، tr تركي، fa فارسي، en إنجليزي؛ يجوز الجمع "tr,en") ─────────
REGION = {
    "🇪🇹 إثيوبيا (القرن الأفريقي وسد النهضة)": [
        ("فانا للإعلام (FBC)", "fanabc.com", "am,en"),
        ("وكالة الأنباء الإثيوبية (ENA)", "ena.et", "am,en"),
        ("ريبورتر (أمهري)", "ethiopianreporter.com", "am"),
        ("ذا ريبورتر (إنجليزي)", "thereporterethiopia.com", "en"),
        ("أديس ستاندرد", "addisstandard.com", "en"),
        ("هيئة الإذاعة الإثيوبية (EBC)", "ebc.et", "am,en"),
        ("والتا إنفو", "waltainfo.com", "am,en"),
        ("أديس فورتشن", "addisfortune.news", "en"),
        ("إثيوبيا إنسايت", "ethiopia-insight.com", "en"),
        ("بوركينا (Borkena)", "borkena.com", "en"),
        ("كابيتال إثيوبيا", "capitalethiopia.com", "en"),
        ("سودان تريبيون", "sudantribune.com", "en"),
    ],
    "🇹🇷 تركيا (شرق المتوسط والمشرق)": [
        ("الأناضول (AA)", "aa.com.tr", "tr,en"),
        ("صباح", "sabah.com.tr", "tr"),
        ("ديلي صباح (إنجليزي)", "dailysabah.com", "en"),
        ("يني شفق", "yenisafak.com", "tr"),
        ("حرييت", "hurriyet.com.tr", "tr"),
        ("حرييت ديلي نيوز (إنجليزي)", "hurriyetdailynews.com", "en"),
        ("TRT هابر", "trthaber.com", "tr"),
        ("TRT وورلد (إنجليزي)", "trtworld.com", "en"),
        ("ميلليت", "milliyet.com.tr", "tr"),
        ("هابرترك", "haberturk.com", "tr"),
        ("جمهورييت (معارضة)", "cumhuriyet.com.tr", "tr"),
        ("سوزجو (معارضة)", "sozcu.com.tr", "tr"),
        ("ستار", "star.com.tr", "tr"),
        ("يني عقد", "yeniakit.com.tr", "tr"),
        ("أيدينلك (أوراسي)", "aydinlik.com.tr", "tr"),
        ("سيتا SETA (مركز أبحاث)", "setav.org", "tr,en"),
    ],
    "🇮🇷 إيران (اليمن والخليج والمحور)": [
        ("تسنيم", "tasnimnews.com", "fa,en"),
        ("فارس", "farsnews.ir", "fa,en"),
        ("إيرنا (IRNA)", "irna.ir", "fa,en"),
        ("مهر", "mehrnews.com", "fa,en"),
        ("إيسنا (ISNA)", "isna.ir", "fa"),
        ("تابناك", "tabnak.ir", "fa"),
        ("نور نيوز (المجلس الأعلى للأمن القومي)", "nournews.ir", "fa"),
        ("جوان (الحرس الثوري)", "javanonline.ir", "fa"),
        ("كيهان", "kayhan.ir", "fa"),
        ("ميزان (السلطة القضائية)", "mizanonline.ir", "fa"),
        ("خامنئي.ir (موقع المرشد)", "khamenei.ir", "fa,en,ar"),
        ("برس تي في", "presstv.ir", "en"),
        ("طهران تايمز", "tehrantimes.com", "en"),
        ("إيران ديلي", "irandaily.ir", "en"),
        ("قناة العالم (عربي)", "alalam.ir", "ar"),
        ("إيران إنترناشيونال (معارضة)", "iranintl.com", "fa,en"),
    ],
}


REGION.update(INTERNATIONAL)
REGION.update({
    "🇸🇩 السودان وجنوب السودان": [
        ("سودان تريبيون", "sudantribune.com", "en"), ("راديو دبنقا", "dabangasudan.org", "en,ar"),
        ("راديو تمازج", "radiotamazuj.org", "en"), ("سودان وور مونيتور", "sudanwarmonitor.com", "en"),
        ("سودان بوست", "sudanpost.info", "en"),
    ],
    "🇸🇴 الصومال والقرن الأفريقي": [
        ("Garowe Online", "garoweonline.com", "en"), ("Hiiraan Online", "hiiraan.com", "en"),
        ("Somali Guardian", "somaliguardian.com", "en"), ("وكالة الأنباء الصومالية SONNA", "sonna.so", "en"),
    ],
    "🇾🇪 اليمن والبحر الأحمر": [
        ("يمن مونيتور", "yemenmonitor.com", "en,ar"), ("مركز صنعاء للدراسات الاستراتيجية", "sanaacenter.org", "en"),
        ("مركز سوث24 للأخبار والدراسات", "south24.net", "both"),
    ],
    "🇮🇶 العراق وكردستان": [
        ("روداو", "rudaw.net", "en"), ("شفق نيوز", "shafaq.com", "en,ar"),
        ("Iraqi News", "iraqinews.com", "en"), ("الوكالة الوطنية العراقية NINA", "ninanews.com", "en"),
        ("كردستان 24", "kurdistan24.net", "en"),
    ],
    "🇱🇧 لبنان وسوريا والأردن": [
        ("نهارنت", "naharnet.com", "en"), ("لوريان لوجور / L'Orient Today", "lorientlejour.com", "en"),
        ("The Syrian Observer", "syrianobserver.com", "en"), ("عنب بلدي", "enabbaladi.net", "ar"),
        ("سانا السورية", "sana.sy", "ar"), ("The Jordan Times", "jordantimes.com", "en"),
        ("عمون", "ammonews.net", "ar"),
    ],
    "🇬🇨 الخليج ووكالات الأنباء الرسمية": [
        ("وكالة الأنباء القطرية QNA", "qna.org.qa", "en"), ("وكالة الأنباء العمانية ONA", "omannews.gov.om", "en"),
        ("وكالة الأنباء الكويتية KUNA", "kuna.net.kw", "en"), ("وكالة الأنباء السعودية SPA", "spa.gov.sa", "en"),
        ("وكالة أنباء الإمارات WAM", "wam.ae", "en"), ("وكالة أنباء البحرين BNA", "bna.bh", "en"),
        ("The Peninsula Qatar", "thepeninsulaqatar.com", "en"), ("Gulf Times", "gulf-times.com", "en"),
        ("Amwaj Media", "amwaj.media", "en"),
    ],
    "🇩🇯 إريتريا وجيبوتي وليبيا": [
        ("شبايت (إريتريا الرسمية)", "shabait.com", "en"), ("أسمارينو", "asmarino.com", "en"),
        ("The Djibouti Post", "thedjiboutipost.com", "en"), ("La Voix de Djibouti", "lavoixdedjibouti.info", "fr"),
        ("Libya Observer", "libyaobserver.ly", "en"),
    ],
})


# ───────── بلد كل مصدر (لإظهاره بجانب اسمه في كل مكان) ─────────
FLAGS = {"إسرائيل": "🇮🇱", "أمريكا": "🇺🇸", "بريطانيا": "🇬🇧", "مصر": "🇪🇬", "السعودية": "🇸🇦", "الإمارات": "🇦🇪", "قطر": "🇶🇦",
         "لبنان": "🇱🇧", "تركيا": "🇹🇷", "إيران": "🇮🇷", "إثيوبيا": "🇪🇹", "فرنسا": "🇫🇷", "السويد": "🇸🇪", "بلجيكا": "🇧🇪",
         "جنوب أفريقيا": "🇿🇦", "هولندا": "🇳🇱", "الأمم المتحدة": "🇺🇳", "أوروبا": "🇪🇺", "السودان": "🇸🇩", "سويسرا": "🇨🇭", "دولي": "🌐", "الصين": "🇨🇳", "اليابان": "🇯🇵", "كوريا الجنوبية": "🇰🇷", "روسيا": "🇷🇺", "هونغ كونغ": "🇭🇰", "كينيا": "🇰🇪", "الصومال": "🇸🇴", "اليمن": "🇾🇪", "العراق": "🇮🇶", "لبنان": "🇱🇧", "سوريا": "🇸🇾", "الأردن": "🇯🇴", "عمان": "🇴🇲", "الكويت": "🇰🇼", "البحرين": "🇧🇭", "ليبيا": "🇱🇾", "إريتريا": "🇪🇷", "جيبوتي": "🇩🇯", "فلسطين": "🇵🇸"}
_TLD = {"il": "إسرائيل", "uk": "بريطانيا", "tr": "تركيا", "ir": "إيران", "et": "إثيوبيا", "eg": "مصر", "sa": "السعودية", "ae": "الإمارات",
        "qa": "قطر", "lb": "لبنان", "fr": "فرنسا", "se": "السويد", "sd": "السودان", "za": "جنوب أفريقيا", "nl": "هولندا", "eu": "أوروبا", "cn": "الصين", "jp": "اليابان", "kr": "كوريا الجنوبية", "ru": "روسيا", "ke": "كينيا", "so": "الصومال", "ye": "اليمن", "iq": "العراق", "sy": "سوريا", "jo": "الأردن", "om": "عمان", "kw": "الكويت", "bh": "البحرين", "ly": "ليبيا", "er": "إريتريا", "dj": "جيبوتي", "ps": "فلسطين"}
_OVERRIDE = {
    "reuters.com": "بريطانيا", "france24.com": "فرنسا", "memri.org": "أمريكا", "i24news.tv": "إسرائيل",
    "middleeasteye.net": "بريطانيا", "newarab.com": "بريطانيا", "middleeastmonitor.com": "بريطانيا", "opendemocracy.net": "بريطانيا",
    "thejc.com": "بريطانيا", "alquds.co.uk": "بريطانيا", "alaraby.co.uk": "بريطانيا", "iranintl.com": "بريطانيا",
    "sudantribune.com": "فرنسا", "aljazeera.net": "قطر", "aawsat.com": "السعودية", "alarabiya.net": "السعودية", "asharq.com": "السعودية",
    "okaz.com.sa": "السعودية", "al-akhbar.com": "لبنان", "almayadeen.net": "لبنان", "independentarabia.com": "السعودية",
    "skynewsarabia.com": "الإمارات", "alittihad.ae": "الإمارات", "alkhaleej.ae": "الإمارات", "intelligence.gov": "أمريكا", "odni.gov": "أمريكا", "nsa.gov": "أمريكا", "nga.mil": "أمريكا",
    "dw.com": "ألمانيا", "spiegel.de": "ألمانيا", "lemonde.fr": "فرنسا", "politico.eu": "أوروبا",
    "sipri.org": "السويد", "iiss.org": "بريطانيا", "rusi.org": "بريطانيا", "chathamhouse.org": "بريطانيا", "crisisgroup.org": "بلجيكا",
    "ecfr.eu": "أوروبا", "issafrica.org": "جنوب أفريقيا", "bellingcat.com": "هولندا", "acleddata.com": "أمريكا", "liveuamap.com": "أوكرانيا",
    "digitallibrary.un.org": "الأمم المتحدة", "reliefweb.int": "الأمم المتحدة", "crsreports.congress.gov": "أمريكا",
    "arabcenterdc.org": "أمريكا", "mei.edu": "أمريكا", "africacenter.org": "أمريكا", "setav.org": "تركيا",
    "understandingwar.org": "أمريكا", "rand.org": "أمريكا", "warontherocks.com": "أمريكا", "stimson.org": "أمريكا",
    "israel-alma.org": "إسرائيل", "besacenter.org": "إسرائيل", "egyptindependent.com": "مصر", "dailynewsegypt.com": "مصر",
    "egypttoday.com": "مصر",
    "khamenei.ir": "إيران", "presstv.ir": "إيران", "alalam.ir": "إيران",
    "thenationalnews.com": "الإمارات", "arabnews.com": "السعودية", "aljazeera.com": "قطر",
    "thenewhumanitarian.org": "سويسرا", "tacticalreport.com": "دولي", "theafricareport.com": "فرنسا", "xinhuanet.com": "الصين", "globaltimes.cn": "الصين", "cgtn.com": "الصين", "chinadaily.com.cn": "الصين", "scmp.com": "هونغ كونغ", "asia.nikkei.com": "اليابان", "nhk.or.jp": "اليابان", "yna.co.kr": "كوريا الجنوبية", "tass.com": "روسيا", "interfax.com": "روسيا", "meduza.io": "روسيا", "rbc.ru": "روسيا", "africa-confidential.com": "بريطانيا", "africaintelligence.com": "فرنسا", "dailymaverick.co.za": "جنوب أفريقيا", "theeastafrican.co.ke": "كينيا",
    "dw.com": "ألمانيا", "france24.com": "فرنسا", "euronews.com": "فرنسا", "afp.com": "فرنسا",
    "sudantribune.com": "السودان", "dabangasudan.org": "السودان", "radiotamazuj.org": "السودان", "sudanwarmonitor.com": "السودان", "sudanpost.info": "السودان",
    "garoweonline.com": "الصومال", "hiiraan.com": "الصومال", "somaliguardian.com": "الصومال", "sonna.so": "الصومال",
    "yemenmonitor.com": "اليمن", "sanaacenter.org": "اليمن", "south24.net": "اليمن",
    "rudaw.net": "العراق", "shafaq.com": "العراق", "iraqinews.com": "العراق", "ninanews.com": "العراق", "kurdistan24.net": "العراق",
    "naharnet.com": "لبنان", "lorientlejour.com": "لبنان", "syrianobserver.com": "سوريا", "enabbaladi.net": "سوريا", "sana.sy": "سوريا",
    "jordantimes.com": "الأردن", "ammonews.net": "الأردن", "qna.org.qa": "قطر", "omannews.gov.om": "عمان", "kuna.net.kw": "الكويت",
    "spa.gov.sa": "السعودية", "wam.ae": "الإمارات", "bna.bh": "البحرين", "thepeninsulaqatar.com": "قطر", "gulf-times.com": "قطر",
    "amwaj.media": "بريطانيا", "shabait.com": "إريتريا", "asmarino.com": "إريتريا", "thedjiboutipost.com": "جيبوتي",
    "lavoixdedjibouti.info": "جيبوتي", "libyaobserver.ly": "ليبيا",
    "defense.gov": "أمريكا", "state.gov": "أمريكا", "whitehouse.gov": "أمريكا", "dni.gov": "أمريكا", "odni.gov": "أمريكا",
    "intelligence.gov": "أمريكا", "nsa.gov": "أمريكا", "nga.mil": "أمريكا", "dia.mil": "أمريكا", "cia.gov": "أمريكا",
    "mod.gov.il": "إسرائيل", "gov.il": "إسرائيل", "idf.il": "إسرائيل", "idi.org.il": "إسرائيل", "israelpolicyforum.org": "أمريكا",
    "sis.gov.uk": "بريطانيا", "mi5.gov.uk": "بريطانيا", "gchq.gov.uk": "بريطانيا", "ncsc.gov.uk": "بريطانيا",
    "commonslibrary.parliament.uk": "بريطانيا", "janes.com": "بريطانيا", "news.usni.org": "أمريكا", "jamestown.org": "أمريكا",
    "hudson.org": "أمريكا", "carnegieendowment.org": "أمريكا", "newlinesinstitute.org": "أمريكا", "defensescoop.com": "أمريكا",
    "c4isrnet.com": "أمريكا", "airandspaceforces.com": "أمريكا", "armytimes.com": "أمريكا", "stripes.com": "أمريكا",
    "intelligence.gov": "أمريكا", "news.un.org": "الأمم المتحدة", "iaea.org": "الأمم المتحدة", "imo.org": "الأمم المتحدة",
    "opcw.org": "الأمم المتحدة", "ohchr.org": "الأمم المتحدة", "ukdefencejournal.org.uk": "بريطانيا", "forcesnews.com": "بريطانيا",
}
FLAGS.update({"ألمانيا": "🇩🇪", "أوكرانيا": "🇺🇦"})
_DOM_COUNTRY = dict(_OVERRIDE)
for _g, _c in ((ISRAEL, "إسرائيل"), (USA, "أمريكا"), (UK, "بريطانيا")):
    for _ents in _g.values():
        for _n, _d, _l in _ents:
            for _x in _d.split("|"):
                _DOM_COUNTRY.setdefault(_x, _c)
for _title, _ents in REGION.items():
    _c = "إثيوبيا" if "إثيوبيا" in _title else "تركيا" if "تركيا" in _title else "إيران"
    for _n, _d, _l in _ents:
        _DOM_COUNTRY.setdefault(_d, _c)
for _ents in ARABIC.values():
    for _n, _d, _l in _ents:
        _DOM_COUNTRY.setdefault(_d, "مصر" if _d in EGYPT_ARABIC else "")
for _k, _ents in EGYPT.items():
    if _k == ARAB_EG_GROUP:
        continue
    for _n, _d, _l in _ents:
        _DOM_COUNTRY[_d] = "مصر"
_DOM_COUNTRY.setdefault("alhadath.net", "السعودية")


def source_country(domain):
    """اسم دولة المصدر بالعربية (أو '' إن لم تُعرف)"""
    d = (domain or "").lower().replace("www.", "").strip()
    parts = d.split(".")
    for i in range(len(parts) - 1):
        c = _DOM_COUNTRY.get(".".join(parts[i:]))
        if c:
            return c
    if parts[-1] in _TLD:
        return _TLD[parts[-1]]
    return ""

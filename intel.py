# -*- coding: utf-8 -*-
"""مكتب الاستخبارات المفتوحة: سجل المصادر، الملفات المترابطة، التصنيف، وبناء التقرير"""
import re
from datetime import datetime

SIDES = {
    "us": "🇺🇸 منظور أمريكي",
    "il": "🇮🇱 منظور إسرائيلي",
    "eu": "🇪🇺 منظور أوروبي/دولي",
    "reg": "🌍 منظور إقليمي وأفريقي",
    "eg": "🇪🇬 منظور مصري",
    "ar": "🌐 صحافة عربية",
    "osint": "📡 بيانات ومصادر مفتوحة",
    "uk": "🇬🇧 منظور بريطاني",
}
EGYPT_RE = re.compile(r"egypt|egyptian|cairo|sisi|sissi|suez|\bnile\b|gerd|rafah|sinai|مصر|القاهر", re.I)

# (الاسم، الدومين، المنظور، النوع: think/official/data، التخصص)
SOURCES = [
    ("ISW", "understandingwar.org", "us", "think", "تحركات الجيوش والميليشيات والخرائط العسكرية"),
    ("CSIS", "csis.org", "us", "think", "التسليح الأمريكي وإيران وإسرائيل والخليج"),
    ("RAND", "rand.org", "us", "think", "الدراسات الاستراتيجية والعسكرية العميقة"),
    ("CFR", "cfr.org", "us", "think", "السياسة الخارجية الأمريكية ومصالح واشنطن"),
    ("War on the Rocks", "warontherocks.com", "us", "think", "تحليلات عسكرية واستراتيجية"),
    ("Stimson Center", "stimson.org", "us", "think", "الأمن الإقليمي والانتشار العسكري"),
    ("Congressional Research Service", "crsreports.congress.gov", "us", "official", "تقارير رسمية للكونجرس: مساعدات مصر، السعودية، عقوبات إيران"),
    ("INSS", "inss.org.il", "il", "think", "الأمن القومي الإسرائيلي وإيران ومصر"),
    ("Alma Center", "israel-alma.org", "il", "think", "حزب الله وسوريا والحدود الشمالية"),
    ("JISS", "jiss.org.il", "il", "think", "الاستراتيجية العسكرية والسياسة الأمنية الإسرائيلية"),
    ("Begin-Sadat Center (BESA)", "besacenter.org", "il", "think", "الدراسات الأمنية والعسكرية"),
    ("IISS", "iiss.org", "eu", "think", "التوازن العسكري والقوات المسلحة"),
    ("SIPRI", "sipri.org", "eu", "data", "صفقات السلاح والإنفاق العسكري"),
    ("ECFR", "ecfr.eu", "eu", "think", "العلاقات الأوروبية والشرق الأوسط"),
    ("RUSI", "rusi.org", "eu", "think", "الدراسات الدفاعية والاستخباراتية"),
    ("Chatham House", "chathamhouse.org", "eu", "think", "السياسة الدولية والأمن الإقليمي"),
    ("International Crisis Group", "crisisgroup.org", "eu", "think", "النزاعات والتحركات السياسية"),
    ("Middle East Institute", "mei.edu", "reg", "think", "مصر والخليج وإيران وتركيا والقرن الأفريقي"),
    ("Arab Center Washington DC", "arabcenterdc.org", "reg", "think", "السياسات العربية والأمن الإقليمي"),
    ("Washington Institute", "washingtoninstitute.org", "us", "think", "إسرائيل وإيران والخليج"),
    ("Atlantic Council", "atlanticcouncil.org", "us", "think", "السياسة الأمريكية والتحالفات"),
    ("Foundation for Defense of Democracies", "fdd.org", "us", "think", "العقوبات وإيران والأمن الإقليمي"),
    ("The Soufan Center", "thesoufancenter.org", "us", "think", "مكافحة الإرهاب والشبكات المسلحة والأمن"),
    ("Center for a New American Security", "cnas.org", "us", "think", "الدفاع والسياسة الخارجية الأمريكية"),
    ("Africa Center for Strategic Studies", "africacenter.org", "reg", "think", "أفريقيا والقرن الأفريقي والأمن"),
    ("ISS Africa", "issafrica.org", "reg", "think", "السودان وإثيوبيا والصومال والبحر الأحمر"),
    ("Ahram Online / الأهرام", "ahram.org.eg", "eg", "media", "الموقف الرسمي والإعلام المصري"),
    ("Al-Ahram Center (ACPSS)", "acpss.ahram.org.eg", "eg", "think", "مركز الأهرام للدراسات السياسية والاستراتيجية"),
    ("Egypt Independent", "egyptindependent.com", "eg", "media", "أخبار مصر بالإنجليزية"),
    ("Mada Masr", "madamasr.com", "eg", "media", "صحافة مصرية مستقلة"),
    ("Daily News Egypt", "dailynewsegypt.com", "eg", "media", "أخبار مصر والاقتصاد"),
    ("Egypt Today", "egypttoday.com", "eg", "media", "أخبار مصر بالإنجليزية"),
    ("State Information Service (SIS)", "sis.gov.eg", "eg", "official", "بيانات رسمية مصرية"),
    ("Egyptian MFA", "mfa.gov.eg", "eg", "official", "الخارجية المصرية"),
    ("ECSS", "ecss.com.eg", "eg", "think", "المركز المصري للدراسات الاستراتيجية"),
    ("Bellingcat", "bellingcat.com", "osint", "think", "تحقيقات مفتوحة وتحليل الصور"),
    ("ACLED", "acleddata.com", "osint", "data", "بيانات الاشتباكات والصراعات"),
    ("Liveuamap", "liveuamap.com", "osint", "data", "الأحداث الميدانية على الخرائط"),
    ("UN Digital Library", "digitallibrary.un.org", "osint", "official", "تقارير ووثائق الأمم المتحدة"),
    ("ReliefWeb", "reliefweb.int", "osint", "official", "تقارير الأزمات والنزاعات الإنسانية"),
    ("UN OCHA", "unocha.org", "osint", "official", "بيانات الاحتياجات الإنسانية والاستجابة للأزمات"),
    ("UNHCR", "unhcr.org", "osint", "official", "بيانات اللاجئين والنزوح"),
    ("International Organization for Migration", "iom.int", "osint", "official", "الهجرة والنزوح وحركة السكان"),
    ("World Bank", "worldbank.org", "osint", "data", "مؤشرات الاقتصاد والتنمية والديون"),
    ("International Monetary Fund", "imf.org", "osint", "data", "تقارير الاقتصاد الكلي وبرامج التمويل"),
    ("US Energy Information Administration", "eia.gov", "us", "official", "بيانات الطاقة والإنتاج والتجارة"),

    ("Tactical Report", "tacticalreport.com", "reg", "think", "تقارير استخباراتية مدفوعة عن السياسة والدفاع والطاقة في الخليج والشرق الأوسط"),
    ("Sudan Tribune", "sudantribune.com", "reg", "media", "الحرب والسياسة والاقتصاد في السودان"),
    ("Radio Dabanga", "dabangasudan.org", "reg", "media", "دارفور والسودان والملف الإنساني"),
    ("Radio Tamazuj", "radiotamazuj.org", "reg", "media", "السودان وجنوب السودان"),
    ("Sudan War Monitor", "sudanwarmonitor.com", "reg", "think", "متابعة ميدانية وتحليل الحرب في السودان"),
    ("Garowe Online", "garoweonline.com", "reg", "media", "الصومال وبونتلاند والقرن الأفريقي"),
    ("Hiiraan Online", "hiiraan.com", "reg", "media", "السياسة والأمن في الصومال"),
    ("Yemen Monitor", "yemenmonitor.com", "reg", "media", "اليمن والحوثيون والبحر الأحمر"),
    ("Sana'a Center", "sanaacenter.org", "reg", "think", "تحليل سياسي واقتصادي وأمني مستقل عن اليمن"),
    ("South24 Center", "south24.net", "reg", "think", "جنوب اليمن والبحر الأحمر والسياسة الإقليمية"),
    ("Rudaw", "rudaw.net", "reg", "media", "العراق وكردستان وسوريا وتركيا"),
    ("Shafaq News", "shafaq.com", "reg", "media", "العراق وكردستان والشرق الأوسط"),
    ("L'Orient Today", "lorientlejour.com", "reg", "media", "لبنان والسياسة والاقتصاد والأمن"),
    ("The Syrian Observer", "syrianobserver.com", "reg", "media", "المشهد السياسي السوري ومصادر المعارضة"),
    ("Qatar News Agency", "qna.org.qa", "reg", "official", "البيانات الرسمية القطرية؛ تُعامل كرواية حكومية"),
    ("Oman News Agency", "omannews.gov.om", "reg", "official", "البيانات الرسمية العمانية؛ تُعامل كرواية حكومية"),
    ("Kuwait News Agency", "kuna.net.kw", "reg", "official", "البيانات الرسمية الكويتية؛ تُعامل كرواية حكومية"),
    ("Saudi Press Agency", "spa.gov.sa", "reg", "official", "البيانات الرسمية السعودية؛ تُعامل كرواية حكومية"),
    ("Emirates News Agency", "wam.ae", "reg", "official", "البيانات الرسمية الإماراتية؛ تُعامل كرواية حكومية"),
    ("Bahrain News Agency", "bna.bh", "reg", "official", "البيانات الرسمية البحرينية؛ تُعامل كرواية حكومية"),
    ("Pentagon / US Department of Defense", "defense.gov", "us", "official", "بيانات وزارة الدفاع الأمريكية والانتشار العسكري"),
    ("US Department of State", "state.gov", "us", "official", "البيانات الدبلوماسية والعقوبات والسياسة الخارجية"),
    ("White House", "whitehouse.gov", "us", "official", "القرارات والبيانات الرئاسية الأمريكية"),
    ("ODNI", "odni.gov", "us", "official", "تقييمات مجتمع الاستخبارات الأمريكي وتقارير التهديدات"),
    ("US Intelligence Community", "intelligence.gov", "us", "official", "الوثائق المفرج عنها والتقارير العامة لمجتمع الاستخبارات"),
    ("National Security Agency", "nsa.gov", "us", "official", "منشورات الأمن السيبراني والتشفير والاستخبارات الإشارية العلنية"),
    ("National Geospatial-Intelligence Agency", "nga.mil", "us", "official", "المعلومات الجغرافية المكانية والخرائط والتحذيرات العلنية"),
    ("CIA", "cia.gov", "us", "official", "منشورات علنية لوكالة الاستخبارات المركزية"),
    ("DIA", "dia.mil", "us", "official", "منشورات استخبارات الدفاع الأمريكية"),
    ("USNI News", "news.usni.org", "us", "media", "البحرية الأمريكية والأساطيل والانتشار البحري"),
    ("Jamestown Foundation", "jamestown.org", "us", "think", "روسيا وأوراسيا والجماعات المسلحة والشرق الأوسط"),
    ("Hudson Institute", "hudson.org", "us", "think", "الدفاع والاستراتيجية والسياسة الأمريكية"),
    ("Carnegie Endowment", "carnegieendowment.org", "us", "think", "السياسة الدولية والشرق الأوسط"),
    ("New Lines Institute", "newlinesinstitute.org", "us", "think", "الشرق الأوسط والأمن الإقليمي"),
    ("DefenseScoop", "defensescoop.com", "us", "media", "التكنولوجيا الدفاعية والإنفاق العسكري"),
    ("C4ISRNET", "c4isrnet.com", "us", "media", "الاستخبارات والمراقبة والاتصالات العسكرية"),
    ("Air & Space Forces Magazine", "airandspaceforces.com", "us", "media", "القوات الجوية والفضائية والتسليح"),
    ("Army Times", "armytimes.com", "us", "media", "الجيش الأمريكي والتجهيزات"),
    ("IDF Spokesperson", "idf.il", "il", "official", "البيانات الرسمية للجيش الإسرائيلي، تُعامل كرواية طرف"),
    ("Israel Ministry of Defense", "mod.gov.il", "il", "official", "التعاون الدفاعي والمشتريات والصناعة العسكرية الإسرائيلية"),
    ("Israel Government Portal", "gov.il", "il", "official", "بوابة رسمية تضم بيانات مجلس الأمن القومي والخارجية وجهات حكومية إسرائيلية؛ تُعامل كرواية رسمية"),
    ("Israel Democracy Institute", "idi.org.il", "il", "think", "السياسة والمجتمع والمؤسسات الإسرائيلية"),
    ("Israel Policy Forum", "israelpolicyforum.org", "il", "think", "السياسة الإسرائيلية والعلاقات الأمريكية الإسرائيلية"),
    ("UK Government (MOD / FCDO)", "gov.uk", "uk", "official", "بوابة الحكومة البريطانية وبيانات الدفاع والخارجية"),
    ("UK National Cyber Security Centre", "ncsc.gov.uk", "uk", "official", "الأمن السيبراني والتحذيرات التقنية"),
    ("UK SIS / MI6", "sis.gov.uk", "uk", "official", "المعلومات العامة والبيانات العلنية لجهاز الاستخبارات الخارجية"),
    ("UK MI5", "mi5.gov.uk", "uk", "official", "الأمن الداخلي ومكافحة التجسس والتهديدات"),
    ("UK GCHQ", "gchq.gov.uk", "uk", "official", "الأمن السيبراني والاستخبارات الإشارية والبيانات العامة"),
    ("UK Parliament Commons Library", "commonslibrary.parliament.uk", "uk", "official", "أبحاث البرلمان البريطاني والملفات القطرية"),
    ("UK Defence Journal", "ukdefencejournal.org.uk", "uk", "media", "الدفاع البريطاني والمشتريات والانتشار"),
    ("Jane's", "janes.com", "uk", "think", "استخبارات دفاعية وتسليح؛ محتوى اشتراكي"),
    ("Africa Confidential", "africa-confidential.com", "uk", "media", "سياسة وأمن أفريقيا؛ محتوى اشتراكي"),
    ("Africa Intelligence", "africaintelligence.com", "eu", "media", "شبكات النفوذ والسياسة والأعمال في أفريقيا؛ محتوى اشتراكي"),
    ("Der Spiegel", "spiegel.de", "eu", "media", "تحقيقات وسياسة ألمانية ودولية"),
    ("Le Monde", "lemonde.fr", "eu", "media", "سياسة وتحقيقات فرنسية"),
    ("Politico Europe", "politico.eu", "eu", "media", "سياسات الاتحاد الأوروبي والأمن"),
    ("Xinhua", "xinhuanet.com", "reg", "media", "الرواية الرسمية الصينية والتغطية الدولية"),
    ("Global Times", "globaltimes.cn", "reg", "media", "الإعلام الصيني القومي والسياسة الخارجية"),
    ("CGTN", "cgtn.com", "reg", "media", "الإعلام الدولي الصيني"),
    ("South China Morning Post", "scmp.com", "reg", "media", "الصين وهونغ كونغ وآسيا"),
    ("Nikkei Asia", "asia.nikkei.com", "reg", "media", "اقتصاد وأمن شرق آسيا"),
    ("NHK World", "nhk.or.jp", "reg", "media", "اليابان وشرق آسيا"),
    ("Yonhap", "yna.co.kr", "reg", "media", "كوريا وشبه الجزيرة الكورية"),
    ("TASS", "tass.com", "reg", "media", "الرواية الرسمية الروسية والتطورات الدولية"),
    ("Interfax", "interfax.com", "reg", "media", "الأخبار الروسية والأوراسية"),
    ("Meduza", "meduza.io", "reg", "media", "صحافة روسية مستقلة من خارج روسيا"),
    ("Daily Maverick", "dailymaverick.co.za", "reg", "media", "جنوب أفريقيا والسياسة والأمن الأفريقي"),
    ("The EastAfrican", "theeastafrican.co.ke", "reg", "media", "شرق أفريقيا والقرن الأفريقي"),
    ("UN News", "news.un.org", "osint", "official", "بيانات وتقارير الأمم المتحدة متعددة اللغات"),
    ("IAEA", "iaea.org", "osint", "official", "الملف النووي والتفتيش والضمانات"),
    ("International Maritime Organization", "imo.org", "osint", "official", "الملاحة البحرية وأمن الممرات"),
    ("OPCW", "opcw.org", "osint", "official", "الأسلحة الكيميائية والتحقيقات الفنية"),
    ("OHCHR", "ohchr.org", "osint", "official", "تقارير حقوق الإنسان والتحقيقات الأممية"),

]

# الملفات المترابطة الستة: (كلمات بحث افتراضية بالإنجليزية، الأطراف، أسئلة الربط)
FILES = {
    "شرق المتوسط": {
        "egypt": ['Egypt Eastern Mediterranean gas', 'Egypt Greece Cyprus maritime', 'Egypt Turkey relations', 'Egypt Israel gas deal'],
        "terms": ["Eastern Mediterranean", "Egypt Turkey Israel gas", "Cyprus Greece Turkey naval"],
        "axes": "مصر، إسرائيل، تركيا، قبرص، اليونان",
    },
    "البحر الأحمر": {
        "egypt": ['Egypt Suez Canal Red Sea', 'Egypt Eritrea', 'Egypt Saudi Red Sea security', 'Egyptian navy Red Sea'],
        "terms": ["Red Sea shipping", "Houthi Red Sea attacks", "Eritrea Djibouti Red Sea base"],
        "axes": "مصر، السعودية، اليمن، إسرائيل، إريتريا، جيبوتي",
    },
    "الخليج وإيران": {
        "egypt": ['Egypt Gulf Iran', 'Egypt Saudi Arabia', 'Egypt UAE investment'],
        "terms": ["Iran Gulf security", "Saudi Arabia UAE Iran", "Iran nuclear military assessment"],
        "axes": "السعودية، الإمارات، إيران، قطر، أمريكا",
    },
    "المشرق العربي": {
        "egypt": ['Egypt Gaza Rafah mediation', 'Egypt Lebanon', 'Egypt Syria'],
        "terms": ["Hezbollah Lebanon Israel", "Syria Turkey Israel", "Syria military"],
        "axes": "سوريا، لبنان، حزب الله، إسرائيل، تركيا",
    },
    "القرن الأفريقي": {
        "egypt": ['Egypt Ethiopia GERD Nile', 'Egypt Somalia troops', 'Egypt Sudan', 'Egypt Eritrea Djibouti'],
        "terms": ["Horn of Africa", "Ethiopia Sea access Red Sea", "Somalia Egypt Turkey UAE", "Sudan war"],
        "axes": "إثيوبيا، الصومال، إريتريا، السودان، جيبوتي",
    },
    "القوى الكبرى": {
        "egypt": ['Egypt Russia China military', 'Egypt US military aid', 'Egypt France Rafale'],
        "terms": ["Russia China Middle East", "US military posture Middle East"],
        "axes": "أمريكا، روسيا، الصين، أوروبا",
    },
}

LINK_QUESTIONS = [
    "علاقته بالتنافس التركي الإماراتي",
    "موقف إثيوبيا من الوصول إلى البحر",
    "تأثيره على المصالح المصرية",
    "موقف السعودية من أمن البحر الأحمر",
    "انعكاساته على المصالح الإسرائيلية",
    "الموقف الأمريكي والصيني والروسي",
]

INTEL_TYPES = ["معلومة مؤكدة", "تقرير من مصدر متخصص", "تسريب غير مؤكد", "تقدير استراتيجي", "خبر إعلامي"]

_LEAK = re.compile(r"تسريب|وفق مصادر|مصادر:|يُزعم|مزاعم|غير مؤكد|reportedly|unconfirmed|leak|sources? (say|said|claim)|alleged|rumou?r|claims?\b|purported|unverified|according to (an )?unnamed", re.I)
_ASSESS = re.compile(r"تقدير|سيناريو|سيناريوهات|قراءة في|رؤية|assessment|outlook|forecast|scenario|implications|what to expect|estimate|prospects|strategy|strategic|balance|trajector|options for", re.I)


def classify_intel(title, url, kind):
    """تصنيف تقديري من العنوان/الرابط/نوع الجهة — ليس حكماً على صحة المعلومة"""
    t = f"{title} {url}"
    if _LEAK.search(title):
        return "تسريب غير مؤكد"
    if _ASSESS.search(t):
        return "تقدير استراتيجي"
    if kind == "media":
        return "خبر إعلامي"
    if kind in ("official", "data"):
        return "معلومة مؤكدة"
    return "تقرير من مصدر متخصص"


def search_links(term):
    """روابط بحث مجانية عن التقارير (تُفتح في تبويب جديد)"""
    from urllib.parse import quote_plus as q
    t = term.strip()
    return [
        ("Google — ملفات PDF", f"https://www.google.com/search?q={q(chr(34) + t + chr(34) + ' filetype:pdf')}"),
        ("Google — تقارير مراكز الأبحاث", f"https://www.google.com/search?q={q(t + ' (site:csis.org OR site:rand.org OR site:inss.org.il OR site:rusi.org OR site:mei.edu OR site:crisisgroup.org) filetype:pdf')}"),
        ("Google Scholar", f"https://scholar.google.com/scholar?q={q(t)}"),
        ("SSRN", f"https://papers.ssrn.com/sol3/results.cfm?txtKey_Words={q(t)}"),
        ("CORE", f"https://core.ac.uk/search?q={q(t)}"),
        ("OpenAlex", f"https://openalex.org/works?search={q(t)}"),
        ("Internet Archive", f"https://archive.org/search?query={q(t)}"),
        ("ReliefWeb", f"https://reliefweb.int/updates?search={q(t)}"),
        ("UN Digital Library", f"https://digitallibrary.un.org/search?ln=en&p={q(t)}"),
        ("SIPRI — قاعدة صفقات السلاح (CSV)", "https://armstransfers.sipri.org/ArmsTransfer/TransferRegister"),
    ]


def build_report(title, file_name, terms, days, items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    out = [f"# {title}", f"*الملف: {file_name} — كلمات البحث: {', '.join(terms)} — آخر {days} يوماً — أُنشئ {now}*", "",
           "> التصنيف تقديري يعتمد على العنوان والرابط ونوع الجهة، وليس حكماً على صحة المعلومة؛ راجع المصدر الأصلي دائماً.", ""]
    for typ in INTEL_TYPES:
        sub = [a for a in items if a.get("ctype") == typ]
        if not sub:
            continue
        out += [f"## {typ} ({len(sub)})", ""]
        for a in sub:
            d = a.get("seendate", "")
            d = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) >= 8 else "-"
            out += [f"- **{a.get('title_ar', '')}**  ",
                    f"  {a.get('title', '')}  ",
                    f"  {a.get('country_ar', '')} · {a.get('domain', '')} · {d} · [الرابط الأصلي]({a.get('url', '')})"]
        out.append("")
    return "\n".join(out)

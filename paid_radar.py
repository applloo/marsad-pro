# -*- coding: utf-8 -*-
"""رادار التقارير المدفوعة: اكتشاف العناوين والبحث عن تغطيات مفتوحة قانونية."""
from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse, urljoin

import requests

import core

# (الاسم، الدومين، الدولة، اللغة، نوع المحتوى). هذه قائمة مراقبة وليست حكماً بأن كل مادة مدفوعة.
PAID_SOURCES = [
    ("Tactical Report", "tacticalreport.com", "دولي/الشرق الأوسط", "en", "استخبارات سياسية ودفاع وطاقة"),
    ("The New York Times", "nytimes.com", "أمريكا", "en", "صحافة وتحقيقات"),
    ("The Washington Post", "washingtonpost.com", "أمريكا", "en", "صحافة وتحقيقات"),
    ("The Wall Street Journal", "wsj.com", "أمريكا", "en", "سياسة واقتصاد وأمن"),
    ("Bloomberg", "bloomberg.com", "أمريكا", "en", "اقتصاد وطاقة وسياسة"),
    ("Foreign Affairs", "foreignaffairs.com", "أمريكا", "en", "تحليل استراتيجي"),
    ("Foreign Policy", "foreignpolicy.com", "أمريكا", "en", "سياسة دولية"),
    ("The Atlantic", "theatlantic.com", "أمريكا", "en", "تحليل وسياسة"),
    ("Politico", "politico.com", "أمريكا", "en", "سياسة وواشنطن"),
    ("The New Yorker", "newyorker.com", "أمريكا", "en", "تحقيقات وتحليل"),
    ("Wired", "wired.com", "أمريكا", "en", "تقنية وأمن سيبراني"),
    ("Haaretz", "haaretz.com|haaretz.co.il", "إسرائيل", "both", "سياسة وأمن وتحقيقات"),
    ("Yedioth Ahronoth / Ynet", "ynet.co.il|ynetnews.com", "إسرائيل", "both", "صحافة إسرائيلية"),
    ("Maariv", "maariv.co.il", "إسرائيل", "he", "سياسة وأمن"),
    ("Israel Hayom", "israelhayom.com|israelhayom.co.il", "إسرائيل", "both", "سياسة وأمن"),
    ("Globes", "globes.co.il", "إسرائيل", "he", "اقتصاد وأعمال"),
    ("Calcalist", "calcalist.co.il", "إسرائيل", "he", "اقتصاد وتقنية"),
    ("The Jerusalem Post", "jpost.com", "إسرائيل", "en", "سياسة وأمن"),
    ("The Times of Israel", "timesofisrael.com", "إسرائيل", "en", "سياسة وأمن"),
    ("The Times", "thetimes.com|thetimes.co.uk", "بريطانيا", "en", "صحافة وتحليل"),
    ("The Telegraph", "telegraph.co.uk", "بريطانيا", "en", "صحافة وتحليل"),
    ("Financial Times", "ft.com", "بريطانيا", "en", "اقتصاد وسياسة دولية"),
    ("The Economist", "economist.com", "بريطانيا", "en", "تحليل دولي"),
    ("Jane's", "janes.com", "بريطانيا", "en", "استخبارات دفاعية وتسليح"),
    ("IISS", "iiss.org", "بريطانيا", "en", "توازنات عسكرية ودفاع"),
    ("Africa Confidential", "africa-confidential.com", "بريطانيا", "en", "سياسة وأمن أفريقي"),
    ("Africa Intelligence", "africaintelligence.com", "فرنسا", "en", "شبكات النفوذ والسياسة والأعمال في أفريقيا"),
    ("Reuters", "reuters.com", "بريطانيا", "en", "وكالة أنباء دولية، قد تتطلب بعض المواد اشتراكاً أو تسجيلاً"),
    ("Der Spiegel", "spiegel.de", "ألمانيا", "both", "تحقيقات وسياسة"),
    ("Le Monde", "lemonde.fr", "فرنسا", "en", "سياسة وتحقيقات"),
    ("Politico Europe", "politico.eu", "أوروبا", "en", "سياسة الاتحاد الأوروبي والأمن"),
    ("Nikkei Asia", "asia.nikkei.com", "اليابان", "en", "اقتصاد وأمن آسيوي"),
    ("South China Morning Post", "scmp.com", "هونغ كونغ", "en", "الصين وآسيا"),
]

# نطاقات يُبحث فيها عن تغطيات مفتوحة. لا نعتبرها كلها مجانية دائماً؛ نتحقق من فتح النص مباشرة.
OPEN_ALTERNATIVE_DOMAINS = [
    "apnews.com", "bbc.com", "bbc.co.uk", "theguardian.com", "npr.org", "pbs.org",
    "france24.com", "dw.com", "euronews.com", "aljazeera.com", "al-monitor.com",
    "middleeasteye.net", "newarab.com", "thenationalnews.com", "arabnews.com",
    "defensenews.com", "breakingdefense.com", "twz.com", "defenseone.com", "news.usni.org",
    "navalnews.com", "armytimes.com", "airandspaceforces.com", "stripes.com", "ukdefencejournal.org.uk",
    "forcesnews.com", "understandingwar.org", "csis.org", "rand.org", "cfr.org", "mei.edu",
    "atlanticcouncil.org", "rusi.org", "chathamhouse.org", "crisisgroup.org", "inss.org.il",
    "israel-alma.org", "jiss.org.il", "besacenter.org", "acleddata.com", "bellingcat.com",
    "reliefweb.int", "un.org", "iaea.org", "eia.gov", "sipri.org", "issafrica.org",
    "sudantribune.com", "dabangasudan.org", "radiotamazuj.org", "garoweonline.com", "hiiraan.com",
    "yemenmonitor.com", "sanaacenter.org", "south24.net", "rudaw.net", "shafaq.com", "naharnet.com",
    "syrianobserver.com", "qna.org.qa", "omannews.gov.om", "spa.gov.sa", "wam.ae", "amwaj.media",
]

PAYWALL_DOMAINS = {d for row in PAID_SOURCES for d in row[1].split("|")}


def _host(url: str) -> str:
    raw = (url or "").strip()
    parsed = urlparse(raw if "://" in raw else "//" + raw)
    return (parsed.hostname or "").lower().removeprefix("www.")


def _matches(host: str, domains) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def _source_for_domain(domain: str):
    for name, domains, country, lang, topic in PAID_SOURCES:
        if _matches(domain, domains.split("|")):
            return {"name": name, "country": country, "language": lang, "topic": topic}
    return {"name": domain, "country": "غير محدد", "language": "en", "topic": ""}


class _ReportLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.href, self.text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href, self.text = dict(attrs).get("href", ""), []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join("".join(self.text).split())))
            self.href, self.text = None, []


def tactical_public_headlines(days=30, limit=60):
    """يقرأ فهرس التقارير العام والنشرات العامة فقط، ولا يفتح نصوص التقارير المقفولة."""
    out, notes, seen = [], [], set()
    for page in ("https://www.tacticalreport.com/reports", "https://www.tacticalreport.com/newsletters"):
        try:
            if not core.is_safe_url(page):
                continue
            response = requests.get(page, headers=core.BROWSER_HEADERS, timeout=18)
            response.raise_for_status()
            parser = _ReportLinks()
            parser.feed(response.text[:1_500_000])
            for href, title in parser.links:
                full = urljoin(response.url, unescape(href)).split("#")[0]
                host = _host(full)
                path = urlparse(full).path.lower()
                if host != "www.tacticalreport.com" and host != "tacticalreport.com":
                    continue
                if not title or len(title) < 18 or not any(x in path for x in ("report", "newsletter", "weekly")):
                    continue
                if path.rstrip("/") in ("/reports", "/newsletters"):
                    continue
                key = re.sub(r"\W+", "", title.lower())
                if key in seen:
                    continue
                seen.add(key)
                out.append({"url": full, "original_paid_url": full, "title": title,
                            "title_ar": core.tr(title, "auto", "ar"), "domain": "tacticalreport.com",
                            "paid_source": "Tactical Report", "paid_country": "دولي/الشرق الأوسط",
                            "paid_topic": "استخبارات سياسية ودفاع وطاقة", "seendate": "",
                            "access_note": "عنوان ظاهر في الفهرس العام؛ التقرير الكامل قد يتطلب اشتراكاً.",
                            "public_index": page})
        except Exception as exc:
            notes.append(f"فهرس Tactical Report تعذّر قراءته: {type(exc).__name__}")
    return out[:limit], notes


def search_paid_headlines(source_names, days=7, terms=None, max_items=120):
    """اكتشاف العناوين/البيانات الوصفية فقط من Google News RSS، لا يجلب نص المقال المدفوع."""
    selected = [(n, d, lang) for n, d, _c, lang, _t in PAID_SOURCES if n in set(source_names)]
    if not selected:
        return [], ["لم يتم اختيار مصادر مدفوعة أو اشتراكية."]
    items, notes = core.gnews_site_search(selected, int(days), terms=terms or None,
                                           joiner="OR", country="US", max_items=max_items)
    out = []
    for item in items:
        meta = _source_for_domain(item.get("domain", ""))
        item["paid_source"] = meta["name"]
        item["paid_country"] = meta["country"]
        item["paid_topic"] = meta["topic"]
        item["original_paid_url"] = item.get("url", "")
        item["access_note"] = "عنوان وبيانات علنية فقط؛ النص الكامل قد يتطلب اشتراكاً."
        out.append(item)
    if "Tactical Report" in set(source_names):
        public_items, public_notes = tactical_public_headlines(days, limit=60)
        notes.extend(public_notes)
        seen = {re.sub(r"\W+", "", x.get("title", "").lower()) for x in out}
        for item in public_items:
            key = re.sub(r"\W+", "", item.get("title", "").lower())
            if key not in seen:
                out.append(item)
                seen.add(key)
    out.sort(key=lambda x: x.get("seendate", ""), reverse=True)
    return out[:max_items], notes


def _title_terms(title: str) -> str:
    text = (title or "").strip()
    if core._HEB.search(text):
        text = core.tr(text, "iw", "en")
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", text)
    stop = {"the", "and", "for", "with", "from", "after", "over", "into", "says", "said", "what", "how", "why", "report", "analysis"}
    chosen = []
    for word in words:
        w = word.lower()
        if w not in stop and w not in chosen:
            chosen.append(w)
        if len(chosen) >= 9:
            break
    return " ".join(chosen) if chosen else text[:100]


def _similarity(a: str, b: str) -> float:
    def toks(s):
        return {x.lower() for x in re.findall(r"[\w'-]{3,}", s or "")}
    aa, bb = toks(a), toks(b)
    return len(aa & bb) / max(1, len(aa | bb))


def find_open_coverage(title, original_domain="", days=30, limit=8):
    """يعثر على تغطيات مفتوحة مرشحة عبر RSS، دون فتح أو نسخ نص المصدر المدفوع."""
    title = (title or "").strip()
    if len(title) < 8:
        return [], "العنوان قصير ولا يكفي للبحث."
    query = f'"{title[:150]}" when:{max(1, int(days))}d'
    feeds = [("en-US", "US", "US:en"), ("en-GB", "GB", "GB:en")]
    if core._HEB.search(title):
        feeds.insert(0, ("he-IL", "IL", "IL:he"))

    def load_candidates(q):
        found, failures = [], []
        for hl, gl, ceid in feeds:
            try:
                found.extend(core._get_feed(core.gnews_url(q, hl, gl, ceid)))
            except Exception as exc:
                failures.append(type(exc).__name__)
        return found, failures

    all_items, errors = load_candidates(query)
    def has_allowed_candidate(rows):
        for row in rows:
            host = _host(row.get("source_url") or row.get("link"))
            if host and _matches(host, OPEN_ALTERNATIVE_DOMAINS) and not _matches(host, PAYWALL_DOMAINS):
                return True
        return False
    if not has_allowed_candidate(all_items):
        broad = _title_terms(title)
        if broad and broad.lower() != title.lower():
            more, more_errors = load_candidates(f'{broad} when:{max(1, int(days))}d')
            all_items.extend(more)
            errors.extend(more_errors)

    # GDELT is an independent discovery path, complementary to Google News RSS.
    end_utc = datetime.now(timezone.utc)
    start_utc = end_utc - timedelta(days=max(1, int(days)))
    gdelt_query = f'"{title[:180]}"'
    try:
        gdelt_rows, gdelt_error = core.gdelt_call(gdelt_query, start_utc, end_utc, 100)
        if gdelt_error:
            errors.append(f"GDELT: {gdelt_error}")
        for row in gdelt_rows:
            host = _host(row.get("domain") or row.get("url", ""))
            if not host or not _matches(host, OPEN_ALTERNATIVE_DOMAINS) or _matches(host, PAYWALL_DOMAINS):
                continue
            date_value = row.get("seendate") or row.get("date") or ""
            try:
                date_value = datetime.strptime(date_value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            except Exception:
                date_value = None
            all_items.append({"title": row.get("title", ""), "link": row.get("url", ""),
                              "source_url": "https://" + host, "source_name": host,
                              "date": date_value, "discovery_method": "GDELT"})
    except Exception as exc:
        errors.append(f"GDELT: {type(exc).__name__}")

    seen, candidates = set(), []
    for row in all_items:
        host = _host(row.get("source_url") or row.get("link"))
        if not host or _matches(host, PAYWALL_DOMAINS) or _matches(host, [original_domain] if original_domain else []):
            continue
        if not _matches(host, OPEN_ALTERNATIVE_DOMAINS):
            continue
        url = core.decode_gnews(row.get("link", "")) if "news.google.com" in (row.get("link", "")) else row.get("link", "")
        real_host = _host(url)
        if not url.startswith("http") or not _matches(real_host, OPEN_ALTERNATIVE_DOMAINS):
            continue
        headline = row.get("title", "")
        if row.get("source_name") and headline.endswith(" - " + row["source_name"]):
            headline = headline[: -len(row["source_name"]) - 3]
        key = re.sub(r"\W+", "", headline.lower())[:90]
        if not headline or key in seen:
            continue
        seen.add(key)
        score = _similarity(title, headline)
        candidates.append({
            "title": headline, "title_ar": core.tr(headline, "auto", "ar"),
            "url": url, "domain": real_host, "date": row.get("date"),
            "match_score": round(score, 3),
            "match_label": "عنوان متقارب جداً" if score >= 0.45 else "تغطية محتملة للموضوع نفسه",
            "source_name": row.get("source_name") or real_host,
            "discovery_method": row.get("discovery_method", "Google News RSS"),
            "text_available": None,
        })
    candidates.sort(key=lambda x: (x["match_score"], x["date"] or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    return candidates[:limit], (f"تم فحص نتائج Google News RSS وGDELT؛ هذه روابط مرشحة من نطاقات بديلة." if candidates else
                                 "لم نعثر على تغطية مفتوحة مطابقة في النطاقات التي فُحصت. جرّب توسيع الفترة أو البحث بكلمات أقل.")


def read_open_article(url, max_chars=14000):
    """يقرأ نصاً متاحاً مباشرة من نطاق بديل مسموح؛ لا يستخدم بروكسي أو أرشيفاً لتجاوز اشتراك."""
    host = _host(url)
    if not url.startswith("https://") or not _matches(host, OPEN_ALTERNATIVE_DOMAINS) or _matches(host, PAYWALL_DOMAINS):
        return None, "الرابط ليس ضمن قائمة النطاقات المفتوحة المسموح بها."
    if not core.is_safe_url(url):
        return None, "الرابط غير آمن أو غير صالح."
    try:
        response = requests.get(url, headers=core.BROWSER_HEADERS, timeout=18, allow_redirects=True)
        final_host = _host(response.url)
        if not response.ok or not _matches(final_host, OPEN_ALTERNATIVE_DOMAINS) or _matches(final_host, PAYWALL_DOMAINS):
            return None, "الموقع لم يقدّم نصاً مفتوحاً مباشراً أو حوّل الرابط إلى نطاق غير مسموح."
        article = core._extract(response.content, response.encoding or response.apparent_encoding)
        text = (article.get("text") or "").strip()
        if len(text) < 500:
            return None, "المتاح من الصفحة أقل من نص مقال قابل للقراءة؛ نعرض الرابط والعنوان فقط."
        translated = core.translate_long(text[:max_chars])
        return {"title": article.get("title", ""), "text": text[:max_chars], "text_ar": translated,
                "url": response.url, "domain": final_host, "chars": len(text)}, "تم جلب النص المنشور مباشرة وترجمته."
    except Exception as exc:
        return None, f"تعذرت قراءة النص المفتوح مباشرة ({type(exc).__name__})."


def legal_search_links(title, source_url=""):
    q = quote_plus((title or "").strip())
    return [
        ("بحث العنوان كما هو في Google", f"https://www.google.com/search?q=%22{q}%22"),
        ("بحث العنوان في Google News", f"https://news.google.com/search?q=%22{q}%22"),
        ("بحث عن إعادة نشر أو اقتباس", f"https://www.google.com/search?q=%22{q}%22+republished+OR+syndicated+OR+summary"),
        ("البحث عن ملخصات ونشرات عامة", f"https://www.google.com/search?q=%22{q}%22+newsletter+OR+briefing+OR+summary"),
        ("إرشادات الاشتراك القانوني عبر Google News", "https://support.google.com/googlenews/answer/7668730"),
    ] + ([ ("المقال الأصلي", source_url) ] if source_url.startswith("https://") else [])

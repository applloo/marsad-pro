# -*- coding: utf-8 -*-
"""صحة المصادر وتجميع الأحداث ومقارنة التغطيات مع حفظ نسب المصادر."""
from __future__ import annotations

import hashlib
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

import core
import intel
import paid_radar
import sources

USER_AGENT = "Mozilla/5.0 (compatible; MarsadNews/8.19; +https://github.com/applloo/marsad-news)"
FEED_PATHS = ("/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/feeds/posts/default")
SIDE_LABELS = {
    "us": "أمريكي",
    "il": "إسرائيلي",
    "uk": "بريطاني",
    "ar": "عربي/إقليمي",
    "other": "دولي/أخرى",
}
WIRE_DOMAINS = {"reuters.com", "apnews.com", "afp.com", "tass.com", "xinhuanet.com"}
ANALYSIS_WORDS = re.compile(r"analysis|opinion|commentary|explainer|editorial|think.?tank|تحليل|رأي|وجهة نظر", re.I)


class _FeedLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "link":
            return
        a = {k.lower(): v for k, v in attrs}
        typ = (a.get("type") or "").lower()
        rel = (a.get("rel") or "").lower().split()
        href = a.get("href") or ""
        if href and "alternate" in rel and ("rss" in typ or "atom" in typ or "xml" in typ):
            self.links.append(href)


def _domain(value: str) -> str:
    raw = (value or "").strip()
    p = urlparse(raw if "://" in raw else "https://" + raw)
    return (p.hostname or "").lower().removeprefix("www.")


def _source_rows():
    rows = {}
    groups = [
        ("il", sources.ISRAEL), ("us", sources.USA), ("uk", sources.UK),
        ("ar", sources.ARABIC), ("ar", sources.REGION), ("eg", sources.EGYPT),
    ]
    for side, mapping in groups:
        for group, entries in mapping.items():
            for name, domains, lang in entries:
                for domain in str(domains).split("|"):
                    d = _domain(domain)
                    if not d:
                        continue
                    row = rows.setdefault(d, {"domain": d, "name": name, "side": side, "language": lang, "groups": []})
                    if group not in row["groups"]:
                        row["groups"].append(group)
    for name, domain, side, kind, specialty in intel.SOURCES:
        d = _domain(domain)
        if d:
            row = rows.setdefault(d, {"domain": d, "name": name, "side": side if side in SIDE_LABELS else "other", "language": "en", "groups": []})
            row["intel_type"] = kind
            row["specialty"] = specialty
    for name, domains, country, lang, topic in paid_radar.PAID_SOURCES:
        for domain in domains.split("|"):
            d = _domain(domain)
            if d:
                row = rows.setdefault(d, {"domain": d, "name": name, "side": "other", "language": lang, "groups": []})
                row["paid_watch"] = True
                row["country"] = country
                row["topic"] = topic
    # Override broad paid-source defaults with a geographic perspective when known.
    for d, side in {
        "haaretz.com": "il", "haaretz.co.il": "il", "ynet.co.il": "il", "ynetnews.com": "il",
        "maariv.co.il": "il", "israelhayom.com": "il", "globes.co.il": "il", "calcalist.co.il": "il",
        "jpost.com": "il", "timesofisrael.com": "il", "nytimes.com": "us", "washingtonpost.com": "us",
        "wsj.com": "us", "bloomberg.com": "us", "foreignaffairs.com": "us", "foreignpolicy.com": "us",
        "ft.com": "uk", "thetimes.com": "uk", "telegraph.co.uk": "uk", "economist.com": "uk",
        "janes.com": "uk", "iiss.org": "uk", "africaintelligence.com": "other",
        "africa-confidential.com": "uk", "tacticalreport.com": "ar",
        "afp.com": "other", "france24.com": "other", "dw.com": "other", "euronews.com": "other",
        "al-monitor.com": "ar", "middleeasteye.net": "ar", "newarab.com": "ar", "thenationalnews.com": "ar",
        "arabnews.com": "ar", "aljazeera.com": "ar", "aljazeera.net": "ar", "amwaj.media": "ar",
        "theafricareport.com": "other", "dailymaverick.co.za": "other", "theeastafrican.co.ke": "ar",
    }.items():
        if d in rows:
            rows[d]["side"] = side
    return [rows[k] for k in sorted(rows)]


SOURCE_CATALOG = _source_rows()
SOURCE_BY_DOMAIN = {x["domain"]: x for x in SOURCE_CATALOG}


def _safe_https(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme == "https" and bool(p.hostname) and core.is_safe_url(url)
    except Exception:
        return False



def _safe_get(url, headers=None, timeout=8, stream=False, max_redirects=3):
    """Follow only HTTPS redirects whose destination passes the public-host safety check."""
    from urllib.parse import urljoin
    current = url
    for _ in range(max_redirects + 1):
        if not _safe_https(current):
            raise ValueError("unsafe URL or redirect")
        response = requests.get(current, headers=headers or {"User-Agent": USER_AGENT}, timeout=timeout,
                                allow_redirects=False, stream=stream)
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise requests.RequestException("redirect without Location")
            current = urljoin(current, location)
            continue
        return response
    raise requests.TooManyRedirects("too many safe redirects")


def _feed_latest(content: bytes):
    try:
        root = ET.fromstring(content)
    except Exception:
        return "", ""
    latest, title = "", ""
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1].lower()
        if tag in ("item", "entry") and not title:
            t = next((x.text for x in el if x.tag.rsplit("}", 1)[-1].lower() == "title" and x.text), "")
            title = t.strip()
        if tag in ("pubdate", "published", "updated", "date") and el.text:
            raw = el.text.strip()
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                latest = dt.astimezone(timezone.utc).isoformat()
            except Exception:
                try:
                    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    latest = dt.astimezone(timezone.utc).isoformat()
                except Exception:
                    pass
            if latest:
                break
    return latest, title


def check_source_health(source: dict, timeout=8):
    """Probe homepage and discover a public RSS/Atom feed; failure is not treated as proof a source is dead."""
    domain = source["domain"]
    homepage = f"https://{domain}/"
    result = {**source, "checked_at": datetime.now(timezone.utc).isoformat(), "status": "unknown",
              "http_status": None, "homepage_url": homepage, "feed_url": "", "latest_item": "",
              "latest_item_date": "", "latency_ms": None, "error": ""}
    if not _safe_https(homepage):
        result.update(status="unsafe_or_unresolvable", error="تعذر التحقق من أمان النطاق أو DNS")
        return result
    started = time.monotonic()
    try:
        response = _safe_get(homepage, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True)
        result["http_status"] = response.status_code
        result["latency_ms"] = round((time.monotonic() - started) * 1000)
        final_url = response.url
        if not _safe_https(final_url):
            response.close()
            result.update(status="redirect_rejected", error="تحويل إلى نطاق غير مسموح")
            return result
        content_type = (response.headers.get("content-type") or "").lower()
        body = response.raw.read(1_000_000, decode_content=True)
        response.close()
        if response.status_code >= 400:
            result.update(status="http_error", error=f"HTTP {response.status_code}")
            return result
        links = []
        if "rss" in content_type or "atom" in content_type or b"<rss" in body[:1000].lower() or b"<feed" in body[:1000].lower():
            latest, title = _feed_latest(body)
            if title:
                result.update(status="healthy_feed", feed_url=final_url, latest_item=title, latest_item_date=latest)
                return result
        if "html" in content_type or body[:100].lstrip().lower().startswith((b"<!doctype html", b"<html")):
            parser = _FeedLinks()
            parser.feed(body.decode(response.encoding or "utf-8", errors="replace"))
            from urllib.parse import urljoin
            links.extend(urljoin(final_url, x) for x in parser.links)
        links.extend(f"https://{domain}{path}" for path in FEED_PATHS)
        seen = set()
        for feed_url in links:
            if feed_url in seen or not _safe_https(feed_url):
                continue
            seen.add(feed_url)
            try:
                fr = _safe_get(feed_url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
                if fr.status_code >= 400 or not _safe_https(fr.url):
                    continue
                fbody = fr.content[:2_000_000]
                latest, title = _feed_latest(fbody)
                if title or b"<rss" in fbody[:1000].lower() or b"<feed" in fbody[:1000].lower():
                    result.update(status="healthy_feed", feed_url=fr.url, latest_item=title, latest_item_date=latest)
                    return result
            except requests.RequestException:
                continue
        result["status"] = "healthy_no_feed"
        result["error"] = "الموقع متاح لكن لم يتم اكتشاف RSS/Atom بالمسارات العامة"
        return result
    except requests.Timeout:
        result.update(status="timeout", error="انتهت مهلة الاتصال")
    except requests.RequestException as exc:
        result.update(status="unreachable_or_blocked", error=type(exc).__name__)
    except Exception as exc:
        result.update(status="probe_error", error=type(exc).__name__)
    result["latency_ms"] = round((time.monotonic() - started) * 1000)
    return result


def scan_sources(names=None, max_workers=8, timeout=8):
    selected = [x for x in SOURCE_CATALOG if not names or x["name"] in set(names) or x["domain"] in set(names)]
    rows = []
    with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), 12))) as pool:
        futures = {pool.submit(check_source_health, row, timeout): row for row in selected}
        for future in as_completed(futures):
            rows.append(future.result())
    order = {x["domain"]: i for i, x in enumerate(selected)}
    rows.sort(key=lambda x: order.get(x["domain"], 99999))
    checked_at = datetime.now(timezone.utc).isoformat()
    return {"id": hashlib.sha256(checked_at.encode("utf-8")).hexdigest()[:16], "checked_at": checked_at,
            "total": len(rows), "rows": rows,
            "counts": {status: sum(1 for x in rows if x["status"] == status) for status in sorted({x["status"] for x in rows})}}



def compare_health_runs(current, previous=None):
    """Annotate current probe against the last saved probe for each domain."""
    previous = previous or {}
    old_rows = {x.get("domain"): x for x in previous.get("rows", []) if x.get("domain")}
    for row in current.get("rows", []):
        old = old_rows.get(row.get("domain"))
        row["previous_status"] = old.get("status") if old else ""
        row["previous_feed_url"] = old.get("feed_url") if old else ""
        row["last_successful_check"] = ""
        if old:
            if old.get("status") in ("healthy_feed", "healthy_no_feed"):
                row["last_successful_check"] = old.get("checked_at") or ""
            else:
                row["last_successful_check"] = old.get("last_successful_check") or ""
            if old.get("status") == "healthy_feed" and row.get("status") == "healthy_feed" and old.get("feed_url") != row.get("feed_url"):
                row["change_status"] = "feed_changed"
                row["change_note"] = "تغير رابط RSS/Atom مقارنة بالفحص السابق"
            elif old.get("status") == "healthy_feed" and row.get("status") == "healthy_no_feed":
                row["change_status"] = "feed_lost"
                row["change_note"] = "كان هناك RSS/Atom في الفحص السابق ولم يتم اكتشافه الآن"
            elif old.get("status") not in ("healthy_feed", "healthy_no_feed") and row.get("status") in ("healthy_feed", "healthy_no_feed"):
                row["change_status"] = "recovered"
                row["change_note"] = "عاد الموقع للاستجابة بعد تعذر الوصول سابقاً"
            elif old.get("status") in ("healthy_feed", "healthy_no_feed") and row.get("status") not in ("healthy_feed", "healthy_no_feed"):
                row["change_status"] = "site_unreachable"
                row["change_note"] = "تعذر الوصول بعد أن كان الموقع متاحاً؛ قد يكون حجباً أو عطلاً مؤقتاً"
            elif old.get("latest_item") != row.get("latest_item") and row.get("latest_item"):
                row["change_status"] = "new_feed_item"
                row["change_note"] = "ظهر عنوان أحدث أو مختلف في الخلاصة"
            else:
                row["change_status"] = "unchanged"
                row["change_note"] = "لا تغيير واضح مقارنة بالفحص السابق"
        else:
            row["change_status"] = "first_check"
            row["change_note"] = "أول فحص محفوظ لهذا النطاق"
        if row.get("status") in ("healthy_feed", "healthy_no_feed"):
            row["last_successful_check"] = current.get("checked_at", "")
    return current


def _tokens(text):
    words = re.findall(r"[\w\u0590-\u05ff'-]{2,}", (text or "").lower())
    stop = {"the", "and", "for", "with", "from", "that", "this", "after", "over", "into", "says", "said", "will", "has", "have", "من", "على", "إلى", "الى", "في", "عن", "مع", "هذا", "هذه", "التي", "الذي", "بين", "بعد", "قبل", "وقال", "قال"}
    return {x for x in words if x not in stop and len(x) > 2}


def _similarity(a, b):
    aa, bb = _tokens(a), _tokens(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def _normal_title(title):
    x = re.sub(r"\s+[|–-]\s+[^|–-]{2,45}$", "", title or "")
    return " ".join(re.sub(r"[^\w\u0590-\u05ff]+", " ", x.lower()).split())


def _side_for_domain(domain):
    d = _domain(domain)
    for suffix, row in SOURCE_BY_DOMAIN.items():
        if d == suffix or d.endswith("." + suffix):
            return row.get("side", "other"), row
    return "other", {"name": d, "side": "other", "intel_type": "media"}


def _kind(article):
    domain = _domain(article.get("domain") or article.get("url"))
    side, source = _side_for_domain(domain)
    title = article.get("title", "")
    if ANALYSIS_WORDS.search(title) or source.get("intel_type") == "think":
        return "تحليل أو رأي", "العنوان أو تصنيف الجهة يشير إلى تحليل، وليس خبراً أولياً بالضرورة"
    if any(domain == d or domain.endswith("." + d) for d in WIRE_DOMAINS):
        return "وكالة أنباء/ناقل محتمل", "مصدر وكالة؛ يلزم مقارنة توقيت النشر والمراجع لتحديد الأصل"
    return "تغطية خبرية", "تصنيف مبدئي من نوع المصدر والعنوان فقط"


def normalize_article(row):
    url = row.get("url") or row.get("link") or ""
    domain = _domain(row.get("domain") or row.get("source_url") or url)
    side, source = _side_for_domain(domain)
    title = (row.get("title") or "").strip()
    date = row.get("published_at") or row.get("seendate") or row.get("date") or row.get("published") or ""
    if isinstance(date, datetime):
        date = date.astimezone(timezone.utc).isoformat() if date.tzinfo else date.replace(tzinfo=timezone.utc).isoformat()
    if isinstance(date, str) and re.fullmatch(r"\d{8}T\d{6}Z", date):
        try:
            date = datetime.strptime(date, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    kind, rationale = _kind({**row, "domain": domain})
    item = {"title": title, "title_ar": row.get("title_ar") or "",
            "url": url, "domain": domain, "source_name": row.get("source_name") or source.get("name") or domain,
            "side": side, "side_label": SIDE_LABELS.get(side, SIDE_LABELS["other"]), "published_at": str(date),
            "kind": kind, "classification_note": rationale, "author": row.get("author") or "",
            "excerpt": row.get("excerpt") or row.get("description") or "", "discovery_method": row.get("discovery_method", "GDELT/Google News")}
    item["id"] = hashlib.sha256((item["url"] or item["domain"] + item["title"]).encode("utf-8")).hexdigest()[:16]
    return item


def collect_articles(query, days=7, limit=120, sides=("us", "il", "uk", "ar")):
    """Search GDELT plus Google News domain-scoped feeds for selected perspectives."""
    query = (query or "").strip()
    if len(query) < 3:
        return [], ["اكتب عبارة بحث من 3 أحرف على الأقل."]
    days = max(1, min(int(days), 90))
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    raw, notes = [], []
    try:
        gdelt, err = core.gdelt_call(query, start, end, min(250, int(limit)))
        if err:
            notes.append("GDELT: " + str(err)[:180])
        raw.extend({**x, "discovery_method": "GDELT"} for x in gdelt)
    except Exception as exc:
        notes.append("GDELT: " + type(exc).__name__)
    selected_rows = []
    side_to_groups = {"us": [sources.USA], "il": [sources.ISRAEL], "uk": [sources.UK], "ar": [sources.ARABIC, sources.REGION]}
    for side in sides:
        for mapping in side_to_groups.get(side, []):
            for entries in mapping.values():
                for name, domains, lang in entries:
                    selected_rows.append((name, domains, lang))
    # Limit domains to avoid huge RSS fan-out and keep request count bounded.
    selected_rows = selected_rows[:160]
    if selected_rows:
        try:
            terms = [query]
            news, nnotes = core.gnews_site_search(selected_rows, days, terms=terms, joiner="OR", country="US", verify_author=False, max_items=min(180, int(limit)))
            raw.extend({**x, "discovery_method": "Google News RSS"} for x in news)
            notes.extend(nnotes[:8])
        except Exception as exc:
            notes.append("Google News RSS: " + type(exc).__name__)
    dedup, out = set(), []
    for row in raw:
        item = normalize_article(row)
        if not item["url"] or not item["title"]:
            continue
        key = item["url"].split("?")[0].rstrip("/") or item["id"]
        if key in dedup:
            continue
        dedup.add(key)
        out.append(item)
    out.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    try:
        core.translate_titles(out)
    except Exception as exc:
        notes.append("تعذرت ترجمة بعض العناوين: " + type(exc).__name__)
        for item in out:
            item["title_ar"] = item.get("title_ar") or item.get("title", "")
    return out[:limit], notes


def cluster_articles(articles, threshold=0.16, max_gap_days=5):
    """Connected-component clustering. Scores are heuristic and never prove same-event identity."""
    rows = [normalize_article(x) if "side_label" not in x else x for x in articles]
    n = len(rows)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    parsed_dates = []
    for row in rows:
        try:
            dt = datetime.fromisoformat((row.get("published_at") or "").replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            parsed_dates.append(dt)
        except Exception:
            parsed_dates.append(None)
    for i in range(n):
        for j in range(i + 1, n):
            if parsed_dates[i] and parsed_dates[j] and abs((parsed_dates[i] - parsed_dates[j]).total_seconds()) > max_gap_days * 86400:
                continue
            a, b = rows[i], rows[j]
            sim = _similarity(a.get("title", ""), b.get("title", ""))
            norm_a, norm_b = _normal_title(a.get("title", "")), _normal_title(b.get("title", ""))
            exact = bool(norm_a and norm_b and (norm_a == norm_b or norm_a in norm_b or norm_b in norm_a))
            if exact or sim >= threshold:
                union(i, j)
    groups = {}
    for i, row in enumerate(rows):
        groups.setdefault(find(i), []).append(row)
    clusters = []
    for group in groups.values():
        if len(group) < 2:
            continue
        group.sort(key=lambda x: x.get("published_at") or "9999", reverse=False)
        sides = {s: [x for x in group if x.get("side") == s] for s in ("us", "il", "uk", "ar", "other")}
        narrative = {}
        for side, items in sides.items():
            if items:
                label = SIDE_LABELS.get(side, SIDE_LABELS["other"])
                narrative[label] = [{"source": x.get("source_name"), "title_ar": x.get("title_ar"), "title": x.get("title"), "url": x.get("url"), "kind": x.get("kind")} for x in items[:12]]
        exact_titles = {}
        for x in group:
            exact_titles.setdefault(_normal_title(x.get("title", "")), []).append(x)
        syndicated = any(len(v) > 1 for v in exact_titles.values())
        earliest = next((x for x in group if x.get("published_at")), group[0])
        lead = max(group, key=lambda x: len(_tokens(x.get("title", ""))))
        topic = lead.get("title_ar") or lead.get("title")
        cluster_id = hashlib.sha256("|".join(sorted(x.get("id", "") for x in group)).encode()).hexdigest()[:14]
        classifications = []
        for x in group:
            if x.get("kind") == "تحليل أو رأي":
                x["origin_assessment"] = "تحليل مستقل/رأي محتمل"
            elif x.get("domain") in WIRE_DOMAINS:
                x["origin_assessment"] = "وكالة/ناقل محتمل"
            elif x is earliest:
                x["origin_assessment"] = "أقدم توقيت مرصود، وليس إثباتاً للأصل"
            elif syndicated:
                x["origin_assessment"] = "إعادة نشر أو تطابق محتمل، يحتاج فحص النص والتوقيت"
            else:
                x["origin_assessment"] = "تغطية مستقلة أو متابعة، غير محسوم"
            classifications.append({"source": x.get("source_name"), "domain": x.get("domain"), "assessment": x["origin_assessment"], "url": x.get("url")})
        clusters.append({"id": cluster_id, "topic_ar": topic, "topic_original": lead.get("title", ""),
                         "article_count": len(group), "source_count": len({x.get("domain") for x in group}),
                         "sides": [SIDE_LABELS[s] for s, items in sides.items() if items],
                         "articles": group, "narratives": narrative, "origin_assessments": classifications,
                         "syndication_possible": syndicated,
                         "caveat": "التجميع والتصنيف استدلال آلي من العناوين والتوقيت ونوع المصدر؛ لا يثبت إعادة النشر أو المصدر الأصلي دون فحص النص الكامل ومراجعته.",
                         "created_at": datetime.now(timezone.utc).isoformat()})
    clusters.sort(key=lambda x: (x["article_count"], x["source_count"]), reverse=True)
    return clusters


def build_case_dossier(query, articles, clusters=None):
    clusters = clusters if clusters is not None else cluster_articles(articles)
    case_id = hashlib.sha256((query + datetime.now(timezone.utc).date().isoformat()).encode()).hexdigest()[:16]
    return {"schema_version": 1, "id": case_id, "case_id": case_id,
            "title": query, "title_ar": core.tr(query, "auto", "ar"), "created_at": datetime.now(timezone.utc).isoformat(),
            "article_count": len(articles), "cluster_count": len(clusters), "articles": articles,
            "event_clusters": clusters,
            "methodology": ["GDELT وGoogle News RSS لاكتشاف العناوين", "تجميع تقريبي حسب تشابه العنوان والتوقيت", "مقارنة زوايا التغطية حسب نطاق المصدر", "الترجمة العربية لا تلغي الاحتفاظ بالنص الأصلي والرابط"],
            "limitations": ["التجميع لا يثبت أن المقالات تتناول الحدث نفسه بنسبة يقين", "أقدم توقيت مرصود لا يثبت المصدر الأصلي", "التصنيف لا يستنتج موقفاً سياسياً من العنوان وحده", "المصادر الرسمية تمثل رواية الجهة صاحبة البيان ولا تعد تحققاً مستقلاً"]}

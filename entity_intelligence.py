# -*- coding: utf-8 -*-
"""Phase 8.20: entity resolution, publication timelines and evidence-led contradiction candidates."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone

import case_links

# Curated aliases only. This is deliberately not presented as general-purpose NER.
ENTITY_ALIASES = {
    "countries": {
        "إيران": ["إيران", "ايران", "Iran", "Iranian", "Tehran"],
        "الولايات المتحدة": ["الولايات المتحدة", "أمريكا", "امريكا", "United States", "U.S.", "US", "Washington"],
        "إسرائيل": ["إسرائيل", "اسرائيل", "Israel", "Israeli", "Tel Aviv"],
        "مصر": ["مصر", "Egypt", "Egyptian", "Cairo"],
        "المملكة المتحدة": ["بريطانيا", "المملكة المتحدة", "United Kingdom", "UK", "British", "London"],
        "السعودية": ["السعودية", "Saudi Arabia", "Saudi", "Riyadh"],
        "الإمارات": ["الإمارات", "الامارات", "UAE", "United Arab Emirates", "Abu Dhabi"],
        "اليمن": ["اليمن", "Yemen", "Yemeni", "Sanaa", "Aden"],
        "السودان": ["السودان", "Sudan", "Sudanese", "Khartoum", "Darfur"],
        "روسيا": ["روسيا", "Russia", "Russian", "Moscow"],
        "الصين": ["الصين", "China", "Chinese", "Beijing"],
        "تركيا": ["تركيا", "Turkey", "Turkish", "Ankara"],
        "أوكرانيا": ["أوكرانيا", "Ukraine", "Ukrainian", "Kyiv"],
        "قطر": ["قطر", "Qatar", "Doha"],
        "لبنان": ["لبنان", "Lebanon", "Lebanese", "Beirut"],
        "العراق": ["العراق", "Iraq", "Iraqi", "Baghdad"],
        "الصومال": ["الصومال", "Somalia", "Somali", "Mogadishu"],
    },
    "organizations": {
        "البنتاجون": ["البنتاجون", "البنتاغون", "Pentagon"],
        "وزارة الدفاع الأمريكية": ["وزارة الدفاع الأمريكية", "US Department of Defense", "Department of Defense", "DoD"],
        "القيادة المركزية الأمريكية": ["القيادة المركزية الأمريكية", "CENTCOM", "U.S. Central Command"],
        "الحرس الثوري الإيراني": ["الحرس الثوري", "IRGC", "Islamic Revolutionary Guard Corps"],
        "الجيش الإسرائيلي": ["الجيش الإسرائيلي", "جيش الدفاع الإسرائيلي", "IDF", "Israel Defense Forces"],
        "حلف الناتو": ["الناتو", "NATO", "North Atlantic Treaty Organization"],
        "الأمم المتحدة": ["الأمم المتحدة", "United Nations", "UN Security Council", "مجلس الأمن"],
        "الاتحاد الأوروبي": ["الاتحاد الأوروبي", "European Union", "EU"],
        "الوكالة الدولية للطاقة الذرية": ["الوكالة الدولية للطاقة الذرية", "IAEA", "International Atomic Energy Agency"],
        "حماس": ["حماس", "Hamas"], "حزب الله": ["حزب الله", "Hezbollah", "Hizbullah"],
        "أنصار الله": ["أنصار الله", "انصار الله", "الحوثيون", "الحوثي", "Houthis", "Houthi movement"],
    },
    "people": {
        "دونالد ترامب": ["Donald Trump", "ترامب", "دونالد ترامب"],
        "جو بايدن": ["Joe Biden", "بايدن", "جو بايدن"],
        "بنيامين نتنياهو": ["Benjamin Netanyahu", "نتنياهو", "بنيامين نتنياهو"],
        "علي خامنئي": ["Ali Khamenei", "Khamenei", "خامنئي", "علي خامنئي"],
        "مسعود بزشكيان": ["Masoud Pezeshkian", "Pezeshkian", "بزشكيان"],
        "عباس عراقجي": ["Abbas Araghchi", "Araghchi", "عراقجي"],
        "ماركو روبيو": ["Marco Rubio", "روبيو"],
        "بيت هيجسيث": ["Pete Hegseth", "هيجسيث"],
        "كيير ستارمر": ["Keir Starmer", "ستارمر"],
        "إسماعيل قاآني": ["Esmail Qaani", "إسماعيل قاآني", "اسماعيل قاآني"],
        "محمد باقري": ["Mohammad Bagheri", "محمد باقري"],
        "يحيى السنوار": ["Yahya Sinwar", "يحيى السنوار", "السنوار"],
        "عبد الملك الحوثي": ["Abdul-Malik al-Houthi", "Abdul Malik al Houthi", "عبدالملك الحوثي", "عبد الملك الحوثي"],
    },
    "ships": {
        "USS Abraham Lincoln": ["USS Abraham Lincoln", "يو إس إس أبراهام لينكولن", "أبراهام لينكولن"],
        "USS Gerald R. Ford": ["USS Gerald R. Ford", "جيرالد فورد", "Gerald Ford"],
        "USS Harry S. Truman": ["USS Harry S. Truman", "هاري ترومان"],
        "USS Dwight D. Eisenhower": ["USS Dwight D. Eisenhower", "دوايت أيزنهاور"],
        "USS Carl Vinson": ["USS Carl Vinson", "كارل فينسون"],
        "USS George H.W. Bush": ["USS George H.W. Bush", "جورج بوش"],
    },
    "bases": {
        "قاعدة العديد الجوية": ["قاعدة العديد", "Al Udeid Air Base", "Al Udeid"],
        "قاعدة الظفرة الجوية": ["قاعدة الظفرة", "Al Dhafra Air Base", "Al Dhafra"],
        "قاعدة عين الأسد": ["عين الأسد", "Ain al-Asad Airbase", "Al Asad Airbase"],
        "قاعدة موفق السلطي": ["قاعدة موفق السلطي", "Muwaffaq Salti Air Base"],
        "قاعدة إنجرليك": ["قاعدة إنجرليك", "Incirlik Air Base", "Incirlik"],
        "دييغو غارسيا": ["دييغو غارسيا", "Diego Garcia"],
        "معسكر ليمونييه": ["معسكر ليمونييه", "Camp Lemonnier"],
    },
}

NEGATIVE = {"نفى", "تنفي", "ينفي", "لم", "لا", "ليس", "رفض", "denied", "deny", "not", "no", "never", "false"}
POSITIVE = {"أكد", "اكد", "أكدت", "اكدت", "تؤكد", "تؤكد", "أعلن", "اعلن", "نفذ", "استهدف", "وقع", "confirmed", "announced", "carried", "struck", "hit", "occurred"}
STOP = {"من", "في", "على", "عن", "الى", "إلى", "مع", "بعد", "قبل", "هذا", "هذه", "the", "and", "for", "with", "from", "that", "this", "was", "were", "has", "have", "will", "said", "says"}


def _norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[أإآٱ]", "ا", s); s = s.replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"[^\w\u0600-\u06ff]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _contains(text, alias):
    t, a = _norm(text), _norm(alias)
    if not t or not a: return False
    return re.search(r"(?<![\w])" + re.escape(a) + r"(?![\w])", t) is not None


def extract_entities(text):
    found = []
    for category, mapping in ENTITY_ALIASES.items():
        for canonical, aliases in mapping.items():
            if any(_contains(text, alias) for alias in aliases):
                found.append({"name": canonical, "type": category, "matched_aliases": [a for a in aliases if _contains(text, a)]})
    # Existing broad country/actor lexicon complements the curated high-specificity list.
    for name in case_links.extract_entities(text):
        if not any(x["name"] == name for x in found):
            found.append({"name": name, "type": "countries_or_actors", "matched_aliases": [name]})
    return found


def _date(row):
    raw = row.get("published_at") or row.get("date") or row.get("seendate") or ""
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return ""


def build_entity_index(articles, cases=()):
    index = defaultdict(lambda: {"type": "", "mentions": [], "case_ids": set(), "domains": set()})
    for row in articles or []:
        title = row.get("title") or row.get("title_ar") or ""
        body = row.get("text") or row.get("summary") or ""
        for ent in extract_entities(title + "\n" + body):
            rec = index[ent["name"]]; rec["type"] = ent["type"]
            rec["mentions"].append({"title": title, "url": row.get("url", ""), "source": row.get("source_name") or row.get("source", ""),
                                    "domain": row.get("domain", ""), "published_at": _date(row), "matched_aliases": ent["matched_aliases"]})
            if row.get("domain"): rec["domains"].add(row["domain"])
    for case in cases or []:
        for ent in extract_entities(case_links.case_text(case)):
            rec = index[ent["name"]]; rec["type"] = ent["type"]
            rec["case_ids"].add(case.get("id", ""))
    out = []
    for name, rec in sorted(index.items()):
        out.append({"name": name, "type": rec["type"], "mention_count": len(rec["mentions"]),
                    "source_domains": sorted(x for x in rec["domains"] if x), "case_ids": sorted(x for x in rec["case_ids"] if x),
                    "mentions": rec["mentions"]})
    return out


def build_publication_timeline(articles):
    """A publication timeline, not an event-occurrence timeline unless event time is separately sourced."""
    rows = []
    for article in articles or []:
        published = _date(article)
        if not published: continue
        rows.append({"timestamp": published, "kind": "publication", "title": article.get("title_ar") or article.get("title") or "بلا عنوان",
                     "original_title": article.get("title", ""), "source": article.get("source_name") or article.get("source", ""),
                     "url": article.get("url", ""), "domain": article.get("domain", ""),
                     "time_basis": "تاريخ نشر المادة كما ورد في بيانات المصدر، وليس بالضرورة وقت وقوع الحدث"})
    rows.sort(key=lambda x: x["timestamp"])
    return rows


def _claim_terms(text):
    return {x for x in _norm(text).split() if len(x) > 2 and x not in STOP and not x.isdigit()}


def _polarity(text):
    words = set(_norm(text).split())
    neg = bool(words & {_norm(x) for x in NEGATIVE})
    pos = bool(words & {_norm(x) for x in POSITIVE})
    if neg and pos: return "mixed"
    if neg: return "negative"
    if pos: return "positive"
    return "unknown"


def detect_contradiction_candidates(articles, min_overlap=0.35):
    """Find only lexical/polarity candidates among similar claims; never adjudicates truth."""
    rows = []
    for a in articles or []:
        title = a.get("title") or a.get("title_ar") or ""
        text = a.get("text") or a.get("summary") or ""
        # Do not elevate headlines alone into claim-level contradiction evidence.
        if not text.strip():
            continue
        claim = text[:1200].strip()
        terms = _claim_terms(claim)
        if len(terms) < 3: continue
        rows.append((a, claim, terms, _polarity(claim)))
    out = []
    for i, (a, ca, ta, pa) in enumerate(rows):
        for b, cb, tb, pb in rows[i+1:]:
            if a.get("url") and a.get("url") == b.get("url"): continue
            union = ta | tb
            overlap = len(ta & tb) / max(1, len(union))
            if overlap < min_overlap or pa == pb or "unknown" in (pa, pb) or "mixed" in (pa, pb): continue
            # At least one source-specific assertion is required; shared vocabulary alone is insufficient.
            shared = sorted(ta & tb)
            cid = hashlib.sha256((str(a.get("url"))+"|"+str(b.get("url"))+"|"+" ".join(shared)).encode()).hexdigest()[:16]
            out.append({"id": cid, "status": "candidate_review_required", "overlap": round(overlap, 3),
                        "claim_a": ca, "claim_b": cb, "polarity_a": pa, "polarity_b": pb,
                        "shared_terms": shared[:20],
                        "source_a": {"name": a.get("source_name") or a.get("source", ""), "url": a.get("url", ""), "published_at": _date(a)},
                        "source_b": {"name": b.get("source_name") or b.get("source", ""), "url": b.get("url", ""), "published_at": _date(b)},
                        "caveat": "مرشح آلي أولي؛ قد يكون الاختلاف بسبب النفي أو التوقيت أو اختلاف التعريف أو اقتباس غير مباشر. لا يمثل حكماً بأن أحد الادعاءين كاذب."})
    out.sort(key=lambda x: (-x["overlap"], x["id"]))
    return out


def link_new_articles_to_cases(articles, cases, min_score=18):
    results = []
    for article in articles or []:
        pseudo = {"id": "incoming", "title": article.get("title_ar") or article.get("title", ""),
                  "description": article.get("summary") or article.get("text", ""), "tags": [],
                  "materials": [{"title": article.get("title", ""), "text": article.get("text") or article.get("summary", ""), "url": article.get("url", "")}],
                  "claims": [], "events": [], "research_notes": ""}
        matches = []
        for case in cases or []:
            detail = case_links.compare_cases(pseudo, case)
            if detail["score"] >= min_score:
                matches.append({"case_id": case.get("id"), "case_title": case.get("title"), **detail})
        if matches:
            results.append({"article": {"title": pseudo["title"], "url": article.get("url", ""), "source": article.get("source_name", "")},
                            "matches": sorted(matches, key=lambda x: -x["score"])[:5]})
    return results


def enrich_dossier(dossier, cases=()):
    articles = dossier.get("articles", [])
    entities = build_entity_index(articles, cases)
    timeline = build_publication_timeline(articles)
    contradictions = detect_contradiction_candidates(articles)
    links = link_new_articles_to_cases(articles, cases)
    return {**dossier, "entity_index": entities, "publication_timeline": timeline,
            "contradiction_candidates": contradictions, "prior_case_matches": links,
            "phase_820_methodology": [
                "استخراج الكيانات من قاموس أسماء ومرادفات معلن وقابل للتوسيع؛ ليس تعرّفاً شاملاً على الأسماء.",
                "ربط الكيانات بالمواد وملفات القضايا عبر المطابقة النصية مع حفظ الروابط والنطاقات.",
                "الخط الزمني يعرض تواريخ النشر المتاحة، ولا يستنتج وقت وقوع الحدث.",
                "التناقضات مرشحات لغوية للمراجعة البشرية ولا تحسم صدق الادعاءات.",
                "روابط الملفات القديمة مبنية على تشابه موضوعي وكيانات مشتركة، ولا تثبت علاقة سببية."]}

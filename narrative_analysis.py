# -*- coding: utf-8 -*-
"""Phase 8.33: evidence-led comparison of competing source narratives.

This module organizes recorded material. It does not determine which account is true.
"""
from __future__ import annotations
import hashlib
import json
import re
from urllib.parse import urlparse

STOP = {"من", "في", "على", "عن", "الى", "إلى", "مع", "بعد", "قبل", "هذا", "هذه", "ذلك", "التي", "الذي", "the", "and", "for", "with", "from", "that", "this", "was", "were", "has", "have", "will", "said", "says", "their", "they"}
NEG = {"نفى", "تنفي", "ينفي", "لم", "لا", "ليس", "رفض", "deny", "denied", "not", "no", "never"}
POS = {"أكد", "اكد", "أكدت", "أعلن", "اعلن", "وقع", "حدث", "نفذ", "استهدف", "confirmed", "announced", "occurred", "carried", "struck"}


def _norm(value):
    s = str(value or "").lower()
    s = re.sub(r"[أإآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\u0600-\u06ff]+", " ", s)).strip()


def _terms(value):
    return {w for w in _norm(value).split() if len(w) > 2 and w not in STOP and not w.isdigit()}


def _polarity(value):
    words = set(_norm(value).split())
    neg, pos = bool(words & NEG), bool(words & POS)
    if neg and pos: return "مختلط/غير واضح"
    if neg: return "نفي أو رفض"
    if pos: return "إثبات أو إعلان"
    return "غير محدد لغوياً"


def _domain(row):
    domain = str(row.get("domain") or "").lower().replace("www.", "")
    if not domain and row.get("url"):
        try: domain = urlparse(row["url"]).netloc.lower().replace("www.", "")
        except Exception: pass
    return domain


def _source(row):
    return str(row.get("outlet") or row.get("source") or row.get("author") or _domain(row) or "مصدر غير محدد").strip()


def _material_text(row):
    return str(row.get("text") or row.get("summary") or row.get("note") or "").strip()


def compare_narratives(materials, claims=(), min_overlap=0.18):
    """Build source map, potential claim tensions, and evidence gaps from saved case data."""
    rows = [dict(x) for x in (materials or []) if isinstance(x, dict)]
    source_map = {}
    for row in rows:
        name, domain = _source(row), _domain(row)
        key = domain or _norm(name)
        bucket = source_map.setdefault(key, {"source": name, "domain": domain, "items": [], "independence_note": ""})
        bucket["items"].append({"id": row.get("id", ""), "title": row.get("title", ""), "date": row.get("date", ""), "url": row.get("url", ""), "speaker": row.get("speaker") or row.get("actor") or "", "text_available": bool(_material_text(row))})
    for bucket in source_map.values():
        bucket["independence_note"] = "مواد من النطاق نفسه لا تُحسب تلقائياً مصادر مستقلة؛ افحص النقل وإعادة النشر." if bucket["domain"] else "النطاق غير معروف؛ لا يمكن تقييم استقلال المصدر من البيانات المتاحة."

    candidates = []
    usable = []
    for row in rows:
        text = _material_text(row)
        terms = _terms(text)
        if text and len(terms) >= 4:
            usable.append((row, text[:2500], terms, _polarity(text)))
    for i, (a, ta_text, ta, pa) in enumerate(usable):
        for b, tb_text, tb, pb in usable[i+1:]:
            if a.get("url") and a.get("url") == b.get("url"):
                continue
            overlap = len(ta & tb) / max(1, len(ta | tb))
            if overlap < min_overlap:
                continue
            da, db = _domain(a), _domain(b)
            same_domain = bool(da and da == db)
            # Similar subject matter is a comparison lead, not automatically a contradiction.
            kind = "اختلاف لغوي محتمل" if pa != pb and "غير محدد" not in (pa, pb) else "تغطيتان متقاربتان تحتاجان مقارنة"
            shared = sorted(ta & tb)
            ident = hashlib.sha256((str(a.get("id") or a.get("url")) + "|" + str(b.get("id") or b.get("url"))).encode()).hexdigest()[:16]
            candidates.append({"id": ident, "kind": kind, "overlap": round(overlap, 3),
                "source_a": _source(a), "source_b": _source(b), "domain_a": da, "domain_b": db,
                "same_domain": same_domain, "title_a": a.get("title", ""), "title_b": b.get("title", ""),
                "date_a": a.get("date", ""), "date_b": b.get("date", ""), "url_a": a.get("url", ""), "url_b": b.get("url", ""),
                "text_a": ta_text, "text_b": tb_text, "polarity_a": pa, "polarity_b": pb, "shared_terms": shared[:18],
                "review_questions": ["هل يتحدث المصدران عن الحدث نفسه والتوقيت نفسه؟", "هل أحد النصين ينقل عن الآخر أو عن مصدر مشترك؟", "هل الاختلاف في الواقعة أم الرقم أم التعريف أم النفي أم التفسير؟", "ما الوثيقة أو الشهادة الأولية التي يمكن أن تختبر الادعاء؟"],
                "caveat": "مرشح للمراجعة وليس إثباتاً لوجود تناقض أو حكماً بصحة أي رواية."})
    candidates.sort(key=lambda x: (-x["overlap"], x["id"]))

    claim_rows = []
    for claim in claims or []:
        if not isinstance(claim, dict): continue
        claim_rows.append({"statement": claim.get("statement", ""), "type": claim.get("type", ""), "status": claim.get("status", ""), "source": claim.get("source", ""), "note": claim.get("note", "")})
    independent_domains = sorted({x["domain"] for x in source_map.values() if x["domain"]})
    return {"schema": "marsad-narrative-comparison-v1", "material_count": len(rows), "usable_text_count": len(usable),
        "source_count": len(source_map), "distinct_domains": len(independent_domains), "sources": list(source_map.values()),
        "comparison_candidates": candidates[:300], "registered_claims": claim_rows,
        "limitations": ["التحليل يعتمد على المواد المحفوظة داخل ملف القضية فقط.", "تشابه الموضوع أو اختلاف ألفاظ النفي لا يكفي وحده لإثبات تناقض.", "اختلاف المصدرين لا يثبت استقلالهما؛ يجب فحص الاقتباس وإعادة النشر والمصدر الأولي.", "لا يصدر المحرك حكماً بالحقيقة أو الكذب ولا يقيّم النوايا.", "المقتطفات القصيرة والعناوين لا تعادل نص المقال الكامل."]}


def build_comparison_prompt(case, report):
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    return f"""أنت محلل مصادر وأدلة. حلّل ملف القضية التالي دون افتراض صحة أي رواية مسبقاً.

القضية: {case.get('title','')}
نطاق القضية: {case.get('description','')}

المطلوب:
1. اعرض كل مصدر وروايته بصورة منفصلة مع الرابط والتاريخ.
2. افصل الوقائع المنسوبة عن الادعاءات والتفسير والتوقع.
3. صنّف كل اختلاف: واقعة، رقم، توقيت، تعريف، نفي/إثبات، سبب، أو تفسير.
4. لا تسمِّ الاختلاف تناقضاً مؤكداً إلا إذا كان الادعاءان يتناولان الواقعة والتوقيت والتعريف نفسيهما ويتعذر اجتماعهما.
5. افحص استقلال المصادر واحتمال النقل عن مصدر واحد أو إعادة النشر.
6. أنشئ مصفوفة: نقطة الاتفاق، نقطة الاختلاف، الأدلة المؤيدة لكل طرف، الأدلة الناقصة، وخطوة التحقق التالية.
7. قيّم قوة الإسناد لا صدق الرواية، واشرح سبب كل تقدير وثقته وحدوده.
8. لا تستنتج النوايا ولا تملأ الفراغات بالتخمين. إذا كان النص مقتطفاً أو غير متاح فاذكر ذلك.
9. اختم بما يمكن قوله بثقة، وما يظل مفتوحاً، وأهم ثلاثة أسئلة بحثية.

بيانات المقارنة:
{payload}

تنبيه: البيانات أعلاه تجميع أولي من ملف القضية وليست تحققاً مستقلاً من الوقائع."""

# -*- coding: utf-8 -*-
"""Phase 8.36: evidence-linked intelligence report center (offline-first)."""
from __future__ import annotations
from datetime import datetime, timezone
import prompt_style
import hashlib
import json

REPORT_TYPES = ["تقرير استخباراتي شامل للقضية", "موجز التطورات اليومية", "مقارنة الروايات والمصادر", "تقرير شبكة الأطراف", "تقرير الإنذارات والتغيرات", "تقرير فجوات التحقق"]


def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _source_id(material):
    raw = str(material.get("url") or material.get("id") or material.get("title") or "")
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def build_report(case, report_type="تقرير استخباراتي شامل للقضية", alerts=None, network=None, narrative=None):
    case = dict(case or {})
    materials = list(case.get("materials") or [])
    claims = list(case.get("claims") or [])
    events = sorted(list(case.get("events") or []), key=lambda x: (str(x.get("date") or "9999"), str(x.get("created_at") or "")))
    sources = []
    for m in materials:
        sources.append({"source_id": _source_id(m), "title": m.get("title") or "بلا عنوان", "url": m.get("url") or "",
                        "outlet": m.get("outlet") or "غير محدد", "domain": m.get("domain") or "",
                        "author": m.get("author") or "غير محدد", "date": m.get("date") or "غير محدد",
                        "type": m.get("type") or "غير محدد", "text_available": bool(m.get("text")),
                        "text_excerpt": str(m.get("text") or "")[:1800]})
    claims_out = [{"statement": c.get("statement"), "type": c.get("type"), "evidence_status": c.get("status"),
                   "source": c.get("source") or "غير مرفق", "note": c.get("note") or ""} for c in claims]
    gaps = []
    if not materials: gaps.append("لا توجد مواد مصدرية داخل الملف.")
    if materials and not any(m.get("text") for m in materials): gaps.append("لا تتوفر نصوص أو مقتطفات محفوظة؛ العناوين وحدها لا تكفي لتحليل المحتوى.")
    if materials and not any(m.get("url") for m in materials): gaps.append("بعض/كل المواد تفتقر إلى روابط أصلية قابلة للمراجعة.")
    if not claims: gaps.append("لم يُدخل الباحث ادعاءات في سجل الادعاءات بعد.")
    if not events: gaps.append("لا يوجد خط زمني مدخل يدوياً.")
    if len({m.get("domain") or m.get("outlet") for m in materials if m.get("domain") or m.get("outlet")}) < 2:
        gaps.append("التنوع الظاهر للمصادر محدود؛ لا يمكن وصف التغطية بأنها مستقلة أو ممثلة.")
    payload = {"id": "report_" + hashlib.sha1((_stamp()+str(case.get("id"))+report_type).encode()).hexdigest()[:14],
               "created_at": _stamp(), "case_id": case.get("id"), "case_title": case.get("title") or "ملف بلا عنوان",
               "report_type": report_type, "material_count": len(materials), "claim_count": len(claims),
               "event_count": len(events), "sources": sources, "claims": claims_out, "events": events,
               "alerts": list(alerts or []), "network": network or {}, "narrative": narrative or {},
               "verification_gaps": gaps,
               "methodology": ["التقرير تجميعي من البيانات المحفوظة في ملف القضية وقت الإنشاء.",
                               "وجود المادة لا يعني صحة محتواها؛ الادعاءات تظل منسوبة لمصادرها وحالة دليلها.",
                               "لا تُعامل إعادة النشر أو تعدد الروابط كتأكيد مستقل دون فحص أصل المعلومات.",
                               "التواريخ المعروضة هي كما سجلها المصدر؛ يجب التمييز بين تاريخ الحدث وتاريخ النشر.",
                               "لا يستنتج التقرير النوايا أو العلاقات السببية من التزامن وحده."]}
    payload["summary"] = f"ملف {payload['case_title']}: {len(materials)} مادة، {len(claims)} ادعاء مسجل، و{len(events)} حدث مدخل. هذا تقرير مبني على السجل المتاح وقت الإنشاء، وليس تحققاً مستقلاً من كل معلومة."
    return payload


def report_markdown(report):
    r = report or {}
    lines = [f"# {r.get('report_type','تقرير استخباراتي')}", f"**القضية:** {r.get('case_title','غير محددة')}",
             f"**وقت الإنشاء:** {r.get('created_at','غير محدد')}", "", "## الملخص التنفيذي", r.get("summary", ""),
             "", "## المواد والمصادر"]
    for s in r.get("sources", []):
        lines += [f"### [{s['source_id']}] {s['title']}", f"- الناشر: {s['outlet']} | الكاتب: {s['author']} | التاريخ: {s['date']}",
                  f"- النوع: {s['type']} | النص متاح: {'نعم' if s['text_available'] else 'لا'}", f"- الرابط: {s['url'] or 'غير متاح'}",
                  f"- المقتطف: {s['text_excerpt'] or 'لا يوجد نص محفوظ'}", ""]
    lines += ["## سجل الادعاءات"]
    for c in r.get("claims", []): lines.append(f"- **{c.get('statement')}** | النوع: {c.get('type')} | حالة الدليل: {c.get('evidence_status')} | المصدر: {c.get('source')}")
    lines += ["", "## الخط الزمني"]
    for e in r.get("events", []): lines.append(f"- {e.get('date','غير محدد')}: {e.get('title','')} | {e.get('detail','')} | المصدر: {e.get('source','غير مرفق')}")
    lines += ["", "## فجوات التحقق"] + [f"- {x}" for x in r.get("verification_gaps", [])]
    lines += ["", "## المنهجية والقيود"] + [f"- {x}" for x in r.get("methodology", [])]
    return "\n".join(lines)


def build_analysis_prompt(report):
    compact = report_markdown(report)
    return """أنت محلل استخباراتي وإعلامي مستقل. حلّل التقرير المرفق دون افتراض صحة أي ادعاء.

المطلوب:
1) ملخص تنفيذي يميز ما هو معلوم عما هو غير معلوم.
2) جدول الوقائع والادعاءات، مع النسبة للمصدر وحالة التحقق.
3) مقارنة الروايات وتحديد الاتفاق والاختلاف والتناقض الحقيقي مقابل الاختلاف التفسيري.
4) فحص استقلال المصادر وكشف إعادة النشر والاعتماد على مصدر أصلي واحد.
5) تحليل الأطراف والمصالح المعلنة، مع فصل الاستنتاج عن المعلومة.
6) تقييم الأدلة المؤيدة والمعارضة وأقوى تفسير بديل.
7) تحديد فجوات المعلومات وما يلزم للتحقق، مع اقتراح أنواع مصادر أولية.
8) تقدير ثقة منفصل لكل استنتاج مع مبرراته.
9) خلاصة مشروطة وما المعلومات التي قد تغيرها.

ثم اكتب سكريبتاً باللهجة المصرية المبسطة: افتتاحية قوية غير مضللة، سياق سريع، عرض الأدلة والروايات المتنافسة، التفنيد والاحتمالات البديلة، ما يهم مصر والمنطقة إذا كان مدعوماً، وخاتمة بسؤال للجمهور. لا تختلق اقتباسات أو أرقاماً أو وقائع. أرفق ملاحظات إنتاج ومشاهد مقترحة، ثم قائمة تدقيق بالمعلومات التي يجب مراجعتها قبل النشر.

""" + prompt_style.source_block() + "\n" + prompt_style.WEB_RESEARCH + "\n\n" + prompt_style.CAIRO_STYLE + """
قواعد إلزامية: لا تحول الادعاء إلى حقيقة؛ لا تنسب رأي الكاتب إلى المؤسسة كلها؛ لا تعتبر تكرار الخبر تأكيداً مستقلاً؛ لا تستنتج نية أو علاقة أو مسؤولية بلا دليل؛ اذكر صراحة عندما لا يحتوي المصدر إلا عنواناً أو مقتطفاً.

=== التقرير ومصادره ===
""" + compact


def build_script_prompt(report):
    return ("حوّل التقرير التالي إلى سكريبت فيديو مصري تحليلي قابل للتسجيل، مع تفنيد الادعاءات وفصل الوقائع عن الرأي، وتوثيق كل نقطة بمصدرها. لا تضف معلومات من خارج التقرير إلا إذا وسمتها بوضوح كمعلومات تحتاج بحثاً خارجياً.\n\n"
            + prompt_style.script_rules() + "\n" + report_markdown(report))


def save_report(store, report, max_reports=500):
    rows = store.setdefault("intel_reports", [])
    if any(x.get("id") == report.get("id") for x in rows): return False
    rows.insert(0, report)
    del rows[max_reports:]
    return True

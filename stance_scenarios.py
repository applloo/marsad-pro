# -*- coding: utf-8 -*-
"""مقارنة تحولات المواقف وبناء سيناريوهات مشروطة من الأدلة المدخلة."""
from __future__ import annotations
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm(value):
    return " ".join(str(value or "").split()).casefold()


def compare_stances(case):
    """Compare explicitly attributed, dated stance notes. No automatic stance inference."""
    groups = {}
    for material in case.get("materials", []):
        actor = (material.get("author") or material.get("outlet") or "جهة غير محددة").strip()
        stance = (material.get("stance") or "").strip()
        if not stance:
            continue
        groups.setdefault(actor, []).append({
            "date": material.get("date") or "غير مؤرخ",
            "stance": stance,
            "title": material.get("title") or "مادة بلا عنوان",
            "type": material.get("type") or "غير محدد",
            "url": material.get("url") or "",
            "material_id": material.get("id") or "",
        })
    results = []
    for actor, entries in groups.items():
        entries.sort(key=lambda x: (x["date"] == "غير مؤرخ", x["date"]))
        if len(entries) < 2:
            continue
        first, latest = entries[0], entries[-1]
        changed = _norm(first["stance"]) != _norm(latest["stance"])
        results.append({"actor": actor, "first": first, "latest": latest,
                        "changed": changed, "count": len(entries),
                        "assessment": "اختلاف بين توصيفين يحتاج مراجعة السياق" if changed else "لا يظهر اختلاف في الموقف المدخل"})
    return sorted(results, key=lambda x: (not x["changed"], x["actor"]))


def build_comparison_prompt(case, comparisons=None):
    comparisons = comparisons if comparisons is not None else compare_stances(case)
    lines = []
    for item in comparisons:
        lines.append(f"الجهة/الكاتب: {item['actor']} | عدد المواد ذات الموقف المدخل: {item['count']}")
        lines.append(f"الأقدم ({item['first']['date']}): {item['first']['stance']} | {item['first']['title']} | {item['first']['url']}")
        lines.append(f"الأحدث ({item['latest']['date']}): {item['latest']['stance']} | {item['latest']['title']} | {item['latest']['url']}")
        lines.append(f"ملاحظة آلية: {item['assessment']}\n")
    return f"""أنت محلل مواقف إعلامية وسياسية. افحص المقارنة التالية لملف: {case.get('title','غير محدد')}.

{chr(10).join(lines) if lines else 'لا توجد جهات لديها موقفان مدخلان على الأقل.'}

المطلوب:
1) ميّز بين تغير موقف الجهة/الشخص وبين اختلاف موضوع المادة أو اختلاف الكاتب عن الخط التحريري للمؤسسة.
2) افحص النص الكامل والسياق والتاريخ ونوع المصدر قبل وصف أي حالة بأنها تحول موقف.
3) أنشئ جدولاً: الجهة، الموقف السابق، الموقف اللاحق، الدليل النصي، تفسير بديل، درجة الثقة، وما ينقص للتحقق.
4) لا تعتبر خانة الموقف اليدوية اقتباساً حرفياً ما لم يرفق النص الأصلي.
5) لا تستنتج نية أو تنسيقاً أو تحولاً استراتيجياً من عنوان أو مادة واحدة.
6) اذكر الحالات غير القابلة للمقارنة بوضوح. لا تخترع نصوصاً أو تواريخ أو روابط.
"""


def build_scenarios(case, drivers, horizon="30 يوماً"):
    """Create a transparent scenario worksheet from analyst-entered drivers."""
    clean = [str(x).strip() for x in (drivers or []) if str(x).strip()]
    return {
        "id": f"scenario_{int(datetime.now(timezone.utc).timestamp()*1000000)}",
        "case_id": case.get("id", ""), "case_title": case.get("title", ""),
        "created_at": now_iso(), "horizon": horizon, "drivers": clean,
        "scenarios": [
            {"name": "استمرار المسار الحالي", "question": "ما الذي يحدث إذا استمرت الاتجاهات الحالية دون تغير جوهري؟", "indicators": clean[:], "confidence": "يحددها الباحث"},
            {"name": "تصعيد / تدهور", "question": "ما الشروط التي قد تدفع إلى تدهور أو تصعيد؟", "indicators": clean[:], "confidence": "يحددها الباحث"},
            {"name": "احتواء / تهدئة", "question": "ما الشروط التي قد تدفع إلى احتواء أو تسوية؟", "indicators": clean[:], "confidence": "يحددها الباحث"},
        ],
        "caveat": "هذه قوالب سيناريوهات مشروطة وليست تنبؤات احتمالية. لا توجد احتمالات محسوبة أو تغذية تلقائية بالبيانات.",
    }


def build_scenario_prompt(record, case):
    scenarios = "\n".join(f"- {s['name']}: {s['question']} | مؤشرات المتابعة: {'، '.join(s['indicators']) or 'لم تحدد'}" for s in record.get("scenarios", []))
    materials = "\n".join(f"- {m.get('date','غير مؤرخ')} | {m.get('title','')} | {m.get('outlet','')} | {m.get('url','')} | الموقف المدخل: {m.get('stance') or 'غير مدخل'}" for m in case.get("materials", []))
    return f"""ابنِ تحليلاً بالسيناريوهات لملف {case.get('title','غير محدد')} خلال أفق {record.get('horizon','غير محدد')}.

المحركات التي أدخلها الباحث:
{chr(10).join(record.get('drivers', [])) or 'لم تُدخل محركات.'}

السيناريوهات المطلوب اختبارها:
{scenarios}

المواد المتاحة:
{materials or 'لا توجد مواد.'}

لكل سيناريو: الشروط المسبقة، سلسلة الأحداث المحتملة، مؤشرات مبكرة قابلة للرصد، عوامل تعوقه، أدلة تؤيده وأدلة تضعفه، وما الذي سيجعلنا نرفع أو نخفض تقديرنا. أضف سيناريو بديلاً إذا كانت السيناريوهات الثلاثة لا تغطي الاحتمالات.
لا تضع نسباً مئوية إلا إذا شرحت منهجاً وبيانات تبررها. افصل الوقائع عن الافتراضات، واذكر فجوات البيانات. هذا تمرين استشرافي مشروط وليس تنبؤاً مؤكداً.
"""

# -*- coding: utf-8 -*-
"""حزم تحليل قابلة لإعادة الاستخدام والتصدير، مع لقطات ثابتة من مواد القضية."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_article(item):
    item = dict(item or {})
    return {
        "id": item.get("id", ""), "type": item.get("type", "خبر"),
        "title": item.get("title") or item.get("title_ar") or "مادة بلا عنوان",
        "author": item.get("author") or item.get("writer") or "غير محدد",
        "outlet": item.get("outlet") or item.get("source") or item.get("domain") or "غير محدد",
        "domain": item.get("domain", ""), "date": item.get("date") or item.get("seendate") or "",
        "url": item.get("url") or item.get("link") or "",
        "text": item.get("text") or item.get("full_text") or item.get("summary") or item.get("snip_ar") or "",
        "stance": item.get("stance", ""), "note": item.get("note", ""),
    }


def build_package(case, prompt, prompt_name, model, threads=None, source_materials=None, package_history=None,
                  output_mode="تحليل + سكريبت مصري", audience="الجمهور العام", script_duration="3 إلى 5 دقائق"):
    """يبني لقطة مستقلة قابلة لإعادة الاستخدام والتصدير."""
    """يبني لقطة غير قابلة للتأثر بتعديلات القضية اللاحقة."""
    materials = [_clean_article(x) for x in (source_materials if source_materials is not None else case.get("materials", []))]
    snapshot = {
        "case_id": case.get("id", ""), "case_title": case.get("title", "ملف بلا عنوان"),
        "case_description": case.get("description", ""), "case_tags": list(case.get("tags", [])),
        "research_notes": case.get("research_notes", ""), "threads": list(threads or []),
        "materials": materials, "claims": list(case.get("claims", [])), "events": list(case.get("events", [])),
    }
    digest = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    previous = [x for x in (package_history or []) if x.get("case_id") == case.get("id")]
    version = max([int(x.get("version", 0)) for x in previous] or [0]) + 1
    return {
        "id": f"pkg_{int(datetime.now(timezone.utc).timestamp() * 1000000)}",
        "case_id": case.get("id", ""), "case_title": case.get("title", "ملف بلا عنوان"),
        "version": version, "created_at": now_iso(), "model": model,
        "prompt_name": prompt_name, "prompt": prompt, "snapshot": snapshot,
        "output_mode": output_mode, "audience": audience, "script_duration": script_duration,
        "sha256": digest, "material_count": len(materials),
        "source_count": len({x.get("domain") or x.get("outlet") for x in materials if x.get("domain") or x.get("outlet")}),
    }


def render_markdown(package):
    s = package["snapshot"]
    out = [f"# حزمة تحليل: {package['case_title']}", "", f"- رقم الإصدار: {package['version']}",
           f"- تاريخ الإنشاء: {package['created_at']}", f"- النموذج المستهدف: {package['model']}",
           f"- البرومبت: {package['prompt_name']}", f"- نمط المخرج: {package.get('output_mode', 'تحليل فقط')}",
           f"- الجمهور: {package.get('audience', 'غير محدد')}", f"- مدة السكريبت: {package.get('script_duration', 'غير محددة')}",
           f"- عدد المواد: {package['material_count']}",
           f"- عدد المصادر: {package['source_count']}", f"- بصمة الحزمة SHA-256: `{package['sha256']}`", "",
           "## الخيوط المختارة", *(f"- {x}" for x in s.get("threads", [])), "",
           "## وصف القضية", s.get("case_description") or "غير محدد", "",
           "## ملاحظات الباحث", s.get("research_notes") or "لا توجد", "", "## المواد والمصادر"]
    for i, m in enumerate(s.get("materials", []), 1):
        out += [f"### [{i}] {m['title']}", f"- النوع: {m['type']}", f"- الكاتب: {m['author']}",
                f"- المصدر: {m['outlet']} ({m['domain']})", f"- التاريخ: {m['date'] or 'غير محدد'}",
                f"- الرابط الأصلي: {m['url'] or 'غير متاح'}", f"- النص/الملخص المتاح: {m['text'] or 'لا يوجد نص محفوظ'}", ""]
    out += ["## سجل الادعاءات"]
    for c in s.get("claims", []):
        out.append(f"- {c.get('statement')} | النوع: {c.get('type')} | الحالة: {c.get('status')} | المصدر: {c.get('source')}")
    out += ["", "## الخط الزمني"]
    for e in sorted(s.get("events", []), key=lambda x: x.get("date") or "9999"):
        out.append(f"- {e.get('date')}: {e.get('title')} | {e.get('detail')} | المصدر: {e.get('source')}")
    out += ["", "---", "# تعليمات التحليل", package.get("prompt", ""), "", "## قواعد سلامة التحليل",
            "- افصل الوقائع المثبتة عن الادعاءات والتفسيرات والتوقعات.",
            "- لا تعتبر تكرار الخبر تأكيداً مستقلاً إذا كانت المواد تنقل عن أصل واحد.",
            "- لا تخترع معلومات أو اقتباسات أو روابط، وصرّح بوضوح بما لا يتوفر من بيانات.",
            "- اربط كل استنتاج بمادته ومصدره، واذكر درجة الثقة وحدودها."]
    return "\n".join(out)


def render_text(package):
    return render_markdown(package)


def render_json(package):
    return json.dumps(package, ensure_ascii=False, indent=2)

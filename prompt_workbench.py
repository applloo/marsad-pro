# -*- coding: utf-8 -*-
"""مكتبة برومبتات بإصدارات محفوظة، دون حذف النسخ السابقة."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import uuid
import json
import re

import prompt_style

CATEGORIES = [
    "استخراج المعلومات", "ربط الأحداث", "التحليل الجيوسياسي",
    "التحقق ومقارنة المصادر", "كتابة السكريبتات", "إنتاج المحتوى", "عام",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _version(number: int, body: str, note: str = "") -> dict:
    body = str(body or "").strip()
    if not body:
        raise ValueError("محتوى البرومبت لا يمكن أن يكون فارغاً")
    return {
        "version": int(number), "body": body, "note": str(note or "").strip(),
        "created_at": now_iso(), "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }


def create_prompt(records: list, name: str, body: str, category: str = "عام",
                  description: str = "", tags: list | None = None) -> dict:
    name = str(name or "").strip()
    if not name:
        raise ValueError("اكتب اسماً للبرومبت")
    if any(x.get("name", "").casefold() == name.casefold() and x.get("status", "active") == "active" for x in records):
        raise ValueError("يوجد برومبت نشط بالاسم نفسه. اختر اسماً آخر أو حدّث النسخة الموجودة")
    if category not in CATEGORIES:
        category = "عام"
    record = {
        "id": "pr_" + uuid.uuid4().hex[:16], "name": name, "category": category,
        "description": str(description or "").strip(), "tags": list(tags or []),
        "status": "active", "current_version": 1,
        "versions": [_version(1, body, "الإصدار الأول")], "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    records.insert(0, record)
    return record


def save_version(records: list, prompt_id: str, body: str, note: str = "") -> dict:
    record = next((x for x in records if x.get("id") == prompt_id), None)
    if not record:
        raise ValueError("البرومبت المطلوب غير موجود")
    if record.get("status") != "active":
        raise ValueError("لا يمكن تعديل برومبت مؤرشف. استعده أولاً")
    versions = record.setdefault("versions", [])
    current = next((v for v in versions if int(v.get("version", 0)) == int(record.get("current_version", 0))), None)
    clean_body = str(body or "").strip()
    if not clean_body:
        raise ValueError("محتوى البرومبت لا يمكن أن يكون فارغاً")
    if current and current.get("body", "").strip() == clean_body:
        raise ValueError("لم يتغير محتوى البرومبت، لم يتم إنشاء إصدار مكرر")
    new = _version(max([int(v.get("version", 0)) for v in versions] or [0]) + 1, clean_body, note)
    versions.append(new)
    record["current_version"] = new["version"]
    record["updated_at"] = now_iso()
    return new


def archive_prompt(records: list, prompt_id: str) -> dict:
    record = next((x for x in records if x.get("id") == prompt_id), None)
    if not record:
        raise ValueError("البرومبت المطلوب غير موجود")
    record["status"] = "archived"
    record["archived_at"] = now_iso()
    return record


def restore_prompt(records: list, prompt_id: str) -> dict:
    record = next((x for x in records if x.get("id") == prompt_id), None)
    if not record:
        raise ValueError("البرومبت المطلوب غير موجود")
    record["status"] = "active"
    record.pop("archived_at", None)
    record["updated_at"] = now_iso()
    return record


def rollback_as_new_version(records: list, prompt_id: str, version_number: int, note: str = "استعادة إصدار سابق") -> dict:
    record = next((x for x in records if x.get("id") == prompt_id), None)
    if not record:
        raise ValueError("البرومبت المطلوب غير موجود")
    old = next((v for v in record.get("versions", []) if int(v.get("version", 0)) == int(version_number)), None)
    if not old:
        raise ValueError("الإصدار المطلوب غير موجود")
    return save_version(records, prompt_id, old.get("body", ""), note)


def current_version(record: dict) -> dict | None:
    return next((v for v in record.get("versions", []) if int(v.get("version", 0)) == int(record.get("current_version", 0))), None)


def active_prompts(records: list) -> list:
    return sorted([x for x in records if x.get("status", "active") == "active"], key=lambda x: x.get("name", "").casefold())


# ---- Prompt Workbench Pro extensions (Phase 8.13) ----
VARIABLES = {
    "case_title": "اسم القضية", "date_from": "بداية الفترة", "date_to": "نهاية الفترة",
    "parties": "الأطراف", "threads": "الخيوط", "sources": "المصادر المفضلة",
    "output_type": "نوع المخرج", "dialect": "اللهجة", "duration": "مدة المحتوى",
    "audience": "الجمهور المستهدف", "research_question": "سؤال البحث", "extra_instructions": "تعليمات إضافية",
}
CHAIN_STAGES = [
    ("extract", "جمع واستخراج المعلومات", "استخرج الوقائع والتواريخ والأرقام والتصريحات والجهات من المواد. أنشئ جدولاً لكل معلومة مع رابطها ومصدرها وتاريخها. افصل الواقعة عن الادعاء والتحليل، ولا تستنتج ما لا تقوله المادة."),
    ("verify", "التحقق ومقارنة المصادر", "اختبر كل ادعاء مقابل المصادر المتاحة. حدد التأييد والتعارض والاستقلالية المحتملة للمصادر، ومصدر الخبر الأصلي، والفجوات. لا تعتبر تكرار الوكالة الواحدة تأكيداً مستقلاً. أعط درجة ثقة مبررة." + "\n" + prompt_style.source_block()),
    ("connect", "ربط الأحداث والخيوط", "اربط الأحداث زمنياً وموضوعياً، وحدد نقاط التحول والجهات والمصالح والروابط المحتملة. ميّز الارتباط عن السببية، واذكر التفسيرات البديلة."),
    ("geopolitical", "التحليل الجيوسياسي", "حلل أهداف الأطراف وقدراتها وقيودها وأوراق الضغط والسيناريوهات. افصل الحقائق عن الاستنتاجات والاحتمالات، واذكر مؤشرات يمكن مراقبتها لتأكيد أو نفي كل سيناريو."),
    ("script", "السكريبت باللهجة المصرية", "اكتب سكريبتاً باللهجة المصرية المبسطة، بخطاف قوي غير مضلل وتسلسل مفهوم وجمل صالحة للإلقاء. لا تضف حقائق غير موجودة في التحليل، واحتفظ بالتحفظات الضرورية.\n" + prompt_style.CAIRO_STYLE),
    ("production", "خطة إنتاج المحتوى", "حوّل السكريبت إلى خطة إنتاج: تقسيم المشاهد، النص الصوتي، الصورة المقترحة، النص على الشاشة، المؤثرات والانتقالات، وملاحظات المونتاج. لا تقترح صوراً توحي بوقائع غير مثبتة."),
]


def now_iso(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _id(prefix): return prefix + uuid.uuid4().hex[:14]
def _hash(text): return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def render_template(template: str, values: dict, strict: bool = False) -> dict:
    """Replace {{variable}} placeholders; report missing and unknown keys without guessing."""
    used = []
    def sub(match):
        key = match.group(1).strip()
        used.append(key)
        value = values.get(key)
        return str(value).strip() if value is not None and str(value).strip() else match.group(0)
    rendered = re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", sub, str(template or ""))
    unknown = sorted({k for k in used if k not in VARIABLES})
    missing = sorted({k for k in used if k in VARIABLES and (k not in values or values.get(k) is None or not str(values.get(k)).strip())})
    if strict and missing:
        raise ValueError("متغيرات مطلوبة لم يتم ملؤها: " + ", ".join(missing))
    return {"text": rendered, "used": sorted(set(used)), "missing": missing, "unknown": unknown}


def create_bundle(cases: list, case_ids: list, title: str = "حزمة بحثية موحدة") -> dict:
    """Snapshot selected cases, deduplicate materials, retain every source-to-case provenance edge."""
    selected = [c for c in cases if c.get("id") in set(case_ids)]
    if not selected: raise ValueError("اختر ملفاً بحثياً واحداً على الأقل")
    materials, index = [], {}
    for case in selected:
        for pos, item in enumerate(case.get("materials", []), 1):
            url = str(item.get("url") or item.get("link") or "").strip()
            fingerprint = "url:" + url.casefold() if url else "text:" + _hash((item.get("title", "") + "\n" + item.get("text", "")).strip())
            if fingerprint not in index:
                rec = dict(item)
                rec["bundle_material_id"] = _id("bm_")
                rec["provenance"] = []
                index[fingerprint] = rec
                materials.append(rec)
            index[fingerprint]["provenance"].append({"case_id": case.get("id"), "case_title": case.get("title", ""), "item_position": pos, "source_url": url})
    claims, events = [], []
    for case in selected:
        for claim in case.get("claims", []):
            claims.append({"case_id": case.get("id"), "case_title": case.get("title", ""), "record": dict(claim)})
        for event in case.get("events", []):
            events.append({"case_id": case.get("id"), "case_title": case.get("title", ""), "record": dict(event)})
    bundle = {"id": _id("pb_"), "title": str(title or "حزمة بحثية موحدة").strip(), "created_at": now_iso(),
        "case_ids": [c.get("id") for c in selected], "cases": [{"id": c.get("id"), "title": c.get("title", ""), "description": c.get("description", "")} for c in selected],
        "materials": materials, "claims": claims, "events": events,
        "material_count": len(materials), "source_case_count": len(selected), "deduplicated_count": sum(max(0, len(x["provenance"])-1) for x in materials)}
    bundle["sha256"] = _hash(json.dumps(bundle, ensure_ascii=False, sort_keys=True))
    return bundle


def render_bundle(bundle: dict) -> str:
    lines = [f"# {bundle.get('title')}", f"تاريخ اللقطة: {bundle.get('created_at')}", f"عدد الملفات: {bundle.get('source_case_count')} | المواد بعد إزالة التكرار: {bundle.get('material_count')}", "", "## الملفات المشمولة"]
    lines += [f"- {c.get('title')} (ID: {c.get('id')})" for c in bundle.get("cases", [])]
    lines += ["", "## المواد والمصادر"]
    for i, m in enumerate(bundle.get("materials", []), 1):
        lines += [f"### {i}. {m.get('title') or 'مادة بلا عنوان'}", f"- الرابط: {m.get('url') or m.get('link') or 'غير متاح'}", f"- المصدر: {m.get('outlet') or m.get('domain') or 'غير محدد'}", f"- التاريخ: {m.get('date') or 'غير محدد'}", f"- واردة من: {', '.join(x.get('case_title','') for x in m.get('provenance', []))}", str(m.get('text') or '')[:12000], ""]
    lines += ["## الادعاءات المسجلة"]
    for x in bundle.get("claims", []): lines.append(f"- [{x['case_title']}] {x['record'].get('statement','')} | النوع: {x['record'].get('type','')} | الحالة: {x['record'].get('status','')} | المصدر: {x['record'].get('source','')}")
    lines += ["", "## الأحداث المسجلة"]
    for x in bundle.get("events", []): lines.append(f"- [{x['case_title']}] {x['record'].get('date','')} | {x['record'].get('title','')} | {x['record'].get('detail','')} | {x['record'].get('source','')}")
    lines += ["", "## قواعد التعامل مع الحزمة", "هذه لقطة بحثية وليست تحققاً مستقلاً. حافظ على رابط كل معلومة بمصدرها وملفها الأصلي. لا تخلط الادعاء بالواقعة، ولا تستنتج السببية من التزامن."]
    return "\n".join(lines)


def new_chain(title: str, bundle: dict, variables: dict | None = None) -> dict:
    if not bundle or not bundle.get("id"): raise ValueError("لازم تختار حزمة بحثية محفوظة أولاً")
    return {"id": _id("pc_"), "title": str(title or "سلسلة بحثية").strip() or "سلسلة بحثية", "bundle_id": bundle["id"],
        "bundle_title": bundle.get("title", ""), "bundle_sha256": bundle.get("sha256", ""), "variables": dict(variables or {}),
        "stages": [{"key": key, "title": label, "instruction": instruction, "status": "pending", "output": "", "updated_at": ""} for key, label, instruction in CHAIN_STAGES],
        "created_at": now_iso(), "updated_at": now_iso(), "approval": {"status": "pending", "approved_at": "", "final_output": ""}}


def chain_stage_prompt(chain: dict, stage_index: int, bundle_text: str) -> dict:
    stages = chain.get("stages", [])
    if stage_index < 0 or stage_index >= len(stages): raise ValueError("مرحلة غير موجودة")
    prior = [s for s in stages[:stage_index] if s.get("status") == "completed" and s.get("output", "").strip()]
    missing_prior = [s.get("title") for s in stages[:stage_index] if s.get("status") != "completed"]
    stage = stages[stage_index]
    var_result = render_template(stage.get("instruction", ""), chain.get("variables", {}))
    prompt = "أنت تعمل ضمن سلسلة بحثية متعددة المراحل. التزم بالأدلة وحدودها ولا تخترع مصادر.\n\n"
    prompt += f"## المهمة الحالية: {stage.get('title')}\n{var_result['text']}\n\n"
    prompt += "## الحزمة البحثية ومصادرها\n" + str(bundle_text or "") + "\n\n"
    if prior:
        prompt += "## مخرجات المراحل السابقة المعتمدة كمدخلات عمل\n"
        for p in prior: prompt += f"### {p.get('title')}\n{p.get('output')}\n\n"
    if missing_prior:
        prompt += "## تنبيه تسلسل\nالمراحل السابقة التالية لم تُسجل كمكتملة، لا تفترض نتائجها: " + "، ".join(missing_prior) + "\n\n"
    prompt += "## شكل التسليم\nاكتب نتيجة منظمة قابلة للمراجعة، وميّز الوقائع والادعاءات والاستنتاجات والسيناريوهات. أرفق مرجع المادة أو رابطها كلما أمكن، وصرّح بالفجوات وعدم اليقين."
    return {"prompt": prompt, "stage": stage, "missing_prior": missing_prior, "prior_count": len(prior)}


def save_stage_output(chain: dict, stage_index: int, output: str, mark_complete: bool = True) -> dict:
    stages = chain.get("stages", [])
    if stage_index < 0 or stage_index >= len(stages): raise ValueError("مرحلة غير موجودة")
    text = str(output or "").strip()
    if not text: raise ValueError("لا يمكن حفظ مخرج فارغ")
    stage = stages[stage_index]
    stage["output"] = text
    stage["status"] = "completed" if mark_complete else "draft"
    stage["updated_at"] = now_iso()
    chain["updated_at"] = now_iso()
    chain["approval"] = {"status": "pending", "approved_at": "", "final_output": ""}
    return stage


def compare_outputs(outputs: list[dict]) -> str:
    if len(outputs) < 2: raise ValueError("أضف نتيجتين على الأقل للمقارنة")
    lines = ["# مقارنة مخرجات المراجعة", "قارن دون افتراض أن الأكثر تفصيلاً هو الأدق."]
    for i, item in enumerate(outputs, 1):
        lines += [f"## النسخة {i}: {item.get('label') or 'نتيجة'}", str(item.get("text") or "")]
    lines += ["## المطلوب", "استخرج نقاط الاتفاق والاختلاف، والادعاءات التي تحتاج تحققاً، والفجوات، وأسباب اختلاف النتائج. لا تدمج روايتين متعارضتين دون بيان التعارض."]
    return "\n\n".join(lines)


def approve_chain(chain: dict, final_output: str) -> dict:
    final_output = str(final_output or "").strip()
    if not final_output: raise ValueError("اكتب أو الصق المخرج النهائي قبل اعتماده")
    incomplete = [x.get("title") for x in chain.get("stages", []) if x.get("status") != "completed"]
    if incomplete: raise ValueError("لا يمكن اعتماد السلسلة قبل إكمال المراحل: " + "، ".join(incomplete))
    chain["approval"] = {"status": "approved", "approved_at": now_iso(), "final_output": final_output, "sha256": _hash(final_output)}
    chain["updated_at"] = now_iso()
    return chain["approval"]

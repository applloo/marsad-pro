# -*- coding: utf-8 -*-
"""Manual-first Egyptian Arabic video production prompts and versioned artifacts."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4

import prompt_style

DEFAULTS = {
    "video_type": "analysis", "duration_minutes": 10, "tone": "sharp",
    "scene_plan_enabled": True, "short_clips_enabled": True,
}
VIDEO_TYPES = {
    "analysis": "تحليل سياسي", "breaking": "تطور عاجل", "story": "حكاية/قصة",
    "documentary": "وثائقي", "explainer": "شرح مبسط",
}
TONES = {"sharp": "حاد وساخر بذكاء", "calm": "هادئ ومتزن", "dramatic": "درامي مشوق", "documentary": "وثائقي رصين"}
DURATIONS = (3, 5, 8, 10, 12, 15, 20)
MAX_DOSSIER = 100000
MAX_ARTIFACT = 60000


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_settings(settings=None):
    data = {**DEFAULTS, **(settings or {})}
    if data["video_type"] not in VIDEO_TYPES:
        raise ValueError("نوع الفيديو غير صالح")
    data["duration_minutes"] = int(data["duration_minutes"])
    if data["duration_minutes"] not in DURATIONS:
        raise ValueError("مدة الفيديو غير مدعومة")
    if data["tone"] not in TONES:
        raise ValueError("أسلوب التقديم غير صالح")
    data["scene_plan_enabled"] = bool(data["scene_plan_enabled"])
    data["short_clips_enabled"] = bool(data["short_clips_enabled"])
    return data


def create_project(case_id, case_title, dossier, settings=None, *, dossier_id="", now=None):
    if not str(case_id or "").strip():
        raise ValueError("معرّف القضية مطلوب")
    if not str(dossier or "").strip():
        raise ValueError("لازم تضيف ملف التحليل النهائي الأول")
    cfg = validate_settings(settings)
    stamp = now or _now()
    return {"id": str(uuid4()), "case_id": str(case_id), "case_title": str(case_title or "")[:300],
            "dossier_id": str(dossier_id or ""), "settings": cfg,
            "created_at": stamp, "updated_at": stamp, "state": "prompt_ready",
            "dossier": str(dossier)[:MAX_DOSSIER], "artifacts": [], "events": [
                {"at": stamp, "message": "إنشاء مشروع إنتاج فيديو من ملف بحث محفوظ"}]}


def _context(project):
    cfg = validate_settings(project.get("settings"))
    return (f"القضية: {project.get('case_title') or 'غير محدد'}\n"
            f"نوع الفيديو: {VIDEO_TYPES[cfg['video_type']]}\n"
            f"المدة: {cfg['duration_minutes']} دقائق\n"
            f"أسلوب التقديم: {TONES[cfg['tone']]}\n"
            f"معرّف ملف التحليل: {project.get('dossier_id') or 'غير محدد'}")


def reading_prompt(project):
    return ("أنت محرر تحقيقات ومحلل سياسي. اقرأ ملف البحث التالي قبل كتابة السكريبت.\n"
            "أخرج ورقة قراءة من: السؤال المركزي، أطروحتين متنافستين، أقوى 5 أدلة مع معرّفات مصادرها، ما ينقض كل أطروحة، التسلسل الزمني، ما نعرفه وما لا نعرفه، أثر محتمل على مصر، وثلاث زوايا سردية.\n"
            "لا تخترع مصادر أو وقائع. افصل بوضوح بين الواقعة والادعاء المنسوب والاستنتاج والتوقع. احتفظ بمعرّفات المصادر حرفياً. لا تعتبر تكرار الخبر استقلالاً في التأكيد. إذا كانت المادة مقتطفات فقط فاذكر ذلك.\n\n"
            + prompt_style.source_block() + "\n" + prompt_style.WEB_RESEARCH + "\n\n"
            f"## إعدادات المشروع\n{_context(project)}\n\n## ملف البحث\n{project.get('dossier','')}")


def script_prompt(project, reading_sheet="", revision_note=""):
    cfg = validate_settings(project.get("settings"))
    words = cfg["duration_minutes"] * 130
    parts = [
        "أنت كاتب ومعدّ فيديوهات سياسية لجمهور مصري. اكتب سكريبتاً قابلاً للإلقاء، لا نشرة أخبار ولا تقريراً أكاديمياً.",
        f"الإعدادات: {_context(project)}. استهدف قرابة {words} كلمة مع مرونة طبيعية في الإلقاء.",
        "اللهجة قاهرية مصرية طبيعية ومفهومة. الأسلوب حاد وذكي من غير شتائم أو تهويل فارغ. استخدم جُملاً قصيرة وانتقالات وأسئلة تشد الانتباه كل 30 إلى 40 ثانية. تجنب التراكيب الثقيلة المليئة بحرف السين قدر الإمكان.",
        prompt_style.CAIRO_STYLE,
        "لو ورقة القراءة فيها فحص للجرايد والكتّاب، استخدمه: قول للمتابع لو المصدر مقال رأي أو ليه خط معروف، وماتتبناش وصف الجريدة كأنه واقعة. " + prompt_style.AR_NAMES_RULE,
        "البناء: افتتاحية بخطاف قوي؛ تمهيد يشرح لماذا الموضوع مهم الآن؛ عرض الأدلة والروايات؛ تحليل ما وراء الحدث؛ تفسير بديل جاد؛ ما الذي قد يحدث تالياً؛ الانعكاس على مصر؛ خاتمة بسؤال يفتح النقاش.",
        "لا تخلط الحقيقة بالاستنتاج أو التوقع. ضع [معرّف المصدر] بعد المعلومة المدعومة. لا تضف أرقاماً أو اقتباسات أو أسماء غير موجودة في الملف. اذكر نقاط عدم اليقين بوضوح. لا تقل إنك تحققت من رابط لم يُفتح فعلياً.",
        "قسّم السكريبت إلى مقاطع بتوقيت تقريبي وعنوان لكل مقطع. اجعل النص المنطوق منفصلاً عن ملاحظات المقدم.",
    ]
    if cfg["scene_plan_enabled"]:
        parts.append("أضف خطة مشاهد كاملة في جدول: التوقيت، الكلام المنطوق، الصورة/الفيديو المقترح، النص على الشاشة، المؤثرات والصوت، ومصدر اللقطة أو طريقة إنتاجها. اقترح خرائط وخطوط زمنية ورسوم بيانات وأرشيفاً عند الحاجة. ضع علامة واضحة على أي مشهد مولد بالذكاء الاصطناعي أو تمثيلي، ولا تقدمه على أنه تصوير حقيقي لحدث.")
    if cfg["short_clips_enabled"]:
        parts.append("أضف 3 مقاطع قصيرة مستقلة لـShorts/Reels، كل واحد بخطاف ونص منطوق وخاتمة، مع توقيت مقترح من الفيديو الطويل وعنوان قصير ونص غلاف.")
    parts.append("اختم بثلاثة عناوين جذابة غير مضللة، وثلاث عبارات للغلاف، ووصف للنشر، وكلمات مفتاحية، وتعليق مثبت، وقائمة المصادر المستخدمة ومعرّفاتها، ونقاط تحتاج تحققاً إضافياً. افصل المخرجات بعناوين واضحة ومستقلة: SCRIPT وPRODUCTION_PLAN وSHORT_CLIPS وPUBLISHING_KIT وSOURCES_AND_UNKNOWNS، حتى يمكن حفظ كل مخرج منفرداً.")
    if revision_note:
        parts.append("ملاحظة إعادة الكتابة: " + str(revision_note)[:3000] + ". أعد كتابة السكريبت فقط مع الحفاظ على ملف البحث ومعرّفات المصادر. لا تطلب إعادة البحث أو التحليل.")
    if reading_sheet:
        parts.append("## ورقة القراءة التحليلية\n" + str(reading_sheet)[:MAX_ARTIFACT])
    parts.append("## ملف البحث الأصلي\n" + project.get("dossier", ""))
    return "\n\n".join(parts)


def revision_prompt(project, existing_script, note):
    if not str(existing_script or "").strip():
        raise ValueError("لا يوجد سكريبت محفوظ لإعادة كتابته")
    return ("أعد تحرير السكريبت التالي وفق الملاحظة، من غير إعادة البحث أو تغيير الوقائع. حافظ على كل معرّفات المصادر، وميّز الوقائع عن التحليل والتوقع. أخرج النسخة الكاملة المعدلة فقط، ثم ملخصاً قصيراً للتغييرات.\n"
            f"إعدادات المشروع: {_context(project)}\nملاحظة التعديل: {str(note or '').strip()[:3000]}\n\n"
            f"ملف البحث المرجعي:\n{project.get('dossier','')}\n\nالسكريبت الحالي:\n{str(existing_script)[:MAX_ARTIFACT]}")


def save_artifact(project, kind, content, *, title="", now=None):
    allowed = {"reading_sheet", "script", "production_plan", "short_clips", "publishing_kit", "combined"}
    if kind not in allowed:
        raise ValueError("نوع المخرج غير صالح")
    value = str(content or "").strip()
    if not value:
        raise ValueError("لا يمكن حفظ مخرج فارغ")
    stamp = now or _now()
    rows = project.setdefault("artifacts", [])
    version = 1 + max((int(x.get("version", 0)) for x in rows if x.get("kind") == kind), default=0)
    row = {"id": str(uuid4()), "kind": kind, "title": str(title or kind)[:200],
           "version": version, "content": value[:MAX_ARTIFACT], "created_at": stamp}
    rows.append(row)
    project["updated_at"] = stamp
    project["state"] = "has_outputs"
    project.setdefault("events", []).append({"at": stamp, "message": f"حفظ {kind} إصدار {version}"})
    project["events"] = project["events"][-100:]
    return row


def latest_artifact(project, kind):
    rows = [x for x in project.get("artifacts", []) if x.get("kind") == kind]
    return max(rows, key=lambda x: int(x.get("version", 0))) if rows else None


def summary(project):
    kinds = {}
    for row in project.get("artifacts", []):
        kinds[row.get("kind", "unknown")] = max(kinds.get(row.get("kind", "unknown"), 0), int(row.get("version", 0)))
    return {"artifacts": len(project.get("artifacts", [])), "latest_versions": kinds,
            "updated_at": project.get("updated_at", "")}

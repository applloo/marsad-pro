# -*- coding: utf-8 -*-
"""تجميع مخرجات استوديو المرصد في حزمة إنتاج قابلة للنقل."""
from __future__ import annotations
import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone


def _clean_name(value: str, fallback: str = "marsad_production") -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value[:64] or fallback


def _section(text: str, headings: tuple[str, ...]) -> str:
    lines = (text or "").splitlines()
    start = level = None
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("#"):
            continue
        title = line.lstrip("# ").strip().lower()
        if any(h.lower() in title for h in headings):
            start, level = i, len(line) - len(line.lstrip("#"))
            break
    if start is None:
        return ""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.lstrip().startswith("#") and len(line) - len(line.lstrip("#")) <= level:
            end = i
            break
    return "\n".join(lines[start:end]).strip()


def _csv_template() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["asset_id", "suggested_filename", "asset_type", "description", "source_or_search_terms", "status", "verification_note"])
    writer.writerow(["AST001", "replace_with_asset_name", "archive_or_original_or_graphic_or_ai", "اكتب وصف الأصل المطلوب", "أضف رابط المصدر أو كلمات البحث", "needs_sourcing", "تحقق من المصدر والترخيص قبل النشر"])
    return output.getvalue()


def _edl_template() -> str:
    return (
        "track\tstart\tend\tasset_id\tshot_id\taction\taudio_note\n"
        "V1\t00:00:00.000\t00:00:05.000\tAST001\tSHOT001\tضع اللقطة الأساسية هنا\tراجع التوقيت بعد تسجيل التعليق\n"
        "V2\t00:00:00.000\t00:00:05.000\tGFX001\tSHOT001\tعنوان أو خريطة توضيحية\tلا تضع نصاً داخل الصورة المولدة\n"
        "A1\t00:00:00.000\t00:00:05.000\tVO001\tSHOT001\tتعليق صوتي\tاستبدل بالتسجيل النهائي\n"
        "A2\t00:00:00.000\t00:00:05.000\tMUS001\tSHOT001\tموسيقى خلفية مرخصة\tاضبط المستوى أسفل التعليق\n"
        "A3\t00:00:00.000\t00:00:05.000\tSFX001\tSHOT001\tمؤثر صوتي عند الحاجة\tتجنب المؤثرات المضللة\n"
    )


def build_production_bundle(job: dict, result: dict, generated_images: list | None = None) -> bytes:
    """Create a portable ZIP; no claim is made that media assets already exist."""
    generated = (result or {}).get("text", "")
    if not generated.strip():
        raise ValueError("لا توجد مخرجات إنتاج محفوظة لإنشاء الحزمة")
    title = job.get("case_title") or "قضية المرصد"
    job_id = _clean_name(job.get("id", "job"))
    generated_images = generated_images or []
    metadata = {
        "project": "مرصد الأخبار", "case_title": title, "case_id": job.get("case_id"),
        "job_id": job.get("id"), "analysis_result_id": job.get("result_id"),
        "provider": result.get("provider"), "model": result.get("model"),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "media_assets_included": bool(generated_images),
        "generated_image_count": len(generated_images),
        "note": ("تتضمن الصور المولدة المدرجة في هذه الحزمة." if generated_images else "حزمة تنظيم وإنتاج بلا صور مولدة مرفقة."),
    }
    readme = f"""# حزمة إنتاج مرصد الأخبار\n\n- القضية: {title}\n- نوع الإنتاج: {job.get('output_type', '')}\n- المنصة: {job.get('platform', '')}\n- اللهجة: {job.get('dialect', '')}\n- المدة: {job.get('duration', '')}\n- النموذج: {result.get('provider', '')} / {result.get('model', '')}\n\n## المحتويات\n- `01_content_full.md`: كامل النص المنتج.\n- `02_storyboard.md`: لوحة المشاهد إن وُجدت.\n- `03_visual_prompts.md`: البرومبتات البصرية إن وُجدت.\n- `04_asset_manifest.csv`: سجل الأصول المطلوب جمعها والتحقق منها.\n- `05_edit_decision_list.tsv`: قالب جدول المونتاج متعدد المسارات.\n- `06_production_job.json`: بيانات التكليف والمصدر والنموذج.\n- `07_quality_checklist.md`: قائمة التحقق قبل النشر.\n- `08_generated_images/`: الصور التي تم توليدها في جلسة العمل الحالية، إن وجدت.\n- `09_generated_images_manifest.json`: بيانات المشاهد والنماذج والبرومبتات للصور المرفقة.\n\n**تنبيه:** الحزمة لا تنشئ فيديوهات. الصور المولدة المرفقة هي الملفات الفعلية الموجودة في جلسة العمل وقت التنزيل. التوقيتات في قالب EDL تجريبية ويجب ضبطها بعد تسجيل التعليق الصوتي.\n"""
    storyboard = _section(generated, ("storyboard", "لوحة المشاهد", "خريطة المشاهد", "خريطة الربط"))
    prompts = _section(generated, ("برومبتات", "prompts", "الوصف البصري", "البرومبت البصري"))
    quality = """# قائمة مراجعة الإنتاج\n\n- [ ] مراجعة كل معلومة مقابل التحليل والمصادر.\n- [ ] تمييز الأرشيف الحقيقي عن التصور التوضيحي المولد.\n- [ ] التحقق من حقوق استخدام الصور والفيديو والموسيقى.\n- [ ] التأكد من ربط كل وحدة إلقاء بمشهد أو ظهور للمقدم.\n- [ ] مراجعة التوقيتات بعد تسجيل التعليق الصوتي.\n- [ ] مراجعة النصوص العربية والأسماء والأرقام على الشاشة.\n- [ ] عدم استخدام صورة مولدة كدليل على واقعة حقيقية.\n- [ ] مراجعة الصوت والترجمة ونسبة الأبعاد قبل التصدير.\n"""
    files = {
        "README.md": readme,
        "01_content_full.md": generated,
        "02_storyboard.md": storyboard or "# لوحة المشاهد\n\nلم يتم العثور على قسم مستقل. راجع الملف الكامل.\n",
        "03_visual_prompts.md": prompts or "# البرومبتات البصرية\n\nلم يتم العثور على قسم مستقل. راجع الملف الكامل.\n",
        "04_asset_manifest.csv": _csv_template(),
        "05_edit_decision_list.tsv": _edl_template(),
        "06_production_job.json": json.dumps({"job": job, "result": metadata}, ensure_ascii=False, indent=2),
        "07_quality_checklist.md": quality,
        "09_generated_images_manifest.json": json.dumps([
            {k: v for k, v in image.items() if k != "image_bytes"} for image in generated_images
        ], ensure_ascii=False, indent=2),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
        for name, content in files.items():
            archive.writestr(f"{job_id}/{name}", content.encode("utf-8"))
        for image in generated_images:
            raw_name = str(image.get("filename", "scene.png"))
            suffix = ".png" if raw_name.lower().endswith(".png") else ".jpg" if raw_name.lower().endswith((".jpg", ".jpeg")) else ".webp" if raw_name.lower().endswith(".webp") else ".bin"
            stem = _clean_name(raw_name.rsplit(".", 1)[0], "scene")
            archive.writestr(f"{job_id}/08_generated_images/{stem}{suffix}", image["image_bytes"])
    return buffer.getvalue()

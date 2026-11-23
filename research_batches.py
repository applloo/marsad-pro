# -*- coding: utf-8 -*-
"""Resumable, provenance-preserving research batches for manual or approved AI workflows."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
import hashlib
import json

MAX_ITEMS_PER_BATCH = 12
MAX_TEXT_PER_ITEM = 5000
MAX_OUTPUT_CHARS = 30000


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_text(value, limit=MAX_TEXT_PER_ITEM):
    return str(value or "").strip()[:limit]


def _source_record(item, index):
    url = str(item.get("url") or item.get("link") or "").strip()
    title = _clean_text(item.get("title_ar") or item.get("title") or "بدون عنوان", 500)
    domain = _clean_text(item.get("domain") or item.get("source") or item.get("outlet") or "مصدر غير محدد", 200)
    date = _clean_text(item.get("seendate") or item.get("date") or item.get("published_at") or "", 80)
    raw_text = item.get("text") or item.get("content") or item.get("body") or item.get("description") or item.get("snippet") or item.get("summary") or ""
    text = _clean_text(raw_text)
    identity = url or f"{title}|{domain}|{date}|{index}"
    sid = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return {
        "source_id": sid, "title": title,
        "original_title": _clean_text(item.get("title") or title, 500),
        "domain": domain, "date": date, "url": url,
        "text": text, "text_truncated": len(str(raw_text or "")) > len(text),
        "text_characters": len(str(raw_text or "")),
        "language": _clean_text(item.get("language") or "", 30),
        "publisher": _clean_text(item.get("publisher") or item.get("writer") or "", 200),
    }


def prepare_materials(items):
    seen, records = set(), []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        row = _source_record(item, index)
        key = row["url"].split("?")[0].rstrip("/") if row["url"] else row["source_id"]
        if key in seen:
            continue
        seen.add(key)
        records.append(row)
    return records


def create_batch(title, items, *, batch_size=8, instructions="", now=None):
    if not str(title or "").strip():
        raise ValueError("اسم البحث مطلوب")
    size = int(batch_size)
    if size < 1 or size > MAX_ITEMS_PER_BATCH:
        raise ValueError(f"حجم الدفعة يجب أن يكون بين 1 و{MAX_ITEMS_PER_BATCH}")
    materials = prepare_materials(items)
    if not materials:
        raise ValueError("لا توجد مواد صالحة للتجميع")
    stamp = now or _now()
    chunks = []
    for offset in range(0, len(materials), size):
        group = materials[offset:offset + size]
        chunks.append({
            "id": str(uuid4()), "index": len(chunks) + 1,
            "source_ids": [x["source_id"] for x in group],
            "materials": group, "state": "pending",
            "created_at": stamp, "updated_at": stamp,
            "output": "", "error": "",
        })
    return {
        "id": str(uuid4()), "title": str(title).strip()[:200],
        "instructions": str(instructions or "").strip()[:3000],
        "created_at": stamp, "updated_at": stamp,
        "state": "prepared", "material_count": len(materials),
        "source_count": len({x["domain"] for x in materials}),
        "batch_size": size, "chunks": chunks,
        "manifest": [{"source_id": x["source_id"], "title": x["title"],
                      "domain": x["domain"], "date": x["date"], "url": x["url"]}
                     for x in materials],
        "merge_output": "", "merge_state": "pending",
        "events": [{"at": stamp, "message": f"تجهيز {len(materials)} مادة في {len(chunks)} دفعة"}],
    }


def chunk_prompt(batch, chunk):
    rows = []
    for item in chunk.get("materials", []):
        rows.append(
            f"### مصدر [{item['source_id']}]\n"
            f"- العنوان: {item['title']}\n"
            f"- العنوان الأصلي: {item['original_title']}\n"
            f"- الناشر/النطاق: {item['domain']}\n"
            f"- التاريخ المنشور: {item['date'] or 'غير متاح'}\n"
            f"- الرابط: {item['url'] or 'غير متاح'}\n"
            f"- النص/المقتطف: {item['text'] or 'لم يُرفق نص المقال'}\n"
            f"- هل اقتُطع النص؟: {'نعم' if item['text_truncated'] else 'لا'}"
        )
    return (
        f"# مهمة تحليل دفعة {chunk.get('index')} من بحث: {batch.get('title')}\n\n"
        "أنت محلل بحثي. حلّل المواد المرفقة فقط، ولا تدّعِ أنك فتحت الروابط أو قرأت نصوصاً غير مرفقة. "
        "احتفظ بمعرّف كل مصدر كما هو بين الأقواس المربعة.\n\n"
        "## المطلوب\n"
        "1. استخرج الوقائع والادعاءات المنسوبة كلٌ على حدة.\n"
        "2. اربط كل نقطة بمعرّف المصدر الداعم، ولا تنشئ استشهاداً غير موجود.\n"
        "3. سجّل التواريخ كما وردت، وميّز تاريخ النشر عن تاريخ الحدث.\n"
        "4. أبرز الاتفاق والتعارض والفجوات والمعلومات غير المتاحة.\n"
        "5. لا تعتبر إعادة نشر الخبر تأكيداً مستقلاً، ولا تستنتج السببية من التشابه الزمني.\n"
        "6. صنّف ما توصلت إليه: واقعة موثقة داخل المادة، ادعاء منسوب، تحليل، أو احتمال.\n"
        "7. اختم بملخص موجز وبقائمة مصادر مستخدمة بمعرّفاتها وروابطها.\n\n"
        f"## تعليمات الباحث\n{batch.get('instructions') or 'لا توجد تعليمات إضافية.'}\n\n"
        f"## مواد الدفعة ({len(rows)})\n\n" + "\n\n".join(rows)
    )


def set_chunk_output(batch, chunk_id, output, *, state="completed", error=""):
    if state not in {"completed", "failed", "pending"}:
        raise ValueError("حالة الدفعة غير صالحة")
    if state == "completed" and not str(output or "").strip():
        raise ValueError("لا يمكن اعتماد دفعة مكتملة بدون نتيجة تحليل")
    chunk = next((x for x in batch.get("chunks", []) if x.get("id") == chunk_id), None)
    if not chunk:
        raise KeyError("الدفعة غير موجودة")
    chunk["output"] = _clean_text(output, MAX_OUTPUT_CHARS)
    chunk["error"] = _clean_text(error, 2000)
    chunk["state"] = state
    chunk["updated_at"] = _now()
    batch["updated_at"] = chunk["updated_at"]
    done = sum(1 for x in batch["chunks"] if x.get("state") == "completed")
    failed = sum(1 for x in batch["chunks"] if x.get("state") == "failed")
    if done == len(batch["chunks"]):
        batch["state"] = "ready_to_merge"
    elif failed:
        batch["state"] = "needs_attention"
    elif done:
        batch["state"] = "in_progress"
    else:
        batch["state"] = "prepared"
    batch.setdefault("events", []).append({
        "at": batch["updated_at"],
        "message": f"تحديث الدفعة {chunk.get('index')}: {chunk['state']}"
    })
    batch["events"] = batch["events"][-100:]
    return batch


def retry_chunk(batch, chunk_id):
    chunk = next((x for x in batch.get("chunks", []) if x.get("id") == chunk_id), None)
    if not chunk:
        raise KeyError("الدفعة غير موجودة")
    if chunk.get("state") not in {"failed", "pending"}:
        raise ValueError("يمكن إعادة تجهيز الدفعة الفاشلة أو المنتظرة فقط")
    chunk["state"] = "pending"
    chunk["error"] = ""
    chunk["output"] = ""
    chunk["updated_at"] = _now()
    batch["state"] = "in_progress" if any(x.get("state") == "completed" for x in batch["chunks"]) else "prepared"
    batch["updated_at"] = chunk["updated_at"]
    return batch


def merge_prompt(batch):
    completed = [x for x in batch.get("chunks", []) if x.get("state") == "completed" and x.get("output")]
    if not completed:
        raise ValueError("لا توجد دفعات مكتملة لدمجها")
    expected = len(batch.get("chunks", []))
    if len(completed) != expected:
        missing = [str(x.get("index")) for x in batch["chunks"] if x.get("state") != "completed"]
        raise ValueError("لا يمكن إعداد الدمج النهائي قبل اكتمال الدفعات. المتبقي: " + "، ".join(missing))
    sections = []
    for chunk in completed:
        sections.append(f"## نتيجة الدفعة {chunk['index']} | المصادر: {', '.join(chunk.get('source_ids', []))}\n{chunk['output']}")
    manifest = json.dumps(batch.get("manifest", []), ensure_ascii=False, indent=2)
    return (
        f"# دمج البحث الكامل: {batch.get('title')}\n\n"
        "ادمج نتائج الدفعات في تقرير بحثي واحد دون فقد أي معلومة أو مصدر.\n"
        "قواعد إلزامية:\n"
        "- لا تضف وقائع غير موجودة في نتائج الدفعات.\n"
        "- أزل التكرار مع الاحتفاظ بجميع معرفات المصادر ذات الصلة.\n"
        "- افصل الوقائع عن الادعاءات والتحليل والسيناريوهات.\n"
        "- أنشئ خطاً زمنياً، وميّز تاريخ النشر عن تاريخ وقوع الحدث.\n"
        "- اعرض الروايات المتعارضة والأدلة المؤيدة والمعارضة والفجوات.\n"
        "- لا تعدّ المصادر الناقلة عن أصل واحد تأكيدات مستقلة.\n"
        "- اختم بخلاصة تنفيذية، وحدود البحث، وقائمة المصادر والروابط.\n\n"
        "## سجل المصادر الأصلي\n```json\n" + manifest + "\n```\n\n"
        "## نتائج الدفعات\n\n" + "\n\n".join(sections)
    )


def summary(batch):
    chunks = batch.get("chunks", [])
    completed = sum(1 for x in chunks if x.get("state") == "completed")
    failed = sum(1 for x in chunks if x.get("state") == "failed")
    pending = len(chunks) - completed - failed
    return {"materials": batch.get("material_count", 0), "chunks": len(chunks),
            "completed": completed, "failed": failed, "pending": pending,
            "progress_percent": round(completed * 100 / len(chunks)) if chunks else 0,
            "state": batch.get("state", "unknown")}

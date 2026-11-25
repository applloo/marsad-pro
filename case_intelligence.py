# -*- coding: utf-8 -*-
"""ملف القضية الاستخباراتي التراكمي: سجل تغييرات وأدلة قابل للمراجعة دون استدعاء AI."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

import prompt_style


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _json_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_text(value):
    return str(value or "").strip()


def _material_payload(item):
    raw_text = _safe_text(item.get("text"))
    return {
        "title": _safe_text(item.get("title")),
        "type": _safe_text(item.get("type")),
        "author": _safe_text(item.get("author")),
        "outlet": _safe_text(item.get("outlet")),
        "date": _safe_text(item.get("date")),
        "url": _safe_text(item.get("url")),
        "text": raw_text[:3000],
        "text_truncated": len(raw_text) > 3000,
        "original_text_characters": len(raw_text),
        "stance": _safe_text(item.get("stance")),
        "note": _safe_text(item.get("note")),
    }


def _claim_payload(item):
    return {
        "statement": _safe_text(item.get("statement")),
        "type": _safe_text(item.get("type")),
        "status": _safe_text(item.get("status")),
        "source": _safe_text(item.get("source")),
        "note": _safe_text(item.get("note")),
    }


def _event_payload(item):
    return {
        "date": _safe_text(item.get("date")),
        "title": _safe_text(item.get("title")),
        "detail": _safe_text(item.get("detail")),
        "source": _safe_text(item.get("source")),
    }


def _external_case_references(case, dossiers):
    """اربط فقط ملفات التحليل التي تذكر case_id صراحةً، مع الاحتفاظ بمصدر الإحالة."""
    refs = []
    case_id = case.get("id")
    for dossier in dossiers or []:
        matched = False
        for match in dossier.get("prior_case_matches", []) or []:
            for candidate in match.get("matches", []) or []:
                if candidate.get("case_id") == case_id:
                    matched = True
                    refs.append({
                        "dossier_id": dossier.get("id", ""),
                        "dossier_title": dossier.get("title_ar") or dossier.get("title") or "",
                        "article_title": (match.get("article") or {}).get("title", ""),
                        "article_url": (match.get("article") or {}).get("url", ""),
                        "source": (match.get("article") or {}).get("source", ""),
                        "match_score": candidate.get("score", 0),
                        "match_level": candidate.get("level", ""),
                        "basis": "اقتراح ربط سابق محفوظ في المرصد، وليس اعتماداً تلقائياً",
                    })
        if matched:
            continue
        # ملف تحليل قد يحتوي على مواد أو كيانات ذات صلة دون رابط قضية صريح؛ لا نخمن الصلة.
    return refs


def build_snapshot(case, dossiers=()):
    materials = case.get("materials", []) or []
    claims = case.get("claims", []) or []
    events = case.get("events", []) or []
    material_rows = []
    for item in materials:
        item_id = item.get("id") or item.get("key") or _json_hash(_material_payload(item))[:16]
        payload = _material_payload(item)
        material_rows.append({"id": str(item_id), "hash": _json_hash(payload), "payload": payload})
    claim_rows = []
    for item in claims:
        item_id = item.get("id") or _json_hash(_claim_payload(item))[:16]
        payload = _claim_payload(item)
        claim_rows.append({"id": str(item_id), "hash": _json_hash(payload), "payload": payload})
    event_rows = []
    for item in events:
        item_id = item.get("id") or _json_hash(_event_payload(item))[:16]
        payload = _event_payload(item)
        event_rows.append({"id": str(item_id), "hash": _json_hash(payload), "payload": payload})
    core = {
        "title": _safe_text(case.get("title")),
        "description": _safe_text(case.get("description")),
        "tags": sorted(_safe_text(x) for x in (case.get("tags", []) or []) if _safe_text(x)),
        "research_notes": _safe_text(case.get("research_notes")),
        "materials": sorted(material_rows, key=lambda x: x["id"]),
        "claims": sorted(claim_rows, key=lambda x: x["id"]),
        "events": sorted(event_rows, key=lambda x: x["id"]),
        "related_dossier_references": _external_case_references(case, dossiers),
    }
    return {"hash": _json_hash(core), "captured_at": now_iso(), "content": core}


def new_case_file(case):
    stamp = now_iso()
    return {
        "id": f"caseintel_{case.get('id')}",
        "case_id": case.get("id"),
        "title": case.get("title", ""),
        "created_at": stamp,
        "updated_at": stamp,
        "snapshots": [],
        "ledger": {"materials": {}, "claims": {}, "events": {}},
        "change_log": [],
        "current_snapshot_hash": "",
        "methodology": [
            "التحديث يتم عند طلب الباحث، ولا يجري استدعاء نموذج ذكاء اصطناعي أو خدمة مدفوعة تلقائياً.",
            "المواد والادعاءات والأحداث تحفظ بمعرفاتها ومصادرها، وتُسجل التعديلات بدلاً من استبدال تاريخها.",
            "الاختلاف في حالة الدليل لا يعني أن الادعاء أصبح صحيحاً أو كاذباً؛ إنه تغيير في سجل الباحث.",
            "الروابط إلى ملفات أخرى تُحفظ كإحالات مقترحة مع أساسها، ولا تثبت علاقة سببية.",
            "السجل تراكمي داخل بيانات التطبيق الحالية، وليس نسخة احتياطية أو سجلاً خارجياً غير قابل للتعديل."
        ],
    }


def update_case_file(record, case, dossiers=()):
    """يضيف لقطة وسجل فروق. لا يحذف الأثر السابق عند حذف مادة من الملف الحالي."""
    if not case or not case.get("id"):
        raise ValueError("ملف القضية يحتاج إلى معرف ثابت")
    record = dict(record or new_case_file(case))
    record.setdefault("snapshots", [])
    record.setdefault("change_log", [])
    record.setdefault("ledger", {"materials": {}, "claims": {}, "events": {}})
    for key in ("materials", "claims", "events"):
        record["ledger"].setdefault(key, {})
    snapshot = build_snapshot(case, dossiers)
    if record.get("current_snapshot_hash") == snapshot["hash"]:
        return record, {"changed": False, "events": [], "snapshot_id": None}

    old_content = record["snapshots"][-1]["content"] if record["snapshots"] else {}
    new_content = snapshot["content"]
    changes = []
    definitions = [
        ("materials", "مادة", _material_payload),
        ("claims", "ادعاء", _claim_payload),
        ("events", "حدث", _event_payload),
    ]
    for collection, label, payload_fn in definitions:
        previous = record["ledger"].setdefault(collection, {})
        current_items = {x["id"]: x for x in new_content.get(collection, [])}
        for item_id, item in current_items.items():
            old = previous.get(item_id)
            if old is None:
                entry = {"id": item_id, "first_seen_at": snapshot["captured_at"],
                         "versions": [{"hash": item["hash"], "payload": item["payload"], "recorded_at": snapshot["captured_at"]}]}
                previous[item_id] = entry
                changes.append({"type": f"new_{collection[:-1] if collection.endswith('s') else collection}",
                                "label": f"إضافة {label}", "record_id": item_id,
                                "summary": item["payload"].get("title") or item["payload"].get("statement") or item["payload"].get("date", ""),
                                "at": snapshot["captured_at"]})
            else:
                if old.get("removed_from_current_case"):
                    old["restored_to_current_case"] = {"at": snapshot["captured_at"], "note": "عاد العنصر إلى الملف الحالي."}
                    old.pop("removed_from_current_case", None)
                    changes.append({"type": f"restored_{collection}", "label": f"إعادة {label} إلى الملف الحالي",
                                    "record_id": item_id, "summary": item["payload"].get("title") or item["payload"].get("statement", ""),
                                    "at": snapshot["captured_at"]})
            if old is not None and old.get("versions") and old["versions"][-1].get("hash") != item["hash"]:
                before = old["versions"][-1]["payload"]
                after = item["payload"]
                changed_fields = [k for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)]
                old["versions"].append({"hash": item["hash"], "payload": after, "recorded_at": snapshot["captured_at"],
                                        "changed_fields": changed_fields})
                label_text = f"تحديث {label}"
                if collection == "claims" and before.get("status") != after.get("status"):
                    label_text = "تغيير حالة دليل ادعاء"
                changes.append({"type": f"updated_{collection}", "label": label_text,
                                "record_id": item_id, "changed_fields": changed_fields,
                                "before": before, "after": after, "at": snapshot["captured_at"]})
        # العناصر التي اختفت من الملف الحالي تظل في السجل مع علامة حذف/إزالة للمراجعة.
        for item_id, old in previous.items():
            if item_id not in current_items and not old.get("removed_from_current_case"):
                old["removed_from_current_case"] = {"at": snapshot["captured_at"], "note": "اختفى العنصر من الملف الحالي؛ احتُفظ بتاريخه التراكمي."}
                changes.append({"type": f"removed_{collection}", "label": f"إزالة {label} من الملف الحالي",
                                "record_id": item_id, "summary": old.get("versions", [{}])[-1].get("payload", {}).get("title", ""),
                                "at": snapshot["captured_at"]})

    if old_content.get("title") != new_content.get("title"):
        changes.append({"type": "case_title_changed", "label": "تغيير عنوان القضية",
                        "before": old_content.get("title", ""), "after": new_content.get("title", ""), "at": snapshot["captured_at"]})
    if old_content.get("description") != new_content.get("description"):
        changes.append({"type": "case_scope_changed", "label": "تعديل وصف أو نطاق القضية",
                        "before": old_content.get("description", ""), "after": new_content.get("description", ""), "at": snapshot["captured_at"]})
    old_refs = {_json_hash(x) for x in old_content.get("related_dossier_references", [])}
    for ref in new_content.get("related_dossier_references", []):
        if _json_hash(ref) not in old_refs:
            changes.append({"type": "related_dossier_added", "label": "إحالة من ملف تغطيات جديد",
                            "reference": ref, "at": snapshot["captured_at"]})

    snapshot["id"] = f"snap_{len(record['snapshots']) + 1}_{snapshot['hash'][:10]}"
    snapshot["change_count"] = len(changes)
    # اللقطة تحفظ بصمة ومعرفات العناصر، أما تفاصيل الإصدارات فتوجد مرة واحدة في سجل الأدلة.
    full_content = snapshot["content"]
    snapshot["content"] = {
        "title": full_content.get("title", ""),
        "description": full_content.get("description", ""),
        "tags": full_content.get("tags", []),
        "research_notes": full_content.get("research_notes", ""),
        "materials": [{"id": x["id"], "hash": x["hash"]} for x in full_content.get("materials", [])],
        "claims": [{"id": x["id"], "hash": x["hash"]} for x in full_content.get("claims", [])],
        "events": [{"id": x["id"], "hash": x["hash"]} for x in full_content.get("events", [])],
        "related_dossier_references": full_content.get("related_dossier_references", []),
    }
    record["snapshots"].append(snapshot)
    record["snapshots"] = record["snapshots"][-100:]
    record["change_log"].extend(changes)
    record["change_log"] = record["change_log"][-2000:]
    record["current_snapshot_hash"] = snapshot["hash"]
    record["title"] = case.get("title", record.get("title", ""))
    record["updated_at"] = snapshot["captured_at"]
    return record, {"changed": True, "events": changes, "snapshot_id": snapshot["id"]}


def build_cumulative_prompt(case, record):
    """برومبت قابل للنسخ والتحرير؛ لا ينفذ أي طلب AI بنفسه."""
    recent = (record or {}).get("change_log", [])[-100:]
    change_lines = []
    for item in recent:
        after_value = item.get("after", {})
        after_map = after_value if isinstance(after_value, dict) else {}
        summary = item.get("summary") or after_map.get("statement") or after_map.get("title") or (str(after_value) if after_value else "")
        if item.get("type") == "updated_claims":
            before = item.get("before", {})
            after = after_map
            summary = f"{after.get('statement', '')} | الحالة: {before.get('status', 'غير محدد')} ← {after.get('status', 'غير محدد')}"
        change_lines.append(f"- {item.get('at', '')} | {item.get('label', item.get('type', 'تغيير'))} | {summary}")
    materials = []
    for i, item in enumerate(case.get("materials", []) or [], 1):
        materials.append(
            f"[مادة {i}] {item.get('title', '')}\nالنوع: {item.get('type', '')} | الكاتب: {item.get('author', '')} | المنبر: {item.get('outlet', '')}\n"
            f"التاريخ: {item.get('date', '')}\nالرابط: {item.get('url', '')}\nالنص المتاح: {item.get('text', '') or 'لا يوجد نص محفوظ؛ لا تستنتج من العنوان وحده.'}"
        )
    claims = "\n".join(
        f"- {x.get('statement')} | الحالة الحالية: {x.get('status')} | النوع: {x.get('type')} | المصدر: {x.get('source', '')}"
        for x in case.get("claims", []) or []) or "لا توجد ادعاءات مسجلة يدوياً."
    events = "\n".join(
        f"- {x.get('date')}: {x.get('title')} | {x.get('detail')} | المصدر: {x.get('source', '')}"
        for x in case.get("events", []) or []) or "لا توجد أحداث مدخلة يدوياً."
    return f"""أنت محلل استخبارات مصادر مفتوحة وباحث توثيق. المطلوب تحديث ملف القضية تراكميًا، لا إعادة كتابة تقرير منفصل يتجاهل التاريخ السابق.

# ملف القضية
العنوان: {case.get('title', '')}
الوصف والنطاق: {case.get('description', '')}
الوسوم: {'، '.join(case.get('tags', []) or [])}
عدد اللقطات التراكمية المحفوظة: {len((record or {}).get('snapshots', []))}
آخر تحديث للسجل: {(record or {}).get('updated_at', 'غير متاح')}

# سجل التغييرات منذ بداية التتبع
{chr(10).join(change_lines) if change_lines else 'لا توجد تغييرات تاريخية محفوظة بعد أول لقطة.'}

# المواد الحالية ومصادرها
{chr(10).join(materials) if materials else 'لا توجد مواد.'}

# سجل الادعاءات الحالي
{claims}

# الأحداث الحالية
{events}

# المطلوب في التحديث
1. اكتب ملخصاً لما استجد فقط، ثم ملخصاً تراكمياً محدثاً للقضية.
2. افصل بين معلومة جديدة، وتصحيح لمعلومة سابقة، وتفسير جديد، وتوقع.
3. حدّد الادعاءات التي تغيرت حالة دليلها، واعرض الحالة القديمة والجديدة، ولا تعتبر تغيير الحالة دليلاً بذاته.
4. حدّث الخط الزمني مع الفصل الصريح بين تاريخ وقوع الحدث وتاريخ نشر الخبر. لا تستنتج تاريخ الحدث من تاريخ النشر.
5. أنشئ سجل أدلة يربط كل نقطة بمادة ورابط ومقتطف أو نص متاح. إذا لم يتوفر النص فاذكر ذلك.
6. أظهر ما يؤيد الاستنتاج وما يناقضه، وحدد المصادر التي تنقل عن أصل واحد حتى لا يُحسب التكرار كتأكيد مستقل.
7. راجع الاستنتاجات السابقة: ما الذي ما زال قائماً، وما الذي ضعف، وما الذي يجب سحبه أو تعليقه؟ اشرح الدليل وراء كل تعديل.
8. أضف الأسئلة المفتوحة ومؤشرات المتابعة التي تستحق الرصد في التحديث القادم.
9. أعطِ تقدير ثقة منفصلاً لكل استنتاج، مع سبب وحدود واضحة.
10. اختم بملخص تنفيذي محدث وبصيغة مناسبة للتحويل إلى تقرير عربي أو سكريبت باللهجة المصرية عند الطلب.

# قواعد إلزامية
- لا تخترع أحداثاً أو تصريحات أو روابط أو اقتباسات.
- لا تملأ الفجوات بمعلومات من الذاكرة العامة دون تمييزها بوضوح عن المواد المقدمة.
- لا تخلط بين التزامن والسببية، ولا بين تكرار الخبر واستقلال التحقق.
- احتفظ بالتناقضات غير المحسومة بدلاً من تسويتها قسراً.
- لا تحذف استنتاجاً سابقاً بصمت؛ اذكر سبب تعديله أو تعليقه.
- إذا كانت المادة مجرد عنوان أو ملخص، قل ذلك بوضوح.
- لا تنفذ بحثاً أو استدعاء API أو عملية مدفوعة. هذا برومبت للتحليل اليدوي بعد مراجعة الباحث.

{prompt_style.source_block()}"""


def summarize(record):
    ledger = record.get("ledger", {}) if isinstance(record, dict) else {}
    return {
        "snapshots": len(record.get("snapshots", []) or []),
        "changes": len(record.get("change_log", []) or []),
        "materials_tracked": len(ledger.get("materials", {}) or {}),
        "claims_tracked": len(ledger.get("claims", {}) or {}),
        "events_tracked": len(ledger.get("events", {}) or {}),
        "updated_at": record.get("updated_at", ""),
    }

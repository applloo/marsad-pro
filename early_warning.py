# -*- coding: utf-8 -*-
"""مركز الإنذار المبكر: مقارنة تراكمية قابلة للمراجعة للمواد والادعاءات والأحداث والمواقف."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import re

try:
    import case_links
except Exception:
    case_links = None

ESCALATION = {
    "تصعيد": ["تصعيد", "هجوم", "ضربة", "قصف", "اجتياح", "تهديد", "إنذار", "تعبئة", "حشد عسكري", "عملية عسكرية", "escalation", "strike", "attack", "invasion", "threat", "mobilization"],
    "تهدئة": ["تهدئة", "خفض التصعيد", "وقف إطلاق النار", "هدنة", "استئناف المفاوضات", "اتفاق", "انسحاب", "de-escalation", "ceasefire", "truce", "talks", "withdrawal"],
    "تشدد خطابي": ["لن نسمح", "خط أحمر", "رد حاسم", "ثمن باهظ", "سحق", "تدمير", "لن نتراجع", "red line", "decisive response", "crush", "destroy"],
    "انفتاح دبلوماسي": ["محادثات", "حوار", "مبادرة", "وساطة", "لقاء", "اتصال", "تفاهم", "dialogue", "initiative", "mediation", "meeting"]
}

URGENT_TERMS = ("هجوم", "ضربة", "قصف", "اجتياح", "تعبئة", "حشد عسكري", "إنذار", "attack", "strike", "bombardment", "invasion", "mobilization")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _material_id(m):
    return str(m.get("id") or m.get("url") or hashlib.sha1((m.get("title", "") + m.get("date", "")).encode()).hexdigest())


def _text(m):
    return " ".join(str(m.get(k) or "") for k in ("title", "text", "stance", "note"))


def _signals(text):
    low = str(text or "").lower()
    return {group: [term for term in terms if term.lower() in low] for group, terms in ESCALATION.items() if any(term.lower() in low for term in terms)}


def _entities(text):
    if case_links:
        try:
            return case_links.extract_entities(text)
        except Exception:
            return []
    return []


def _fingerprint(row, keys):
    return hashlib.sha256(_stable({k: row.get(k) for k in keys}).encode("utf-8")).hexdigest()


def _snapshot(case):
    materials = case.get("materials", []) or []
    return {
        "material_ids": sorted(_material_id(m) for m in materials),
        "material_fingerprints": {_material_id(m): _fingerprint(m, ("title", "text", "stance", "note", "author", "outlet", "date", "type", "speaker", "actor", "position")) for m in materials},
        "entities": sorted(set(_entities(" ".join(_text(m) for m in materials)) + _entities(case.get("title", "") + " " + case.get("description", "")))),
        "claims": {_material_id(c): _fingerprint(c, ("statement", "type", "status", "source", "note")) for c in case.get("claims", []) or []},
        "claim_rows": {_material_id(c): dict(c) for c in case.get("claims", []) or []},
        "events": {_material_id(e): _fingerprint(e, ("date", "title", "detail", "source")) for e in case.get("events", []) or []},
        "event_rows": {_material_id(e): dict(e) for e in case.get("events", []) or []},
        "material_count": len(materials), "updated_at": case.get("updated_at", ""),
    }


def _severity(materials, changed_claims, changed_events, stance_changes):
    text = " ".join(_text(m) for m in materials).lower()
    urgent_hits = [term for term in URGENT_TERMS if term.lower() in text]
    if urgent_hits:
        return "مراجعة عاجلة", "warning", urgent_hits
    if stance_changes or changed_claims or changed_events:
        return "مراجعة مهمة", "review", []
    return "متابعة", "info", []


def scan_cases(cases, state=None):
    """ينشئ خط أساس أولاً، ثم يرصد الإضافات والتعديلات دون اعتبارها إثباتاً لصحتها."""
    state = dict(state or {})
    baselines = dict(state.get("baselines") or {})
    reports = list(state.get("reports") or [])
    alerts, initialized = [], []
    for case in cases or []:
        cid = case.get("id")
        if not cid:
            continue
        snap = _snapshot(case)
        old = baselines.get(cid)
        if old is None:
            initialized.append(case.get("title", "ملف بلا عنوان"))
            snap["material_rows"] = {_material_id(m): dict(m) for m in case.get("materials", []) or []}
            baselines[cid] = snap
            continue
        old_ids = set(old.get("material_ids", []))
        current = {_material_id(m): m for m in case.get("materials", []) or []}
        new_materials = [m for mid, m in current.items() if mid not in old_ids]
        changed_materials = [m for mid, m in current.items() if mid in old_ids and old.get("material_fingerprints", {}).get(mid) and old["material_fingerprints"][mid] != snap["material_fingerprints"][mid]]
        old_entities = set(old.get("entities", []))
        new_entities = sorted(set(snap["entities"]) - old_entities)
        old_claims, new_claims = old.get("claim_rows", {}), { _material_id(c): c for c in case.get("claims", []) or [] }
        changed_claims = []
        for key, row in new_claims.items():
            previous = old_claims.get(key)
            if previous and old.get("claims", {}).get(key) != snap["claims"].get(key):
                changed_claims.append({"id": key, "before": previous, "after": row})
            elif not previous:
                changed_claims.append({"id": key, "before": None, "after": row})
        old_events, new_events = old.get("event_rows", {}), { _material_id(e): e for e in case.get("events", []) or [] }
        changed_events = []
        for key, row in new_events.items():
            previous = old_events.get(key)
            if not previous or old.get("events", {}).get(key) != snap["events"].get(key):
                changed_events.append({"id": key, "before": previous, "after": row})
        # لا نعتبر تغير زاوية المادة موقفاً رسمياً إلا إذا كان المتحدث/الطرف محدداً صراحةً.
        old_actor_positions = {}
        for m in old.get("material_rows", {}).values():
            actor = str(m.get("speaker") or m.get("actor") or "").strip().lower()
            position = str(m.get("position") or m.get("stance") or "").strip()
            if actor and position:
                old_actor_positions.setdefault(actor, set()).add(position)
        stance_changes = []
        for m in case.get("materials", []) or []:
            actor = str(m.get("speaker") or m.get("actor") or "").strip().lower()
            position = str(m.get("position") or m.get("stance") or "").strip()
            mid = _material_id(m)
            if actor and position and actor in old_actor_positions and position not in old_actor_positions[actor] and mid not in old_ids:
                stance_changes.append({"actor": m.get("speaker") or m.get("actor"), "previous_positions": sorted(old_actor_positions[actor]), "new_position": position, "material_id": mid, "title": m.get("title", ""), "url": m.get("url", "")})
        if new_materials or changed_materials or new_entities or changed_claims or changed_events or stance_changes:
            material_alerts = []
            for m in new_materials:
                text = _text(m)
                material_alerts.append({"material_id": _material_id(m), "title": m.get("title", "مادة بلا عنوان"), "type": m.get("type", "غير محدد"), "date": m.get("date", ""), "url": m.get("url", ""), "author": m.get("author", ""), "outlet": m.get("outlet", ""), "speaker": m.get("speaker") or m.get("actor", ""), "signals": _signals(text), "entities": _entities(text), "text_available": bool(m.get("text"))})
            changed_alerts = [{"material_id": _material_id(m), "title": m.get("title", "مادة معدلة"), "url": m.get("url", ""), "changed_fields": [k for k in ("title", "text", "stance", "note", "author", "outlet", "date", "type", "speaker", "actor", "position") if old.get("material_fingerprints", {}).get(_material_id(m)) != snap["material_fingerprints"][_material_id(m)] and old.get("material_rows", {}).get(_material_id(m), {}).get(k) != m.get(k)]} for m in changed_materials]
            severity, severity_code, urgent_terms = _severity(new_materials + changed_materials, changed_claims, changed_events, stance_changes)
            alerts.append({"id": hashlib.sha1(f"{cid}|{now_iso()}".encode()).hexdigest()[:14], "case_id": cid, "case_title": case.get("title", ""), "created_at": now_iso(), "new_materials": material_alerts, "changed_materials": changed_alerts, "new_entities": new_entities, "changed_claims": changed_claims, "changed_events": changed_events, "stance_changes": stance_changes, "severity": severity, "severity_code": severity_code, "urgent_terms": urgent_terms, "signal_groups": sorted({g for m in material_alerts for g in m["signals"]}), "note": "هذا رصد آلي لتغيرات في السجل ومؤشرات نصية. لا يثبت صحة المادة أو حدوث تغير سياسي؛ يلزم فحص المصدر والسياق ومراجعة بشرية."})
        baselines[cid] = snap
        baselines[cid]["material_rows"] = { _material_id(m): dict(m) for m in case.get("materials", []) or [] }
    reports.extend(alerts)
    reports = reports[-500:]
    return {"baselines": baselines, "reports": reports, "last_scan": now_iso()}, alerts, initialized


def build_daily_brief(alerts, date_label=None):
    date_label = date_label or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# موجز الإنذار المبكر | {date_label}", "", f"عدد الملفات التي ظهر بها تغيير: {len(alerts or [])}", ""]
    if not alerts:
        lines.append("لم تُرصد تغييرات جديدة مقارنة بآخر خط أساس محفوظ.")
    for a in alerts or []:
        lines += [f"## {a.get('case_title')}", f"درجة المتابعة: {a.get('severity', 'غير مصنفة')}", f"وقت الرصد: {a.get('created_at')}"]
        if a.get("new_entities"): lines.append("كيانات جديدة: " + "، ".join(a["new_entities"]))
        for m in a.get("new_materials", []):
            lines.append(f"- [مادة جديدة: {m.get('type')}] {m.get('title')} | {m.get('outlet')} | {m.get('date')} | {m.get('url')}")
            for group, terms in m.get("signals", {}).items(): lines.append(f"  - إشارة لغوية ({group}): " + "، ".join(terms))
        for m in a.get("changed_materials", []): lines.append(f"- [مادة تغيرت بياناتها] {m.get('title')} | الحقول: {', '.join(m.get('changed_fields', []))} | {m.get('url')}")
        for c in a.get("changed_claims", []):
            before, after = c.get("before") or {}, c.get("after") or {}
            lines.append(f"- [تغير ادعاء] {before.get('statement') or after.get('statement')} | الحالة: {before.get('status', 'جديد')} ← {after.get('status', 'غير محدد')} | المصدر: {after.get('source', '')}")
        for e in a.get("changed_events", []):
            before, after = e.get("before") or {}, e.get("after") or {}
            lines.append(f"- [تغير حدث] {before.get('title') or after.get('title')} | {before.get('date', '')} ← {after.get('date', '')} | المصدر: {after.get('source', '')}")
        for s in a.get("stance_changes", []): lines.append(f"- [تغير زاوية/موقف مسجل يحتاج مراجعة] {s.get('actor')}: {', '.join(s.get('previous_positions', []))} ← {s.get('new_position')} | {s.get('url')}")
        lines.append(a.get("note", "")); lines.append("")
    lines += ["## حدود الرصد", "الموجز يقارن السجلات المحفوظة منذ آخر خط أساس. لا يثبت صحة المحتوى أو حدوث تصعيد فعلي. إشارات الكلمات ليست إثباتاً لحدث أو نية. تغير زاوية/موقف لا يظهر إلا عند وجود متحدث/طرف محدد وحقل موقف محفوظ. لا يثبت الرصد وجود تناقض بين روايتين؛ يجب فحص الادعاءات ومصادرها وتواريخها يدوياً أو عبر تحليل موثق."]
    return "\n".join(lines)


def build_analysis_prompt(alerts, cases_by_id=None):
    brief = build_daily_brief(alerts)
    return f"""أنت محلل إنذار مبكر. حلل موجز التغيرات التالي اعتماداً حصراً على المواد والسجلات المذكورة فيه.\n\n{brief}\n\nأنتج تقريراً بالأقسام التالية: (1) الجديد مقارنة بخط الأساس. (2) البيانات أو الادعاءات التي تغيرت حرفياً، مع قبل/بعد ومصدر التغيير. (3) هل يوجد تعارض مباشر بين تصريحين؟ لا تسمه تناقضاً قبل مطابقة المتحدث والسياق والتاريخ ونص الادعاء. (4) هل يوجد تحول موقف مسجل؟ لا تستنتجه من كلمة أو عنوان؛ تحقق من هوية المتحدث ومصدر أولي ومقارنة نصين مؤرخين. لا تستنتج ذلك من كلمة منفردة. (5) التحركات والأحداث الجديدة وما هو مؤكد مقابل المنسوب. (6) إشارات تستحق المتابعة وما سببها. (7) هل يستحق الأمر مراجعة عاجلة؟ اذكر معيار القرار ولا تساوِ الكلمات الدالة بالحدث الفعلي. (8) تفسيرات بديلة غير تصعيدية. (9) فجوات المعلومات ومصادر التحقق المطلوبة. (10) درجة ثقة منفصلة لكل استنتاج.\n\nقواعد: لا تخترع تصريحات أو تواريخ أو أحداثاً. افصل الواقعة المنشورة عن الإشارة اللغوية والاستنتاج. اعتبر درجة المتابعة الآلية أولوية فرز لا حكماً استخباراتياً. اذكر حدود النصوص المقتطفة وتعدد المصادر المستقلة."""

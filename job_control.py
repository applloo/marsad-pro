# -*- coding: utf-8 -*-
"""Durable, auditable task lifecycle helpers for Marsad.

This module is deliberately storage-agnostic. Callers persist returned records
through the existing store/Gist layer. It does not claim distributed locking.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

STATES = {"queued", "submitted", "running", "succeeded", "failed", "cancelled", "stale"}
ACTIVE = {"queued", "submitted", "running"}
TERMINAL = {"succeeded", "failed", "cancelled", "stale"}
TRANSITIONS = {
    "queued": {"submitted", "running", "failed", "cancelled"},
    "submitted": {"running", "succeeded", "failed", "cancelled", "stale"},
    "running": {"succeeded", "failed", "cancelled", "stale"},
    "stale": {"running", "failed", "cancelled"},
    "failed": {"queued"},
    "cancelled": {"queued"},
    "succeeded": set(),
}


def utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def iso(value=None):
    return utc_now(value).isoformat(timespec="seconds")


def new_task(workflow: str, label: str, *, details=None, idempotency_key=None, now=None) -> dict:
    if not workflow or not label:
        raise ValueError("اسم المهمة ونوعها مطلوبان")
    stamp = iso(now)
    task_id = str(uuid4())
    return {
        "id": task_id, "workflow": str(workflow), "label": str(label),
        "details": str(details or "")[:500], "idempotency_key": idempotency_key,
        "state": "queued", "attempt": 1, "created_at": stamp,
        "updated_at": stamp, "heartbeat_at": stamp, "events": [
            {"at": stamp, "state": "queued", "message": "تم إنشاء طلب التشغيل"}
        ],
    }


def find_active(tasks, workflow, idempotency_key=None):
    for task in (tasks or []):
        if task.get("workflow") != workflow or task.get("state") not in ACTIVE:
            continue
        if idempotency_key is None or task.get("idempotency_key") == idempotency_key:
            return task
    return None


def transition(task: dict, state: str, message="", *, now=None, metadata=None) -> dict:
    if state not in STATES:
        raise ValueError("حالة المهمة غير معروفة")
    current = task.get("state")
    if state == current:
        return task
    if state not in TRANSITIONS.get(current, set()):
        raise ValueError(f"انتقال غير مسموح: {current} -> {state}")
    stamp = iso(now)
    task["state"] = state
    task["updated_at"] = stamp
    if state in ACTIVE:
        task["heartbeat_at"] = stamp
    if state in TERMINAL:
        task["finished_at"] = stamp
    if metadata:
        task.setdefault("metadata", {}).update(metadata)
    task.setdefault("events", []).append({
        "at": stamp, "state": state, "message": str(message or "")[:500]
    })
    task["events"] = task["events"][-50:]
    return task


def heartbeat(task: dict, message="", *, now=None) -> dict:
    if task.get("state") not in ACTIVE:
        return task
    stamp = iso(now)
    task["heartbeat_at"] = stamp
    task["updated_at"] = stamp
    if message:
        task.setdefault("events", []).append({
            "at": stamp, "state": task["state"], "message": str(message)[:500]
        })
        task["events"] = task["events"][-50:]
    return task


def mark_stale(tasks, *, stale_after_minutes=90, now=None):
    """Mark old active tasks stale for human review; never assumes they failed."""
    current = utc_now(now)
    changed = []
    for task in (tasks or []):
        if task.get("state") not in ACTIVE:
            continue
        raw = task.get("heartbeat_at") or task.get("updated_at") or task.get("created_at")
        try:
            last = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
        if current - last.astimezone(timezone.utc) > timedelta(minutes=max(1, int(stale_after_minutes))):
            transition(task, "stale", "لم يصل تحديث خلال المهلة؛ يلزم التحقق من حالة التشغيل الفعلية", now=current)
            changed.append(task)
    return changed


def retry_task(task: dict, *, now=None) -> dict:
    if task.get("state") not in {"failed", "cancelled"}:
        raise ValueError("يمكن إعادة محاولة المهمة الفاشلة أو الملغاة فقط")
    retry = new_task(
        task.get("workflow", "unknown"), task.get("label", "مهمة"),
        details=task.get("details", ""), idempotency_key=task.get("idempotency_key"),
        now=now,
    )
    retry["attempt"] = int(task.get("attempt", 1)) + 1
    retry["parent_task_id"] = task.get("id")
    retry["events"][0]["message"] = f"إعادة محاولة للمهمة {task.get('id')}"
    return retry


def append_event(tasks, task: dict, *, limit=300):
    rows = list(tasks or [])
    existing = next((i for i, row in enumerate(rows) if row.get("id") == task.get("id")), None)
    if existing is None:
        rows.insert(0, task)
    else:
        rows[existing] = task
    return rows[:max(1, int(limit))]


def summary(tasks):
    rows = list(tasks or [])
    counts = {state: sum(1 for x in rows if x.get("state") == state) for state in sorted(STATES)}
    return {"total": len(rows), "active": sum(counts[x] for x in ACTIVE),
            "failed": counts["failed"], "stale": counts["stale"], "counts": counts}

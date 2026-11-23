# -*- coding: utf-8 -*-
"""Persistent user-maintained billing profiles. Prices are estimates, not provider quotes."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib


def profile_key(provider: str, model: str) -> str:
    raw = f"{provider.strip()}::{model.strip()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def get_profile(settings: dict, provider: str, model: str) -> dict:
    profiles = (settings or {}).get("billing_profiles", {})
    return dict(profiles.get(profile_key(provider, model), {}))


def save_profile(settings: dict, provider: str, model: str, input_price: float,
                 output_price: float, monthly_budget: float, source_url: str = "") -> dict:
    if not provider.strip() or not model.strip():
        raise ValueError("حدد المزود واسم النموذج")
    if input_price <= 0 or output_price <= 0 or monthly_budget <= 0:
        raise ValueError("أسعار الإدخال والإخراج وسقف الإنفاق يجب أن تكون أكبر من صفر")
    settings.setdefault("billing_profiles", {})[profile_key(provider, model)] = {
        "provider": provider, "model": model,
        "input_price_per_million": float(input_price),
        "output_price_per_million": float(output_price),
        "monthly_budget_usd": float(monthly_budget),
        "currency": "USD", "pricing_source_url": str(source_url or "").strip(),
        "last_reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return settings["billing_profiles"][profile_key(provider, model)]


def month_spend(usage_rows: list, month: str, provider: str, model: str) -> float:
    return sum(float(row.get("cost_usd") or 0) for row in usage_rows
               if row.get("month") == month and row.get("provider") == provider
               and row.get("model") == model)


def preflight(used: float, projected: float, budget: float) -> dict:
    remaining = max(0.0, float(budget) - float(used))
    after = float(used) + float(projected)
    return {"allowed": budget > 0 and after <= float(budget),
            "used_usd": float(used), "projected_usd": float(projected),
            "remaining_usd": remaining, "after_usd": after,
            "over_by_usd": max(0.0, after - float(budget))}


def active_reservations(settings: dict, provider: str, model: str, month: str, now=None) -> list:
    """Return unexpired pending reservations for one provider/model/month."""
    now_dt = now or datetime.now(timezone.utc)
    if isinstance(now_dt, str):
        now_dt = datetime.fromisoformat(now_dt.replace("Z", "+00:00"))
    rows = (settings or {}).get("billing_reservations", [])
    active = []
    for row in rows:
        if row.get("provider") != provider or row.get("model") != model or row.get("month") != month:
            continue
        if row.get("status") != "pending":
            continue
        try:
            expires = datetime.fromisoformat(str(row.get("expires_at", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if expires > now_dt:
            active.append(row)
    return active


def reserved_spend(settings: dict, provider: str, model: str, month: str, now=None) -> float:
    return sum(float(x.get("amount_usd") or 0) for x in active_reservations(settings, provider, model, month, now))


def reserve(settings: dict, provider: str, model: str, month: str, amount: float,
            request_id: str, ttl_seconds: int = 900, now=None) -> dict:
    """Add a durable-intent reservation record. Persistence/CAS is the caller's job.

    Gist does not provide an atomic compare-and-swap primitive, so this is a
    best-effort cross-session guard, not a hard distributed lock or billing cap.
    """
    if not request_id or not provider or not model or amount < 0 or ttl_seconds < 1:
        raise ValueError("بيانات حجز الإنفاق غير صالحة")
    settings.setdefault("billing_reservations", [])
    existing = next((x for x in settings["billing_reservations"] if x.get("id") == request_id), None)
    if existing:
        return existing
    now_dt = now or datetime.now(timezone.utc)
    expires = now_dt.timestamp() + int(ttl_seconds)
    row = {
        "id": request_id, "provider": provider, "model": model, "month": month,
        "amount_usd": round(float(amount), 8), "status": "pending",
        "created_at": now_dt.isoformat(timespec="seconds"),
        "expires_at": datetime.fromtimestamp(expires, timezone.utc).isoformat(timespec="seconds"),
    }
    settings["billing_reservations"].insert(0, row)
    settings["billing_reservations"] = settings["billing_reservations"][:500]
    return row


def finish_reservation(settings: dict, request_id: str, actual_cost: float = 0.0,
                       status: str = "settled") -> bool:
    if status not in ("settled", "released", "failed"):
        raise ValueError("حالة الحجز غير معروفة")
    for row in (settings or {}).get("billing_reservations", []):
        if row.get("id") == request_id:
            row["status"] = status
            row["actual_cost_usd"] = round(max(0.0, float(actual_cost or 0)), 8)
            row["finished_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            return True
    return False


def budget_preflight(usage_rows: list, settings: dict, month: str, provider: str,
                     model: str, projected: float, budget: float) -> dict:
    committed = month_spend(usage_rows, month, provider, model)
    reserved = reserved_spend(settings, provider, model, month)
    check = preflight(committed + reserved, projected, budget)
    check.update({"committed_usd": committed, "reserved_usd": reserved})
    return check

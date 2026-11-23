# -*- coding: utf-8 -*-
"""Article-reader quality signals. Heuristics only; never claim extraction is complete."""
from __future__ import annotations
import re

_PAYWALL = re.compile(r"subscribe|subscription|sign\s*in|log\s*in|members\s*only|premium content|للمشتركين|اشترك الآن|سجّل الدخول|تسجيل الدخول|למנויים|הרשמה", re.I)
_LOADING = re.compile(r"loading\.\.\.|جار(?:ٍ|ي)? التحميل|please wait|enable javascript|جافاسكربت", re.I)


def inspect_article(text: str) -> dict:
    """Return cautious completeness/summary signals from extracted text."""
    value = (text or "").strip()
    chars = len(value)
    words = len(value.split())
    tail = value[-700:] if value else ""
    paywall = bool(_PAYWALL.search(tail))
    loading = bool(_LOADING.search(tail))
    if chars < 120:
        status, label, detail = "insufficient", "نص غير كافٍ", "المحتوى المستخرج أقصر من أن يُعامل كمقال قابل للتحليل."
    elif paywall or loading or chars < 1800:
        status, label, detail = "possibly_partial", "قد يكون مقتطفاً أو نصاً جزئياً", "قد تكون بقية المادة محجوبة أو محمّلة ديناميكياً؛ لا يمكن تأكيد اكتمال النص آلياً."
    else:
        status, label, detail = "usable_unverified", "نص قابل للقراءة، واكتماله غير مؤكد", "طول النص مناسب مبدئياً، لكن الطول وحده لا يثبت أن المقال كامل."
    minutes = max(1, round(words / 190)) if words else 0
    return {
        "status": status, "label": label, "detail": detail,
        "chars": chars, "words": words, "reading_minutes": minutes,
        "summary_allowed": chars >= 400 and words >= 60,
        "paywall_signal": paywall, "loading_signal": loading,
    }


def metadata_rows(article: dict | None) -> list[tuple[str, str]]:
    """Normalize metadata for display without inventing missing values."""
    article = article or {}
    authors = article.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    return [
        ("الكاتب", "، ".join(str(x).strip() for x in authors if str(x).strip()) or "غير متاح في النص المستخرج"),
        ("تاريخ النشر", str(article.get("date") or "غير متاح في النص المستخرج")),
        ("طريقة الاستخراج", str(article.get("via") or "غير محددة")),
    ]

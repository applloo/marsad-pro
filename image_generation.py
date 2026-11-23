# -*- coding: utf-8 -*-
"""توليد صور المشاهد عبر OpenAI Images API مع إبقاء المفاتيح خارج التخزين."""
from __future__ import annotations

import base64
import binascii
import requests

API_URL = "https://api.openai.com/v1/images/generations"
MODELS = ["gpt-image-2.6-flare", "gpt-image-2.5-flare", "gpt-image-2", "gpt-image-1.5", "gpt-image-1-mini"]
FLEXIBLE_SIZE_MODELS = {"gpt-image-2.6-flare", "gpt-image-2.5-flare", "gpt-image-2"}
LEGACY_SIZE_LABELS = ("مربع 1:1", "أفقي 3:2", "رأسي 2:3")


def sizes_for_model(model: str) -> dict:
    """Return only resolutions supported by the selected image model."""
    if model in FLEXIBLE_SIZE_MODELS:
        return dict(SIZES)
    return {label: SIZES[label] for label in LEGACY_SIZE_LABELS}
SIZES = {
    "مربع 1:1": "1024x1024",
    "أفقي 3:2": "1536x1024",
    "رأسي 2:3": "1024x1536",
    "أفقي 16:9": "2048x1152",
    "رأسي 9:16": "1152x2048",
}
QUALITIES = ["low", "medium", "high"]


def generate_image(prompt: str, api_key: str, model: str = "gpt-image-2.6-flare",
                   size: str = "1024x1536", quality: str = "medium", timeout: int = 240) -> dict:
    """Generate one image and return bytes plus safe metadata. Never logs or returns the API key."""
    prompt = str(prompt or "").strip()
    if not prompt:
        raise ValueError("اكتب وصف الصورة أولاً")
    if len(prompt) > 12000:
        raise ValueError("وصف الصورة طويل جداً، اختصره إلى 12 ألف حرف")
    if not api_key or not str(api_key).strip():
        raise ValueError("مفتاح OPENAI_API_KEY مطلوب لتوليد الصور")
    if model not in MODELS:
        raise ValueError("نموذج الصور غير مدعوم في هذه الواجهة")
    if size not in sizes_for_model(model).values():
        raise ValueError("المقاس المختار غير مدعوم مع نموذج الصور المحدد. اختر مقاساً متاحاً لهذا النموذج.")
    if quality not in QUALITIES:
        raise ValueError("جودة الصورة غير مدعومة")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {str(api_key).strip()}", "Content-Type": "application/json"},
        json={"model": model, "prompt": prompt, "size": size, "quality": quality,
              "output_format": "png", "n": 1},
        timeout=timeout,
    )
    if response.status_code >= 400:
        try:
            payload = response.json()
            err = payload.get("error") or {}
            message = err.get("message") or payload.get("message") or ""
            code = err.get("code") or ""
        except Exception:
            message, code = "", ""
        safe_detail = str(message)[:350]
        if code == "moderation_blocked":
            raise RuntimeError("تم إيقاف الطلب بواسطة مراجعة المحتوى. عدّل الوصف البصري وحاول مجدداً.")
        if response.status_code in (401, 403):
            raise RuntimeError("مفتاح API غير صالح أو لا يملك صلاحية استخدام نموذج الصور. راجع إعدادات حساب OpenAI والتحقق المؤسسي عند الحاجة.")
        if response.status_code == 429:
            raise RuntimeError("تم تجاوز حد الاستخدام أو الرصيد المتاح لدى مزود الصور. راجع حدود الحساب والفوترة.")
        raise RuntimeError(f"فشل توليد الصورة (HTTP {response.status_code}). {safe_detail}")

    try:
        item = (response.json().get("data") or [])[0]
        raw = base64.b64decode(item.get("b64_json", ""), validate=True)
    except (ValueError, TypeError, IndexError, KeyError, binascii.Error):
        raise RuntimeError("استجابة مزود الصور لم تحتوِ على صورة صالحة")
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("صيغة الصورة المستلمة غير متوقعة")
    return {"image_bytes": raw, "model": model, "size": size, "quality": quality,
            "request_id": response.headers.get("x-request-id", "")}

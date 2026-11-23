# -*- coding: utf-8 -*-
"""موصلات النماذج لمرصد الأخبار. لا تحفظ مفاتيح API ولا ترسل أي طلب تلقائياً."""
from __future__ import annotations
import requests
from urllib.parse import urlparse

PROVIDERS = {
    "openrouter_free": {
        "label": "OpenRouter · نماذج مجانية فقط", "kind": "openai",
        "base_url": "https://openrouter.ai/api/v1", "secret_name": "OPENROUTER_API_KEY",
        "default_model": "openrouter/free", "free_only": True,
        "models": ["openrouter/free"],
        "note": "موجّه للنماذج المجانية فقط. التوافر والجودة يتغيران، مع حدود يومية ودقيقة.",
    },
    "groq": {
        "label": "Groq · الخطة المجانية", "kind": "openai",
        "base_url": "https://api.groq.com/openai/v1", "secret_name": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-20b", "free_only": True,
        "models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"],
        "note": "استخدمه فقط إذا كان حسابك على الخطة المجانية ولم تفعل فوترة مدفوعة. الحصص تختلف حسب النموذج.",
    },
    "cloudflare": {
        "label": "Cloudflare Workers AI", "kind": "cloudflare",
        "secret_name": "CLOUDFLARE_API_TOKEN", "account_secret": "CLOUDFLARE_ACCOUNT_ID",
        "default_model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "free_only": True,
        "models": ["@cf/meta/llama-3.3-70b-instruct-fp8-fast", "@cf/qwen/qwen2.5-7b-instruct"],
        "note": "حصة مجانية يومية معلنة، لكن تجاوزها على خطة Workers المدفوعة قد يترتب عليه رسوم. بعض النماذج تتطلب فوترة.",
    },
    "gemini": {
        "label": "Google Gemini API", "kind": "gemini",
        "secret_name": "GEMINI_API_KEY", "default_model": "gemini-3.8-flash",
        "models": ["gemini-3.8-flash"],
        "note": "الخطة المجانية والمدفوعة تختلفان في النماذج والحصص والخصوصية. لا يمكن استنتاج نوع الفوترة من المفتاح.",
    },
    "custom_openai": {
        "label": "مزود مخصص · OpenAI-compatible API", "kind": "openai_custom",
        "default_model": "اكتب اسم النموذج", "models": ["اكتب اسم النموذج"],
        "note": "يربط أي مزود يدعم واجهة OpenAI Chat Completions، مثل مزودات الاستضافة والنماذج المتوافقة. أدخل عنوان API الأساسي واسم النموذج ومفتاحه. لا يدعم تلقائياً واجهات الشركات ذات البروتوكولات الخاصة غير المتوافقة.",
    },
    "ollama": {
        "label": "Ollama · تشغيل محلي", "kind": "ollama",
        "default_model": "qwen2.5:7b", "models": ["qwen2.5:7b", "llama3.1:8b", "gemma3:4b"],
        "note": "لا يحتاج API key أو اشتراكاً. يجب أن يكون Ollama شغالاً على نفس الجهاز الذي يشغّل تطبيق مرصد الأخبار.",
    },
}


def provider_options():
    return {v["label"]: k for k, v in PROVIDERS.items()}


def _usage_openai(data):
    u = data.get("usage") or {}
    return {
        "input_tokens": u.get("prompt_tokens", u.get("input_tokens")),
        "output_tokens": u.get("completion_tokens", u.get("output_tokens")),
        "total_tokens": u.get("total_tokens"),
    }


def _post_json(url, headers, payload, timeout):
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if response.status_code >= 400:
        # لا نعيد نص الاستجابة الخام لأنه قد يحتوي بيانات حساسة أو تفاصيل داخلية.
        try:
            detail = (response.json().get("error") or {}).get("message") or response.json().get("message")
        except Exception:
            detail = ""
        raise RuntimeError(f"فشل مزود النموذج (HTTP {response.status_code}). {str(detail)[:400]}")
    return response.json(), response.headers


def call_model(provider_id: str, model: str, prompt: str, api_key: str = "", account_id: str = "",
               base_url: str = "", max_output_tokens: int = 4096, timeout: int = 180):
    """يرسل طلباً واحداً صريحاً ويعيد النص وبيانات الاستخدام. لا يعيد المفتاح في أي نتيجة."""
    if provider_id not in PROVIDERS:
        raise ValueError("مزود غير معروف")
    cfg = PROVIDERS[provider_id]
    if not prompt or not prompt.strip():
        raise ValueError("الحزمة فارغة")
    if len(prompt) > 180_000:
        raise ValueError("الحزمة أكبر من الحد الحالي (180 ألف حرف). قسّمها إلى دفعات قبل الإرسال.")
    if cfg["kind"] not in ("ollama",) and not api_key:
        raise ValueError("مفتاح API غير موجود. أضفه في أسرار التطبيق أو أدخله للجلسة الحالية.")
    model = (model or cfg["default_model"]).strip()
    if cfg["kind"] == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        data, headers = _post_json(url, {"x-goog-api-key": api_key}, {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": int(max_output_tokens)},
        }, timeout)
        candidates = data.get("candidates") or []
        text = "\n".join(p.get("text", "") for p in (candidates[0].get("content", {}).get("parts", []) if candidates else []))
        u = data.get("usageMetadata") or {}
        usage = {"input_tokens": u.get("promptTokenCount"), "output_tokens": u.get("candidatesTokenCount"),
                 "total_tokens": u.get("totalTokenCount")}
        return {"text": text, "usage": usage, "model": model, "provider": provider_id,
                "finish_reason": (candidates[0].get("finishReason") if candidates else "unknown"),
                "cost_usd": None, "rate_headers": {}}

    if cfg["kind"] in ("openai", "openai_custom"):
        root = (base_url or cfg.get("base_url", "")).rstrip("/")
        if cfg["kind"] == "openai_custom":
            parsed = urlparse(root)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("عنوان API المخصص لازم يكون HTTPS صحيحاً، بدون بيانات دخول أو query أو fragment. اكتب العنوان الأساسي مثل https://api.example.com/v1")
            if not model or model == "اكتب اسم النموذج":
                raise ValueError("اكتب اسم النموذج كما يحدده مزود الخدمة")
        elif not root:
            raise ValueError("عنوان المزود غير مضبوط")
        h = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if provider_id == "openrouter_free":
            h.update({"HTTP-Referer": "https://marsad-news.local", "X-Title": "Marsad News"})
        data, response_headers = _post_json(root + "/chat/completions", h, {
            "model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": int(max_output_tokens),
        }, timeout)
        choices = data.get("choices") or []
        content = (choices[0].get("message", {}).get("content") if choices else "") or ""
        if isinstance(content, list):
            content = "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
        return {"text": content, "usage": _usage_openai(data), "model": data.get("model", model),
                "provider": provider_id, "finish_reason": choices[0].get("finish_reason") if choices else "unknown",
                "cost_usd": (data.get("usage") or {}).get("cost"),
                "rate_headers": {k: v for k, v in response_headers.items() if k.lower().startswith("x-ratelimit-")}}

    if cfg["kind"] == "cloudflare":
        if not account_id:
            raise ValueError("أدخل Cloudflare Account ID")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        data, _ = _post_json(url, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                             {"messages": [{"role": "user", "content": prompt}], "max_tokens": int(max_output_tokens)}, timeout)
        result = data.get("result") or {}
        answer = result.get("response") or result.get("output") or ""
        usage = result.get("usage") or data.get("usage") or {}
        return {"text": answer, "usage": {"input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"), "total_tokens": usage.get("total_tokens")},
                "model": model, "provider": provider_id, "finish_reason": "unknown", "cost_usd": None, "rate_headers": {}}

    # Ollama local chat API
    root = (base_url or "http://127.0.0.1:11434").rstrip("/")
    data, _ = _post_json(root + "/api/chat", {"Content-Type": "application/json"}, {
        "model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
        "options": {"temperature": 0.2, "num_predict": int(max_output_tokens)},
    }, timeout)
    u = data.get("prompt_eval_count")
    out = data.get("eval_count")
    return {"text": (data.get("message") or {}).get("content", ""),
            "usage": {"input_tokens": u, "output_tokens": out, "total_tokens": (u + out) if isinstance(u, int) and isinstance(out, int) else None},
            "model": data.get("model", model), "provider": provider_id, "finish_reason": data.get("done_reason", "unknown"),
            "cost_usd": 0.0, "rate_headers": {}}


def estimate_cost(input_tokens, output_tokens, input_price_per_million, output_price_per_million):
    """تقدير بالدولار بناء على أسعار أدخلها المستخدم، وليس تسعيراً مفترضاً."""
    if input_tokens is None or output_tokens is None:
        return None
    return (input_tokens * float(input_price_per_million or 0) + output_tokens * float(output_price_per_million or 0)) / 1_000_000

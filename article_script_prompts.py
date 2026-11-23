# -*- coding: utf-8 -*-
"""Free, source-grounded prompts for turning one or more articles into an Egyptian Arabic script."""
from __future__ import annotations
from urllib.parse import quote_plus


def _val(item, *keys):
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return "غير متاح"


def build_script_prompt(items, *, dialect="عامية مصرية مبسطة", duration="5 إلى 7 دقائق", tone="تحليلي حاد ومتوازن"):
    items = [x for x in (items or []) if isinstance(x, dict)]
    if not items:
        raise ValueError("لا توجد مقالات لبناء البرومبت")
    blocks = []
    for i, item in enumerate(items, 1):
        blocks.append(
            f"المادة [{i}]\nالعنوان العربي: {_val(item, 'title_ar', 'title')}\n"
            f"العنوان الأصلي: {_val(item, 'title_en', 'title')}\n"
            f"المصدر/المنبر: {_val(item, 'outlet', 'source', 'domain')}\n"
            f"الكاتب: {_val(item, 'writer', 'author')}\nالتاريخ: {_val(item, 'seendate', 'date', 'published_at')}\n"
            f"الرابط: {_val(item, 'url', 'link')}\n"
            f"النص أو المقتطف المتاح: {_val(item, 'text', 'full_text', 'summary_ar', 'snip_ar', 'snippet', 'description')}\n"
            f"ملاحظة الاكتمال: لا تفترض أن النص كامل لمجرد توفر العنوان أو المقتطف."
        )
    return f'''أنت باحث ومحلل سياسي وإعلامي مصري، ومهمتك تحويل المواد المرفقة إلى تحليل موثق ثم سكريبت قابل للإلقاء.

إعدادات المخرج:
- اللهجة: {dialect}
- المدة المستهدفة: {duration}
- النبرة: {tone}
- الجمهور: متابع عربي مهتم بالسياسة والشرق الأوسط، دون افتراض خبرة تخصصية.

المواد المصدرية:
{chr(10).join(blocks)}

نفّذ المراحل بالترتيب ولا تتجاوزها:
1) استخرج ما تقوله كل مادة فعلاً، مع رقمها ورابطها. لا تستنتج مضمون مقال مدفوع أو غير متاح من عنوانه وحده.
2) افصل بوضوح بين الوقائع المثبتة، والادعاءات المنسوبة لأصحابها، والتحليل، والرأي، والتوقع.
3) افحص التواريخ: ميّز تاريخ النشر عن تاريخ الحدث، ونبّه إلى أي غموض.
4) قارن الروايات: نقاط الاتفاق والاختلاف والتناقضات المحتملة، وحدد إن كانت المواد مستقلة أم تنقل عن مصدر أصلي واحد.
5) فنّد كل ادعاء مهم: ما الدليل المؤيد؟ ما الدليل المعارض؟ ما التفسير البديل الأقوى؟ وما المعلومة الناقصة التي قد تحسمه؟
6) حلل مصالح وقدرات وقيود الأطراف، لكن لا تنسب نوايا مؤكدة بلا دليل. ميّز الارتباط عن السببية.
7) اذكر أثر التطورات على مصر والمنطقة عندما تسنده المواد، ولا تفرض رابطاً غير موجود.
8) اكتب خلاصة تحليلية متوازنة، ثم سكريبت {dialect} بخطاف قوي غير مضلل، وسرد واضح، وانتقالات طبيعية، وخاتمة تطرح سؤالاً حقيقياً للنقاش.
9) أرفق في النهاية جدول تدقيق: الجملة في السكريبت | نوعها (واقعة/ادعاء/تحليل/توقع) | المصدر | درجة الثقة | ما يلزم للتحقق.

قواعد صارمة:
- لا تخترع معلومات أو اقتباسات أو أرقاماً أو تصريحات أو روابط.
- لا تعامل العنوان أو المقتطف المترجم كأنه نص المقال الكامل.
- إذا كانت المادة خلف اشتراك، قل إن النص الكامل غير متاح واطلب مصدراً مفتوحاً مستقلاً؛ لا تحاول تجاوز الاشتراك.
- لا تساوِ بين مصدرين لمجرد اختلافهما، ولا ترجّح رواية دون أدلة.
- اذكر بوضوح ما لا يمكن استنتاجه من المواد الحالية.
- لا تكتب بلغة أكاديمية ثقيلة. اجعل السكريبت طبيعياً ومناسباً للتسجيل الصوتي.
'''


def alternative_search_links(item):
    title = _val(item, 'title_en', 'title')
    title_ar = _val(item, 'title_ar')
    author = _val(item, 'writer', 'author')
    topic = _val(item, 'title', 'title_ar', 'title_en')
    queries = [
        ('العنوان الأصلي بين علامتي اقتباس', f'"{title}"'),
        ('العنوان العربي', f'"{title_ar}"'),
        ('الكاتب مع الموضوع', f'"{author}" {topic}'),
        ('تغطيات مستقلة مفتوحة', f'{topic} analysis interview report'),
    ]
    return [{'label': label, 'query': query,
             'google': 'https://www.google.com/search?q=' + quote_plus(query),
             'news': 'https://news.google.com/search?q=' + quote_plus(query)} for label, query in queries if query and query not in {'"غير متاح"', 'غير متاح'}]

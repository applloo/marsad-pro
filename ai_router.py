# -*- coding: utf-8 -*-
"""اقتراحات Auto AI Router وحزم مهام قابلة للمراجعة. لا ينفذ أي إرسال."""
from __future__ import annotations

TASKS = {
    "استخراج المعلومات من الأخبار": {
        "goal": "استخراج الوقائع والأسماء والتواريخ والأماكن والأرقام والاقتباسات والادعاءات من كل مادة بصورة منظمة.",
        "deliverables": "جدول حقائق، جدول ادعاءات، الكيانات والأطراف، التواريخ، الروابط إلى المصدر، والفجوات التي تحتاج تحققاً.",
        "priority": ["gemini", "groq", "openrouter_free", "custom_openai", "cloudflare", "ollama"],
    },
    "تحليل الأحداث وربطها": {
        "goal": "بناء تسلسل زمني وربط الأحداث والخيوط والأطراف، مع التمييز بين الارتباط الزمني والسببية.",
        "deliverables": "خط زمني، شبكة علاقات، نقاط تحول، فرضيات بديلة، أدلة مؤيدة ومعارضة، وأسئلة بحث تالية.",
        "priority": ["gemini", "custom_openai", "openrouter_free", "groq", "cloudflare", "ollama"],
    },
    "التحليل الجيوسياسي": {
        "goal": "تحليل مصالح الأطراف وقدراتها وقيودها وأهدافها المعلنة والمحتملة، ووضع سيناريوهات مشروطة.",
        "deliverables": "خريطة مصالح، دوافع وقدرات، مؤشرات إنذار مبكر، ثلاثة سيناريوهات، واحتمالات نوعية مع مبرراتها.",
        "priority": ["gemini", "custom_openai", "openrouter_free", "groq", "ollama", "cloudflare"],
    },
    "كتابة سكريبت باللهجة المصرية": {
        "goal": "تحويل النتائج الموثقة إلى سكريبت مصري طبيعي مبسط صالح للإلقاء، من دون التضحية بالدقة.",
        "deliverables": "عنوان جذاب غير مضلل، افتتاحية قوية، سكريبت بإيقاع صوتي، خاتمة، ومصادر منفصلة عن نص الإلقاء.",
        "priority": ["gemini", "groq", "openrouter_free", "custom_openai", "cloudflare", "ollama"],
    },
    "إنتاج المحتوى": {
        "goal": "تحويل التحليل إلى حزمة إنتاج محتوى متعددة المنصات ومخرجات قابلة للتنفيذ.",
        "deliverables": "أفكار زوايا، سكريبت، تقسيم مشاهد، تعليمات بصرية، عناوين ووصف ومنشورات قصيرة لكل منصة.",
        "priority": ["gemini", "custom_openai", "openrouter_free", "groq", "ollama", "cloudflare"],
    },
}


def build_task_prompt(base_package: str, task: str, extra_instructions: str = "") -> str:
    if task not in TASKS:
        raise ValueError("نوع المهمة غير معروف")
    spec = TASKS[task]
    parts = [base_package.strip(), "\n\n# تكليف Auto AI Router", f"## المهمة الأساسية\n{task}",
             f"## الهدف\n{spec['goal']}", f"## المخرجات المطلوبة\n{spec['deliverables']}",
             "## قواعد التنفيذ\n- استخدم المواد المرفقة فقط كقاعدة للوقائع، وميّز بوضوح أي معرفة خارجية أو افتراض.\n"
             "- لا تخترع مصادر أو روابط أو اقتباسات أو أرقاماً.\n"
             "- اربط كل معلومة مهمة بمصدرها، واذكر تاريخ المصدر إن توفر.\n"
             "- افصل الوقائع عن الادعاءات والتحليل والسيناريوهات.\n"
             "- اذكر ما لا تستطيع إنجازه بسبب نقص البيانات بدلاً من ملء الفراغ بالتخمين.\n"
             "- نفّذ جميع عناصر المخرج، ولا تكتفِ بشرح ما ينبغي فعله."]
    if extra_instructions.strip():
        parts.append("## تعليمات إضافية من المستخدم\n" + extra_instructions.strip())
    return "\n\n".join(parts)


def recommend_provider(task: str, available_provider_ids: list[str]) -> str | None:
    """يرتب الموجود فعلاً فقط، ولا يفترض التوافر أو المجانية أو جودة النموذج."""
    if task not in TASKS:
        raise ValueError("نوع المهمة غير معروف")
    available = set(available_provider_ids)
    return next((p for p in TASKS[task]["priority"] if p in available), None)


def estimate_input_tokens(text: str) -> int:
    """تقدير احتياطي تقريبي للنص العربي/المختلط، وليس عداد مزود رسمي."""
    return max(1, int(len(text or "") * 0.75))
